"""Drafts page — per-run editor-state dashboard. KNOW-2277.

Lists recent runs that have at least one draft row in
``report_lesson_drafts``, with a status badge per lesson (pending /
in-progress / saved). Click "Open" to jump back into the report at the
right tab and lesson.
"""

from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.services import report_drafts as svc
from app.templates import templates

router = APIRouter(tags=["drafts"])


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
                        "/artifacts/report-"
                        + quote(r.run_id, safe="")
                        + ".html?tab=lesson-edits"
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
