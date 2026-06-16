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
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from app.config import get_settings
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
    """Clear the cached service instance. For test fixtures only."""
    global _service
    _service = None


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
async def release_execute(body: ReleaseExecuteRequest) -> dict[str, str]:
    """Spawn a background release; return ``{"action_key": "..."}``."""
    _require_valid_version(body.to_version)
    _require_api_key()
    action_key = await run_in_threadpool(
        lambda: _get_service().execute_release(
            body.to_version, body.lessons, dry_run=body.dry_run
        )
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
async def release_log(action_key: str = Query(...)) -> dict[str, Any]:
    """Poll the in-process buffer for a running/finished release.

    Returns ``{"action_key", "status", "log"}``; unknown key → 404.
    ``get_release_log`` is a cheap dict lookup, so it's called directly.
    """
    log = _get_service().get_release_log(action_key)
    if log is None:
        raise HTTPException(
            status_code=404, detail=f"No log for key: {action_key}"
        )
    return {
        "action_key": log.action_key,
        "status": log.status,
        "log": log.log,
    }
