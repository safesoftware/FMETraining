"""Drafts: Save Draft API + per-run editor-state dashboard.

Two responsibilities live here:

* **POST/GET/DELETE ``/api/drafts``** (KNOW-2273) — the Save Draft API
  that writes lesson HTML to the draft store and upserts ``lesson_drafts``.
  Replaces the legacy ``_handle_save_lesson`` in ``serve.py`` writing to
  ``REPO_ROOT/2026.1/...``.

* **GET ``/drafts``** (KNOW-2277) — per-run editor-state dashboard. Lists
  recent runs that have at least one draft row in
  ``report_lesson_drafts``, with a status badge per lesson (pending /
  in-progress / saved). Click "Open" to jump back into the report at the
  right tab and lesson.

Endpoints in this module:

- ``POST   /api/drafts``        — create or update a draft.
- ``GET    /api/drafts``        — list drafts (optional filters).
- ``GET    /api/drafts/{id}``   — fetch one (metadata + html_content).
- ``DELETE /api/drafts/{id}``   — archive a draft (status='archived').
- ``GET    /drafts``            — per-run dashboard page.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.db.engine import _get_or_create_session_factory
from app.db.session import get_session
from app.models.skilljar import LessonDraft
from app.services import report_drafts as svc
from app.services.draft_storage import (
    DraftStorageError,
    DraftStorageUnavailable,
    LocalDiskDraftStorage,
)
from app.templates import templates


# TODO(KNOW-XXXX, image-serving follow-up): drafts saved via this API
# can contain `<img src="images/foo.png">` references. Today there is no
# matching `/api/drafts/{id}/images/{name}` endpoint to serve them, so a
# browser preview of a saved draft renders broken images. Decide between
# (a) S3 image bucket via the existing pipeline/lesson_image_upload
# flow, or (b) local /var/lib/fme-train/drafts/<...>/images served by
# Nginx. Image upload + rewrite belong here when that decision is made.

_logger = logging.getLogger(__name__)

router = APIRouter(tags=["drafts"])


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class SaveDraftRequest(BaseModel):
    to_version: str = Field(min_length=1, max_length=32)
    path: str = Field(
        min_length=1,
        max_length=512,
        description="Skilljar-taxonomy triple <lp>/<course>/<lesson>",
    )
    html_content: str
    source_skilljar_lesson_id: Optional[str] = None


class DraftSummary(BaseModel):
    """Metadata-only view used by the list endpoint."""

    id: int
    to_version: str
    path: str
    s3_key: str
    source_skilljar_lesson_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    run_id: Optional[str] = None


class DraftDetail(DraftSummary):
    """Detail view: same as summary plus the HTML body."""

    html_content: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _get_storage() -> LocalDiskDraftStorage:
    """Build the configured draft storage. v1 is always local disk."""
    settings = get_settings()
    root = Path(settings.drafts_root)
    return LocalDiskDraftStorage(root)


def _summary_from_row(row: LessonDraft) -> DraftSummary:
    return DraftSummary(
        id=row.id,
        to_version=row.to_version,
        path=row.path,
        s3_key=row.s3_key,
        source_skilljar_lesson_id=row.source_skilljar_lesson_id,
        status=row.status,
        created_at=row.created_at,
        updated_at=row.updated_at,
        run_id=row.run_id,
    )


# ---------------------------------------------------------------------------
# Save Draft API (KNOW-2273)
# ---------------------------------------------------------------------------


@router.post("/api/drafts", status_code=201)
async def save_draft(req: SaveDraftRequest) -> DraftSummary:
    """Create or update a lesson draft.

    Idempotent on ``(to_version, path)`` — re-saving the same lesson
    overwrites the file and increments ``updated_at`` rather than
    creating a duplicate row. The DB enforces uniqueness via the
    ``uq_lesson_drafts_to_version_path`` constraint so two racing POSTs
    can't double-insert: the second one's INSERT raises
    ``IntegrityError``, which we catch and retry as an UPDATE.

    Promoted drafts (already pushed to Skilljar) cannot be overwritten
    via this endpoint — would silently desync the live lesson from our
    record. Returns 409 instead. The editor flow for a re-edit of a
    promoted lesson is to first un-promote (a separate Release-tab
    action) and then re-save through this path.

    TODO(KNOW-2259): once auth lands, populate ``created_by`` / ``updated_by``
    from the session cookie. For now both stay NULL.
    """
    storage = _get_storage()
    try:
        location = await storage.write(
            to_version=req.to_version,
            path=req.path,
            html=req.html_content,
        )
    except DraftStorageUnavailable as exc:
        # Server-side: misconfigured drafts_root, disk full, etc.
        raise HTTPException(status_code=503, detail=str(exc))
    except DraftStorageError as exc:
        # Caller's input is invalid (bad path, traversal attempt, etc.).
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        session_factory = _get_or_create_session_factory()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    now = datetime.now(timezone.utc)

    # Attempt INSERT first. If a concurrent request beat us to it, the
    # UNIQUE constraint trips IntegrityError and we fall through to an
    # UPDATE instead. This is safer than SELECT-then-INSERT, which has
    # a TOCTOU window large enough for two browser tabs to collide.
    async with session_factory() as session:
        row = LessonDraft(
            to_version=req.to_version,
            path=req.path,
            s3_key=location.key,
            source_skilljar_lesson_id=req.source_skilljar_lesson_id,
            status="draft",
            created_at=now,
            updated_at=now,
        )
        session.add(row)
        try:
            await session.commit()
            await session.refresh(row)
            return _summary_from_row(row)
        except IntegrityError:
            await session.rollback()

    # Fall through to update path: the row already exists.
    async with session_factory() as session:
        existing = await session.scalar(
            select(LessonDraft).where(
                LessonDraft.to_version == req.to_version,
                LessonDraft.path == req.path,
            )
        )
        if existing is None:
            # Extremely narrow race: row existed when we INSERT'd, then
            # was deleted between the rollback and this SELECT. Surface
            # as 503 so the caller retries.
            raise HTTPException(
                status_code=503,
                detail="Draft row vanished mid-save; please retry.",
            )
        if existing.status == "promoted":
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Draft {existing.id} for {req.path!r} is promoted; "
                    "un-promote it from the Release tab before re-saving."
                ),
            )
        existing.s3_key = location.key
        existing.source_skilljar_lesson_id = req.source_skilljar_lesson_id
        existing.updated_at = now
        # If a previously-archived draft is re-saved, treat that as
        # un-archiving it.
        if existing.status == "archived":
            existing.status = "draft"
        await session.commit()
        await session.refresh(existing)
        return _summary_from_row(existing)


@router.get("/api/drafts")
async def list_drafts(
    to_version: Optional[str] = None,
    status: Optional[str] = None,
) -> list[DraftSummary]:
    """List drafts. Optional ``to_version`` and ``status`` filters."""
    try:
        session_factory = _get_or_create_session_factory()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    stmt = select(LessonDraft).order_by(LessonDraft.updated_at.desc())
    if to_version is not None:
        stmt = stmt.where(LessonDraft.to_version == to_version)
    if status is not None:
        stmt = stmt.where(LessonDraft.status == status)

    async with session_factory() as session:
        rows = (await session.scalars(stmt)).all()
    return [_summary_from_row(r) for r in rows]


@router.get("/api/drafts/{draft_id}")
async def get_draft(draft_id: int) -> DraftDetail:
    """Fetch a single draft, including the stored HTML body."""
    try:
        session_factory = _get_or_create_session_factory()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    async with session_factory() as session:
        row = await session.get(LessonDraft, draft_id)
    if row is None:
        raise HTTPException(status_code=404, detail=f"draft {draft_id} not found")

    storage = _get_storage()
    try:
        html = await storage.read(row.s3_key)
    except LookupError as exc:
        # Row exists but the file is gone — surface as 404 since the
        # draft is effectively missing from the user's perspective.
        raise HTTPException(
            status_code=404,
            detail=f"draft {draft_id} content missing: {exc}",
        )
    summary = _summary_from_row(row)
    return DraftDetail(html_content=html, **summary.model_dump())


@router.delete("/api/drafts/{draft_id}", status_code=204)
async def archive_draft(draft_id: int) -> None:
    """Mark a draft archived. The file stays on disk for audit; readers
    skip archived drafts via the ``status`` filter."""
    try:
        session_factory = _get_or_create_session_factory()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    async with session_factory() as session:
        row = await session.get(LessonDraft, draft_id)
        if row is None:
            raise HTTPException(status_code=404, detail=f"draft {draft_id} not found")
        if row.status == "promoted":
            # A promoted draft is one that's been pushed to Skilljar.
            # Archiving it would leave the Release tab confused, so refuse.
            raise HTTPException(
                status_code=409,
                detail=f"draft {draft_id} is promoted; cannot archive",
            )
        row.status = "archived"
        row.updated_at = datetime.now(timezone.utc)
        await session.commit()


# ---------------------------------------------------------------------------
# Drafts dashboard page (KNOW-2277)
# ---------------------------------------------------------------------------


@router.get("/drafts", response_class=HTMLResponse)
async def drafts_page(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    runs = await svc.list_runs_with_drafts(session, limit=50)
    rows = [
        {
            "run_id": r.run_id,
            "to_version": r.to_version or "",
            "started_at": r.started_at,
            "created_at": r.created_at,
            "lessons": [
                {
                    "lesson_dir": lesson.lesson_dir,
                    "status": lesson.status,
                    "open_url": (
                        "/report/"
                        + quote(r.run_id, safe="")
                        + "?tab=lesson-edits"
                    ),
                    "saved_to_version_path": lesson.saved_to_version_path,
                    "updated_at": lesson.updated_at,
                }
                for lesson in r.lessons
            ],
        }
        for r in runs
    ]
    return templates.TemplateResponse(
        request, "drafts.html", {"runs": rows}
    )
