"""Service helpers for ``report_lesson_drafts``.

Routes call these; the service owns the SQL. KNOW-2276.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.report_drafts import ReportLessonDraft
from app.models.runs import Run
from app.services.html_sanitizer import sanitize_report_html


class StaleDraftError(Exception):
    """Raised by :func:`upsert_draft` when ``expected_updated_at`` does
    not match the row already in the database — i.e. someone else
    updated the same lesson in another tab. Carries the current row so
    the caller can return it in the 409 response.
    """

    def __init__(self, current: ReportLessonDraft) -> None:
        super().__init__(
            f"Stale draft for run_id={current.run_id} "
            f"lesson_dir={current.lesson_dir}"
        )
        self.current = current


async def get_drafts_for_run(
    session: AsyncSession, run_id: str
) -> list[ReportLessonDraft]:
    """Return every draft row for *run_id* (one per lesson_dir)."""
    result = await session.execute(
        select(ReportLessonDraft).where(ReportLessonDraft.run_id == run_id)
    )
    return list(result.scalars().all())


async def get_draft(
    session: AsyncSession, run_id: str, lesson_dir: str
) -> Optional[ReportLessonDraft]:
    result = await session.execute(
        select(ReportLessonDraft).where(
            ReportLessonDraft.run_id == run_id,
            ReportLessonDraft.lesson_dir == lesson_dir,
        )
    )
    return result.scalar_one_or_none()


async def upsert_draft(
    session: AsyncSession,
    *,
    run_id: str,
    lesson_dir: str,
    decisions: dict[str, Any],
    body_html: Optional[str],
    expected_updated_at: Optional[datetime] = None,
    updated_by: Optional[int] = None,
) -> ReportLessonDraft:
    """Insert or update the draft row for ``(run_id, lesson_dir)``.

    If *expected_updated_at* is provided and the existing row's
    ``updated_at`` differs, raises :class:`StaleDraftError` so the
    caller can return 409 + the current row.

    ``body_html`` is sanitized here (the single write choke point) before
    it is persisted: the report re-renders it via ``innerHTML`` and the
    draft is shared across all ``@safe.com`` users of the run, so an
    unsanitized payload would be stored cross-user XSS.
    """
    body_html = sanitize_report_html(body_html)
    existing = await get_draft(session, run_id, lesson_dir)
    if existing is None:
        row = ReportLessonDraft(
            run_id=run_id,
            lesson_dir=lesson_dir,
            decisions_json=dict(decisions),
            body_html=body_html,
            updated_by=updated_by,
        )
        session.add(row)
        await session.flush()
        return row

    if (
        expected_updated_at is not None
        and existing.updated_at != expected_updated_at
    ):
        raise StaleDraftError(existing)

    existing.decisions_json = dict(decisions)
    existing.body_html = body_html
    existing.updated_by = updated_by
    # ``onupdate=utc_now`` covers the timestamp; we still bump it
    # explicitly so the returned row reflects the new value before
    # the implicit flush at commit time.
    existing.updated_at = utc_now()
    await session.flush()
    return existing


async def reset_draft(
    session: AsyncSession, run_id: str, lesson_dir: str
) -> bool:
    """Delete the draft row. Returns ``True`` if a row was removed."""
    result = await session.execute(
        delete(ReportLessonDraft).where(
            ReportLessonDraft.run_id == run_id,
            ReportLessonDraft.lesson_dir == lesson_dir,
        )
    )
    await session.flush()
    return (result.rowcount or 0) > 0


async def mark_saved(
    session: AsyncSession,
    *,
    run_id: str,
    lesson_dir: str,
    saved_to_version_path: str,
    updated_by: Optional[int] = None,
) -> ReportLessonDraft:
    """Stamp ``saved_to_version_at = now`` and the version-folder path.

    Creates the draft row if it doesn't exist yet (e.g. user never
    touched accept/reject and went straight to Save to Version Folder).
    """
    existing = await get_draft(session, run_id, lesson_dir)
    now = utc_now()
    if existing is None:
        row = ReportLessonDraft(
            run_id=run_id,
            lesson_dir=lesson_dir,
            decisions_json={},
            body_html=None,
            saved_to_version_at=now,
            saved_to_version_path=saved_to_version_path,
            updated_by=updated_by,
        )
        session.add(row)
        await session.flush()
        return row

    existing.saved_to_version_at = now
    existing.saved_to_version_path = saved_to_version_path
    if updated_by is not None:
        existing.updated_by = updated_by
    existing.updated_at = now
    await session.flush()
    return existing


@dataclass
class RunWithDrafts:
    run_id: str
    to_version: Optional[str]
    started_at: Optional[datetime]
    created_at: datetime
    lessons: list["LessonDraftSummary"]


@dataclass
class LessonDraftSummary:
    lesson_dir: str
    status: str  # "pending" | "in_progress" | "saved"
    updated_at: datetime
    saved_to_version_at: Optional[datetime]
    saved_to_version_path: Optional[str]


def _draft_status(draft: ReportLessonDraft) -> str:
    """Compute the lesson status badge from a draft row.

    * ``saved`` if the row records a version-folder push.
    * ``in_progress`` if any decision is non-pending or any WYSIWYG
      content has been typed.
    * ``pending`` otherwise (a row that exists but is essentially empty
      — rare; arises if the user reset everything without deleting).
    """
    if draft.saved_to_version_at is not None:
        return "saved"
    decisions = draft.decisions_json or {}
    has_decision = any(v != "pending" for v in decisions.values())
    has_body = bool(draft.body_html)
    if has_decision or has_body:
        return "in_progress"
    return "pending"


async def list_runs_with_drafts(
    session: AsyncSession, *, limit: int = 50
) -> list[RunWithDrafts]:
    """Return recent runs that have at least one draft row, with
    per-lesson status summaries. Backs the Phase 1b ``/drafts`` page.
    """
    drafts_q = await session.execute(
        select(ReportLessonDraft, Run)
        .join(Run, Run.id == ReportLessonDraft.run_id)
        .order_by(Run.created_at.desc(), ReportLessonDraft.lesson_dir.asc())
    )
    rows = list(drafts_q.all())

    by_run: dict[str, RunWithDrafts] = {}
    for draft, run in rows:
        bucket = by_run.get(run.id)
        if bucket is None:
            bucket = RunWithDrafts(
                run_id=run.id,
                to_version=run.to_version,
                started_at=run.started_at,
                created_at=run.created_at,
                lessons=[],
            )
            by_run[run.id] = bucket
            if len(by_run) > limit:
                # Trimmed implicitly by ``break`` once we exhaust the
                # limit. We keep filling the buckets we already have
                # though, so subsequent draft rows for an already-seen
                # run still attach.
                pass
        bucket.lessons.append(
            LessonDraftSummary(
                lesson_dir=draft.lesson_dir,
                status=_draft_status(draft),
                updated_at=draft.updated_at,
                saved_to_version_at=draft.saved_to_version_at,
                saved_to_version_path=draft.saved_to_version_path,
            )
        )

    # ``by_run`` was built in run-creation-desc order via the SQL ORDER
    # BY, so dict insertion order is the order we want. Apply the
    # limit at the run granularity here.
    return list(by_run.values())[:limit]
