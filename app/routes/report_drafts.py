"""Editor-state API for the per-lesson recommendations / lesson-edits
report. KNOW-2276 (Phase 1a).

Endpoints (all return / accept JSON; the report's embedded JS calls
these from the same origin once :file:`app/main.py` mounts
``/artifacts``):

* ``GET  /api/runs/{run_id}/report-drafts``      — bulk fetch on report load.
* ``PUT  /api/runs/{run_id}/report-drafts``      — debounced auto-save.
* ``POST /api/runs/{run_id}/report-drafts/reset``      — Reset to original.
* ``POST /api/runs/{run_id}/report-drafts/mark-saved`` — called by the
  report after the legacy :file:`serve.py` ``/api/save-lesson`` succeeds.
* ``GET  /api/runs/with-drafts`` — backs the Phase 1b ``/drafts`` page.

``lesson_dir`` lives in the JSON body rather than the URL path because
real ``lesson_dir`` strings contain slashes (e.g.
``fme-form-basic/Connect To Data 2026.1/Some Lesson``); a
``{lesson_dir:path}`` URL converter would greedily swallow the
``/reset`` and ``/mark-saved`` action suffixes.

Auth: every ``/api/`` path is gated by :class:`app.auth.middleware.AuthMiddleware`
(fail-closed 401 for anonymous requests), so all endpoints here require a
signed-in ``@safe.com`` Google-OIDC user. The ``PUT`` additionally takes
``Depends(require_user)`` to attribute the write via ``updated_by``. Note the
shared one-row-per-``(run_id, lesson_dir)`` model is intentional (collaborative
draft); ``body_html`` is sanitized server-side in ``upsert_draft`` rather than
partitioned per user.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_user
from app.db.session import get_session
from app.models.users import User
from app.services import report_drafts as svc

router = APIRouter(tags=["report-drafts"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class _DraftBase(BaseModel):
    decisions: dict[str, str] = Field(default_factory=dict)
    body_html: Optional[str] = None
    saved_to_version_at: Optional[datetime] = None
    saved_to_version_path: Optional[str] = None
    updated_at: datetime


class DraftsForRunResponse(BaseModel):
    """Response shape for the bulk-fetch endpoint.

    The ``lessons`` map is keyed by ``lesson_dir`` for O(1) lookup in
    the report JS (one map traversal per lesson on first render).
    """

    lessons: dict[str, _DraftBase] = Field(default_factory=dict)


class UpsertDraftRequest(BaseModel):
    lesson_dir: str
    decisions: dict[str, str] = Field(default_factory=dict)
    body_html: Optional[str] = None
    # Optional optimistic-concurrency token. When present, the server
    # 409s if the row in the database has a different ``updated_at``.
    expected_updated_at: Optional[datetime] = None


class UpsertDraftResponse(BaseModel):
    updated_at: datetime


class StaleDraftResponse(BaseModel):
    """Returned with status 409 when ``expected_updated_at`` mismatches.

    Carries the current row so the client can reapply state without an
    extra GET round-trip.
    """

    detail: str = "stale draft"
    current: _DraftBase


class ResetDraftRequest(BaseModel):
    lesson_dir: str


class ResetDraftResponse(BaseModel):
    ok: bool
    deleted: bool


class MarkSavedRequest(BaseModel):
    lesson_dir: str
    saved_to_version_path: str


class MarkSavedResponse(BaseModel):
    saved_to_version_at: datetime
    saved_to_version_path: str


class _LessonSummary(BaseModel):
    lesson_dir: str
    status: str
    updated_at: datetime
    saved_to_version_at: Optional[datetime] = None
    saved_to_version_path: Optional[str] = None


class _RunSummary(BaseModel):
    run_id: str
    to_version: Optional[str] = None
    started_at: Optional[datetime] = None
    created_at: datetime
    lessons: list[_LessonSummary]


class RunsWithDraftsResponse(BaseModel):
    runs: list[_RunSummary]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_payload(row: Any) -> _DraftBase:
    return _DraftBase(
        decisions=dict(row.decisions_json or {}),
        body_html=row.body_html,
        saved_to_version_at=row.saved_to_version_at,
        saved_to_version_path=row.saved_to_version_path,
        updated_at=row.updated_at,
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@router.get(
    "/api/runs/{run_id}/report-drafts",
    response_model=DraftsForRunResponse,
)
async def get_run_drafts(
    run_id: str,
    session: AsyncSession = Depends(get_session),
) -> DraftsForRunResponse:
    rows = await svc.get_drafts_for_run(session, run_id)
    return DraftsForRunResponse(
        lessons={row.lesson_dir: _to_payload(row) for row in rows}
    )


@router.put(
    "/api/runs/{run_id}/report-drafts",
    response_model=UpsertDraftResponse,
)
async def upsert_run_draft(
    run_id: str,
    body: UpsertDraftRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_user),
) -> UpsertDraftResponse:
    try:
        row = await svc.upsert_draft(
            session,
            run_id=run_id,
            lesson_dir=body.lesson_dir,
            decisions=body.decisions,
            body_html=body.body_html,
            expected_updated_at=body.expected_updated_at,
            updated_by=user.id,
        )
    except svc.StaleDraftError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=StaleDraftResponse(current=_to_payload(exc.current)).model_dump(
                mode="json"
            ),
        )
    return UpsertDraftResponse(updated_at=row.updated_at)


@router.post(
    "/api/runs/{run_id}/report-drafts/reset",
    response_model=ResetDraftResponse,
)
async def reset_run_draft(
    run_id: str,
    body: ResetDraftRequest,
    session: AsyncSession = Depends(get_session),
) -> ResetDraftResponse:
    deleted = await svc.reset_draft(session, run_id, body.lesson_dir)
    return ResetDraftResponse(ok=True, deleted=deleted)


@router.post(
    "/api/runs/{run_id}/report-drafts/mark-saved",
    response_model=MarkSavedResponse,
)
async def mark_run_draft_saved(
    run_id: str,
    body: MarkSavedRequest,
    session: AsyncSession = Depends(get_session),
) -> MarkSavedResponse:
    row = await svc.mark_saved(
        session,
        run_id=run_id,
        lesson_dir=body.lesson_dir,
        saved_to_version_path=body.saved_to_version_path,
    )
    if row.saved_to_version_at is None or row.saved_to_version_path is None:
        # mark_saved is contracted to set both; if it didn't, fail loudly
        # rather than return nulls (an assert would be stripped under -O).
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="mark_saved did not persist save metadata",
        )
    return MarkSavedResponse(
        saved_to_version_at=row.saved_to_version_at,
        saved_to_version_path=row.saved_to_version_path,
    )


@router.get(
    "/api/runs/with-drafts",
    response_model=RunsWithDraftsResponse,
)
async def list_runs_with_drafts(
    session: AsyncSession = Depends(get_session),
) -> RunsWithDraftsResponse:
    runs = await svc.list_runs_with_drafts(session, limit=50)
    return RunsWithDraftsResponse(
        runs=[
            _RunSummary(
                run_id=r.run_id,
                to_version=r.to_version,
                started_at=r.started_at,
                created_at=r.created_at,
                lessons=[
                    _LessonSummary(
                        lesson_dir=lesson.lesson_dir,
                        status=lesson.status,
                        updated_at=lesson.updated_at,
                        saved_to_version_at=lesson.saved_to_version_at,
                        saved_to_version_path=lesson.saved_to_version_path,
                    )
                    for lesson in r.lessons
                ],
            )
            for r in runs
        ]
    )
