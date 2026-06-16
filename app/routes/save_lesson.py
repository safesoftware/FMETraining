"""Save accepted lesson edits into the on-disk version tree.

    POST /api/save-lesson

Ports the legacy ``serve.py`` ``/api/save-lesson`` ("Save to Version")
endpoint into the FastAPI app. The write logic lives in
``app.services.lesson_writer``; this module is the thin HTTP shell that
resolves ``Settings`` (content root + S3 creds), maps the service's
exceptions onto status codes, and freezes the response contract WS-F's
report JS depends on.

Auth: gated by the global ``AuthMiddleware`` (see ``app/main.py``); no
per-route auth here. Response contract (frozen):
  * 200 → ``{"target_path": "<rel>/index.html"}``
  * 409 → ``{"target_path": "<rel>/index.html", "exists": true}``  (top-level
          ``target_path`` — the report's overwrite-confirm JS reads
          ``data.target_path``; do NOT wrap it in ``detail``)
  * 400 → ``HTTPException`` for bad/shallow ``lesson_dir`` or missing fields
  * 500/503 → ``HTTPException`` for image-upload / credential failures
"""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.config import get_settings
from app.services.lesson_writer import write_lesson

_logger = logging.getLogger(__name__)

router = APIRouter(tags=["save-lesson"])


class SaveLessonRequest(BaseModel):
    lesson_dir: str
    to_version: str
    html_content: str
    force: bool = False


@router.post("/api/save-lesson")
def save_lesson(body: SaveLessonRequest):
    """Write accepted lesson edits into ``Settings.lesson_content_root``.

    See module docstring for the frozen response contract.
    """
    lesson_dir = body.lesson_dir.strip()
    to_version = body.to_version.strip()
    if not lesson_dir or not to_version:
        raise HTTPException(
            status_code=400, detail="lesson_dir and to_version are required"
        )

    settings = get_settings()
    content_root = Path(settings.lesson_content_root)

    try:
        target_path = write_lesson(
            lesson_dir,
            to_version,
            body.html_content,
            force=body.force,
            content_root=content_root,
            s3_bucket=settings.aws_s3_bucket,
            s3_key_id=settings.aws_access_key_id,
            s3_secret=settings.aws_secret_access_key,
            # NOTE: app default region is us-west-2 (vs pipeline's us-east-1).
            # We thread the value from Settings; ops MUST set AWS_S3_REGION on
            # the box to whichever region the S3 bucket actually lives in.
            s3_region=settings.aws_s3_region,
        )
    except ValueError as exc:
        # Shallow / malformed lesson_dir.
        raise HTTPException(status_code=400, detail=str(exc))
    except FileExistsError as exc:
        # Target exists and force was not set. Return the relative target path
        # at the TOP LEVEL (not under `detail`) so the report's
        # overwrite-confirm JS can read `data.target_path` and re-POST with
        # force=true.
        return JSONResponse(
            status_code=409,
            content={"target_path": exc.filename, "exists": True},
        )
    except RuntimeError as exc:
        # Image upload / S3 credential failure. Distinguish a missing-creds
        # config error (503 — service misconfigured) from a transient upload
        # failure (500). upload_lesson_images raises a "...must be set in .env"
        # message when AWS_S3_BUCKET / AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
        # are absent.
        message = str(exc)
        _logger.warning("save-lesson image upload failed: %s", message)
        lowered = message.lower()
        is_config_error = "must be set" in lowered or "credential" in lowered
        status_code = 503 if is_config_error else 500
        raise HTTPException(status_code=status_code, detail=message)

    return {"target_path": target_path}
