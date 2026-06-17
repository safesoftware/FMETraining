"""Skilljar release endpoints (release-status/plan/execute/link-draft-course/release-log).

Disjoint sibling of ``app/routes/skilljar.py`` (no shared router object). These
endpoints port the legacy launcher ``serve.py`` release handlers (lines 540-655)
into the FastAPI app, against the FROZEN contract in
``docs/plans/release-sprint-api-contract.md``.

Async handlers wrap the SYNCHRONOUS ``SkilljarReleaseService`` (WS-B) methods —
which do blocking network + disk I/O — via
``starlette.concurrency.run_in_threadpool`` so they don't block the event loop.
``get_release_log`` is a cheap dict lookup and is called directly.

Service singleton
-----------------
The in-process release-log registry on ``SkilljarReleaseService`` must survive
across the execute → poll request boundary, so we hold ONE service instance via
a lazy module-level getter (``_get_service``). It is built on first use from
``get_settings()`` — NOT at import time (the stub isn't import-safe to construct
eagerly, and tests need a swappable seam). Tests monkeypatch ``_get_service`` to
return a fake service.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.auth.dependencies import require_user
from app.config import get_settings
from app.db.session import get_session
from app.models.users import User
from app.services import release_locks
from app.services.skilljar_release_service import SkilljarReleaseService

_logger = logging.getLogger(__name__)

router = APIRouter(tags=["skilljar-release"])

# ``to_version`` shape guard, e.g. "2026.1" (contract §Conventions + serve.py).
_TO_VERSION_RE = re.compile(r"^\d{4}\.\d+$")


# ---------------------------------------------------------------------------
# Service singleton (lazy)
# ---------------------------------------------------------------------------

_service: Optional[SkilljarReleaseService] = None


def _get_service() -> SkilljarReleaseService:
    """Return the process-wide ``SkilljarReleaseService``, building it lazily.

    Held as a module-level singleton so the in-process release-log registry
    persists across the execute → poll calls. Constructed on first use from
    ``get_settings()`` (never at import time). Tests monkeypatch this function
    (or the cached instance's methods) to inject a fake service.
    """
    global _service
    if _service is None:
        _service = SkilljarReleaseService(get_settings())
    return _service


def reset_service_for_tests() -> None:
    """Clear the cached service instance + pending-finalize map. Tests only."""
    global _service
    _service = None
    _pending_finalize.clear()


# ---------------------------------------------------------------------------
# Release lock + history bookkeeping (WS-E, KNOW-2358)
# ---------------------------------------------------------------------------
#
# Live releases (NOT dry-runs) acquire a per-course lock + an audit row, then
# release the lock + close the audit row when the in-process release log goes
# terminal. The release runs in a daemon thread (can't touch the async DB), so
# finalization happens lazily in the async layer: the WS-D UI polls
# /api/release-log until done, and that terminal poll finalizes;
# /api/release-history reconciles too (in case the final poll was missed). The
# lock TTL is the crash backstop. The pending map is in-process, mirroring the
# release-log registry on the service.

_TERMINAL_LOG_STATUSES = {"done", "error"}


@dataclass
class _PendingFinalize:
    """What a finished release needs in order to finalize: which history rows
    to close and which locks to release."""

    history_ids: list[int]
    target_ids: list[str]
    user_id: Optional[int]


_pending_finalize: dict[str, _PendingFinalize] = {}


async def _finalize_action(
    session: AsyncSession, action_key: str, log_status: str
) -> None:
    """Close history + release locks for a finished release (idempotent)."""
    pending = _pending_finalize.get(action_key)
    if pending is None:
        return
    hist_status = "success" if log_status == "done" else "failed"
    await release_locks.finish_release_history(
        session, pending.history_ids, status=hist_status
    )
    await release_locks.release_held_locks(
        session, pending.target_ids, user_id=pending.user_id
    )
    _pending_finalize.pop(action_key, None)


async def _reconcile_pending(session: AsyncSession) -> None:
    """Finalize any pending release whose in-process log is already terminal.

    Backstop for when the client stopped polling /api/release-log before the
    terminal poll fired. If the in-process log is gone (e.g. after a restart)
    we drop the pending entry and let the lock TTL handle cleanup.
    """
    service = _get_service()
    for key in list(_pending_finalize.keys()):
        log = service.get_release_log(key)
        if log is None:
            _pending_finalize.pop(key, None)
        elif log.status in _TERMINAL_LOG_STATUSES:
            await _finalize_action(session, key, log.status)


def _history_row_to_dict(row: Any) -> dict[str, Any]:
    """Serialize a ``ReleaseHistory`` row for the API (parses ``target_id``)."""
    info = release_locks.parse_target_id(row.target_id)
    return {
        "id": row.id,
        "target_id": row.target_id,
        "to_version": info["to_version"],
        "course": info["course"],
        "status": row.status,
        "user_id": row.user_id,
        "started_at": row.started_at.isoformat() if row.started_at else None,
        "finished_at": row.finished_at.isoformat() if row.finished_at else None,
    }


# ---------------------------------------------------------------------------
# Guards
# ---------------------------------------------------------------------------


def _require_valid_version(to_version: str) -> None:
    """400 unless ``to_version`` matches ``\\d{4}\\.\\d+`` (contract)."""
    if not to_version or not _TO_VERSION_RE.match(to_version):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid to_version: {to_version!r} (expected e.g. '2026.1')",
        )


def _require_api_key() -> None:
    """503 when ``SKILLJAR_API_KEY`` is unset (mirrors skilljar.py 49-53)."""
    if not get_settings().skilljar_api_key:
        raise HTTPException(
            status_code=503,
            detail="SKILLJAR_API_KEY is not configured",
        )


# ---------------------------------------------------------------------------
# Request schemas
# ---------------------------------------------------------------------------


class ReleaseExecuteRequest(BaseModel):
    to_version: str = Field(min_length=1, max_length=32)
    lessons: list[str] = Field(default_factory=list)
    dry_run: bool = False


class LinkDraftCourseRequest(BaseModel):
    course_prefix: str = Field(min_length=1, max_length=512)
    skilljar_course_id: str = Field(min_length=1, max_length=128)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/api/release-status")
async def release_status(to_version: str = Query(...)) -> dict[str, list[str]]:
    """Saved + mapped + direct lesson dirs for ``to_version``.

    Returns ``{"saved": [...], "mapped": [...], "direct": [...]}``.
    """
    _require_valid_version(to_version)
    return await run_in_threadpool(_get_service().release_status, to_version)


@router.get("/api/release-plan")
async def release_plan(
    to_version: str = Query(...),
    lessons: list[str] = Query(default=[]),
) -> dict[str, Any]:
    """Pre-flight release plan for the selected lessons (the plan dict)."""
    _require_valid_version(to_version)
    return await run_in_threadpool(
        _get_service().build_release_plan, to_version, lessons
    )


@router.post("/api/release-execute")
async def release_execute(
    body: ReleaseExecuteRequest,
    user: User = Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> dict[str, str]:
    """Spawn a background release; return ``{"action_key": "..."}``.

    Live runs (``dry_run=False``) acquire a per-course release lock (409 if any
    course is already being released) and record a ``running`` history row
    before starting; these are committed before the release thread starts so a
    concurrent execute sees the lock. Dry-runs are a preview and skip all of
    this. The lock/history are finalized on the terminal /api/release-log poll.
    """
    _require_valid_version(body.to_version)
    _require_api_key()
    service = _get_service()

    if body.dry_run:
        action_key = await run_in_threadpool(
            lambda: service.execute_release(
                body.to_version, body.lessons, dry_run=True
            )
        )
        return {"action_key": action_key}

    target_ids = release_locks.course_target_ids_for(body.lessons)
    history_ids: list[int] = []
    if target_ids:
        conflicts = await release_locks.acquire_release_locks(
            session, target_ids, user_id=user.id
        )
        if conflicts:
            courses = [release_locks.parse_target_id(t)["course"] for t in conflicts]
            raise HTTPException(
                status_code=409,
                detail=(
                    "A release is already in progress for: "
                    + ", ".join(courses)
                    + ". Wait for it to finish, or try again later."
                ),
            )
        history_ids = await release_locks.start_release_history(
            session, target_ids, user_id=user.id
        )
        # Commit before the release thread starts so the lock is visible to a
        # concurrent execute and the audit row is durable.
        await session.commit()

    try:
        action_key = await run_in_threadpool(
            lambda: service.execute_release(
                body.to_version, body.lessons, dry_run=False
            )
        )
    except Exception:
        # Plan-building failed before the release thread started — undo the lock
        # and mark history failed so the course isn't wedged until TTL.
        if target_ids:
            await release_locks.finish_release_history(
                session, history_ids, status="failed"
            )
            await release_locks.release_held_locks(
                session, target_ids, user_id=user.id
            )
            await session.commit()
        raise

    if target_ids:
        _pending_finalize[action_key] = _PendingFinalize(
            history_ids=history_ids, target_ids=target_ids, user_id=user.id
        )
    return {"action_key": action_key}


@router.post("/api/link-draft-course")
async def link_draft_course(body: LinkDraftCourseRequest) -> dict[str, Any]:
    """Match a local draft course folder to a Skilljar course; return matches.

    The pipeline raises ``RuntimeError`` on failure → HTTP 400.
    """
    _require_api_key()
    try:
        return await run_in_threadpool(
            _get_service().link_draft_course,
            body.course_prefix,
            body.skilljar_course_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/release-log")
async def release_log(
    action_key: str = Query(...),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Poll the in-process buffer for a running/finished release.

    Returns ``{"action_key", "status", "log"}``; unknown key → 404. When the
    log has gone terminal, this poll also finalizes the release's lock + history
    (WS-E) — the WS-D UI polls until done, so this fires right as it finishes.
    """
    log = _get_service().get_release_log(action_key)
    if log is None:
        raise HTTPException(
            status_code=404, detail=f"No log for key: {action_key}"
        )
    if log.status in _TERMINAL_LOG_STATUSES and action_key in _pending_finalize:
        await _finalize_action(session, action_key, log.status)
    return {
        "action_key": log.action_key,
        "status": log.status,
        "log": log.log,
    }


@router.get("/api/release-history")
async def release_history(
    to_version: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
) -> dict[str, Any]:
    """Recent release audit rows (newest first), optionally one version.

    Returns ``{"history": [{id, target_id, to_version, course, status,
    user_id, started_at, finished_at}, ...]}``. Reconciles any pending
    finalizations first so a release that finished after the last poll still
    shows its final status.
    """
    if to_version:
        _require_valid_version(to_version)
    await _reconcile_pending(session)
    rows = await release_locks.list_release_history(
        session, to_version=to_version, limit=limit
    )
    return {"history": [_history_row_to_dict(r) for r in rows]}
