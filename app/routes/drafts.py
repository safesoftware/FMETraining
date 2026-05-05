"""Save Draft API.

Plan section 5: ``POST /api/drafts`` writes the HTML to the draft store
(local disk in the EC2 deployment) and upserts ``lesson_drafts``. Replaces
the legacy ``_handle_save_lesson`` in ``serve.py`` writing to
``REPO_ROOT/2026.1/...``.

Endpoints:

- ``POST   /api/drafts``        — create or update a draft.
- ``GET    /api/drafts``        — list drafts (optional ``to_version`` filter).
- ``GET    /api/drafts/{id}``   — fetch one (metadata + html_content).
- ``DELETE /api/drafts/{id}``   — archive a draft (status='archived').
                                  We don't physically delete the file —
                                  keeps the audit trail.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.config import get_settings
from app.db.engine import _get_or_create_session_factory
from app.models.skilljar import LessonDraft
from app.services.draft_storage import (
    DraftStorageError,
    LocalDiskDraftStorage,
)

_logger = logging.getLogger(__name__)

router = APIRouter()


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
# Endpoints
# ---------------------------------------------------------------------------


@router.post("/api/drafts", status_code=201)
async def save_draft(req: SaveDraftRequest) -> DraftSummary:
    """Create or update a lesson draft.

    Idempotent on ``(to_version, path)`` — re-saving the same lesson
    overwrites the file and increments ``updated_at`` rather than
    creating a duplicate row.

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
    except DraftStorageError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        session_factory = _get_or_create_session_factory()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        existing = await session.scalar(
            select(LessonDraft).where(
                LessonDraft.to_version == req.to_version,
                LessonDraft.path == req.path,
            )
        )
        if existing is None:
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
            await session.commit()
            await session.refresh(row)
        else:
            existing.s3_key = location.key
            existing.source_skilljar_lesson_id = req.source_skilljar_lesson_id
            existing.updated_at = now
            # If a previously-archived draft is re-saved, treat that as
            # un-archiving it. Promoted drafts stay promoted (the editor
            # shouldn't overwrite a published lesson via this path).
            if existing.status == "archived":
                existing.status = "draft"
            await session.commit()
            await session.refresh(existing)
            row = existing

    return _summary_from_row(row)


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
