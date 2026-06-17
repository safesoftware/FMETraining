"""Release locks + history wiring (WS-E, KNOW-2358).

Wires the existing ``release_locks`` / ``release_history`` tables
(``app/models/skilljar.py``, present since ``0001_baseline``) into the live,
filesystem-based release flow. The live flow operates on **lesson-dir strings**
under a ``to_version`` (no DB lesson model — that's the deferred v2 work), so we
key both tables on a **per-course** ``target_id``:

    target_id = "course:<to_version>/<lp>/<course folder>"

i.e. ``"course:" + <the lesson_dir minus its last path segment>``. The
``to_version`` is therefore encoded in the ``target_id`` itself (first path
segment after the ``course:`` prefix), so we never need a separate version
column. The v2-only FK columns (``skilljar_lesson_id`` / ``draft_id`` /
``before_hash`` / ``after_hash``) stay NULL.

Locks are **advisory**: ``POST /api/release-execute`` (live runs only — dry-runs
skip locking + history) acquires a lock per course before starting the release
and a 409 is returned if any course is already locked by a live (unexpired)
lock. The lock carries a TTL (:data:`LOCK_TTL`) so a crashed/abandoned release
can't wedge a course forever; the normal path releases the lock when the
release finishes (see the finalize-on-poll path in
``app/routes/skilljar_release.py``).

History is an append-only audit row per course per release execution
(``started_at`` → ``finished_at`` + ``status``), surfaced via
``GET /api/release-history``.

All functions are async and operate on a caller-supplied ``AsyncSession`` (they
``flush`` but never ``commit`` — the caller owns the transaction boundary),
matching the rest of the app's async DB code.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ReleaseHistory, ReleaseLock
from app.models.base import utc_now

# How long a release lock stays valid without being explicitly released. The
# normal flow releases on completion; this is the crash/abandon backstop.
LOCK_TTL = timedelta(minutes=30)

_COURSE_PREFIX = "course:"


# ---------------------------------------------------------------------------
# target_id helpers
# ---------------------------------------------------------------------------


def course_target_id(lesson_dir: str) -> str:
    """``target_id`` for the course that ``lesson_dir`` belongs to.

    ``"2026.1/lp/Course 2026.1/Lesson"`` → ``"course:2026.1/lp/Course 2026.1"``.
    A path with no ``/`` (already a course-ish prefix) is used as-is.
    """
    trimmed = lesson_dir.strip().rstrip("/")
    course_prefix = trimmed.rsplit("/", 1)[0] if "/" in trimmed else trimmed
    return f"{_COURSE_PREFIX}{course_prefix}"


def course_target_ids_for(lessons: list[str]) -> list[str]:
    """Distinct, sorted per-course ``target_id``s for ``lessons`` (skips blanks)."""
    return sorted({course_target_id(d) for d in lessons if d and d.strip()})


def parse_target_id(target_id: str) -> dict[str, str]:
    """Split a ``course:`` ``target_id`` into display fields.

    Returns ``{"to_version", "course_prefix", "course"}``. ``to_version`` is the
    first path segment; ``course`` is the last (the course-folder name).
    """
    course_prefix = (
        target_id[len(_COURSE_PREFIX):]
        if target_id.startswith(_COURSE_PREFIX)
        else target_id
    )
    parts = course_prefix.split("/")
    return {
        "to_version": parts[0] if parts and parts[0] else "",
        "course_prefix": course_prefix,
        "course": parts[-1] if parts else course_prefix,
    }


def _aware(dt: datetime) -> datetime:
    """Treat a naive datetime (SQLite round-trips can drop tzinfo) as UTC."""
    return dt if dt.tzinfo is not None else dt.replace(tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Locks
# ---------------------------------------------------------------------------


async def acquire_release_locks(
    session: AsyncSession,
    target_ids: list[str],
    *,
    user_id: int | None,
    intent: str = "release",
) -> list[str]:
    """Atomically claim a lock for every ``target_id`` (all-or-nothing).

    Returns the list of ``target_id``s that are already held by a **live**
    (unexpired) lock — empty list means every lock was acquired. On conflict
    nothing is written, so the caller can 409 without rolling back partial
    state. Expired locks are taken over.
    """
    if not target_ids:
        return []

    now = utc_now()

    # Pass 1 — detect live conflicts; write nothing yet.
    existing: dict[str, ReleaseLock | None] = {}
    conflicts: list[str] = []
    for tid in target_ids:
        lock = await session.get(ReleaseLock, tid)
        existing[tid] = lock
        if lock is not None and _aware(lock.expires_at) > now:
            conflicts.append(tid)
    if conflicts:
        return sorted(conflicts)

    # Pass 2 — claim all (insert new, or take over an expired row).
    expires_at = now + LOCK_TTL
    for tid in target_ids:
        lock = existing[tid]
        if lock is None:
            session.add(
                ReleaseLock(
                    target_id=tid,
                    locked_by=user_id,
                    locked_at=now,
                    expires_at=expires_at,
                    intent=intent,
                )
            )
        else:
            lock.locked_by = user_id
            lock.locked_at = now
            lock.expires_at = expires_at
            lock.intent = intent
    await session.flush()
    return []


async def release_held_locks(
    session: AsyncSession,
    target_ids: list[str],
    *,
    user_id: int | None = None,
) -> None:
    """Delete locks for ``target_ids``.

    When ``user_id`` is given, only locks owned by that user (or with no owner)
    are deleted — so we never drop a lock another user took over after ours
    expired mid-release.
    """
    if not target_ids:
        return
    stmt = delete(ReleaseLock).where(ReleaseLock.target_id.in_(target_ids))
    if user_id is not None:
        stmt = stmt.where(
            or_(ReleaseLock.locked_by == user_id, ReleaseLock.locked_by.is_(None))
        )
    await session.execute(stmt)
    await session.flush()


# ---------------------------------------------------------------------------
# History
# ---------------------------------------------------------------------------


async def start_release_history(
    session: AsyncSession,
    target_ids: list[str],
    *,
    user_id: int | None,
) -> list[int]:
    """Create one ``running`` history row per course; return their ids."""
    if not target_ids:
        return []
    rows = [
        ReleaseHistory(
            target_id=tid,
            user_id=user_id,
            started_at=utc_now(),
            status="running",
        )
        for tid in target_ids
    ]
    session.add_all(rows)
    await session.flush()
    return [r.id for r in rows]


async def finish_release_history(
    session: AsyncSession,
    history_ids: list[int],
    *,
    status: str,
) -> None:
    """Close ``running`` history rows to ``status`` with a ``finished_at``.

    Idempotent: only rows still ``running`` are updated, so a double-finalize
    (e.g. two terminal polls racing) is a no-op the second time.
    """
    if not history_ids:
        return
    await session.execute(
        update(ReleaseHistory)
        .where(
            ReleaseHistory.id.in_(history_ids),
            ReleaseHistory.status == "running",
        )
        .values(status=status, finished_at=utc_now())
    )
    await session.flush()


async def list_release_history(
    session: AsyncSession,
    *,
    to_version: str | None = None,
    limit: int = 50,
) -> list[ReleaseHistory]:
    """Recent history rows, newest first, optionally filtered to one version."""
    stmt = select(ReleaseHistory).order_by(ReleaseHistory.started_at.desc()).limit(limit)
    if to_version:
        stmt = stmt.where(
            ReleaseHistory.target_id.like(f"{_COURSE_PREFIX}{to_version}/%")
        )
    result = await session.execute(stmt)
    return list(result.scalars().all())
