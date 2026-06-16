"""Serve lesson content images for the report + WYSIWYG preview (KNOW-2347).

``GET /lesson-content/{rel_path}`` returns a file from the lesson content tree.
The report references images by a stable, same-origin URL
``/lesson-content/{lesson_dir}/images/{file}`` instead of a relative
``../{lesson_dir}/...`` path that only resolved under the old "serve from
project root" model and 404'd after the EC2 cutover (the report now lives at
``/artifacts/{run_id}/report-{run_id}.html`` and the ``/artifacts`` mount never
served the content tree).

Public — *not* under ``/api/`` — so it isn't gated by ``AuthMiddleware`` and
images load in a browser without an auth round-trip, exactly like ``/artifacts``.
The office-IP firewall is the network perimeter (same posture as the report
HTML and ``/artifacts``).

**Swap point (KNOW-2360).** Bytes are sourced through a
:class:`pipeline.content_source.ContentSource` (selected by Settings:
``content_source`` = ``local`` | ``s3mirror``), not by ``FileResponse`` over a
local path — under ``s3mirror`` there is no local file. The route returns a
plain ``Response`` with the resolved bytes + content type; the URL format is
unchanged across both backends.
"""
from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.config import get_settings
from app.services.content_files import read_content_bytes
from pipeline.content_source import build_content_source

router = APIRouter(tags=["lesson-content"])


@router.get("/lesson-content/{rel_path:path}")
async def get_lesson_content(rel_path: str) -> Response:
    """Return a lesson image / index.html from the configured content source."""
    settings = get_settings()
    source = build_content_source(
        source=settings.content_source,
        content_root=Path(settings.lesson_content_root).resolve(),
        base_url=settings.content_s3_base_url,
    )
    try:
        data, media_type = read_content_bytes(rel_path, source=source)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail="Not found") from exc
    return Response(content=data, media_type=media_type)
