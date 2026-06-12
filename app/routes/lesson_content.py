"""Serve lesson content images for the report + WYSIWYG preview (KNOW-2347).

``GET /lesson-content/{rel_path}`` streams a file from the lesson content tree
(``Settings.lesson_content_root``). The report references images by a stable,
same-origin URL ``/lesson-content/{lesson_dir}/images/{file}`` instead of a
relative ``../{lesson_dir}/...`` path that only resolved under the old
"serve from project root" model and 404'd after the EC2 cutover (the report now
lives at ``/artifacts/{run_id}/report-{run_id}.html`` and the ``/artifacts``
mount never served the content tree).

Public — *not* under ``/api/`` — so it isn't gated by ``AuthMiddleware`` and
images load in a browser without an auth round-trip, exactly like ``/artifacts``.
The office-IP firewall is the network perimeter (same posture as the report
HTML and ``/artifacts``).
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings
from app.services.content_files import resolve_content_path

router = APIRouter(tags=["lesson-content"])


@router.get("/lesson-content/{rel_path:path}")
async def get_lesson_content(rel_path: str) -> FileResponse:
    """Stream a file from the content tree by its repo-relative path."""
    content_root = Path(get_settings().lesson_content_root).resolve()
    try:
        file_path = resolve_content_path(rel_path, content_root=content_root)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Not found") from exc
    return FileResponse(file_path)
