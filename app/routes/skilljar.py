"""Skilljar inventory sync endpoint.

Plan section 5:

    POST /api/skilljar-inventory/sync

Triggers a full sync of courses, lessons, and published-paths into our
DB. Throttled to one sync per minute team-wide so a chatty UI button
doesn't hammer Skilljar.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException

from app.config import get_settings
from app.db.engine import _get_or_create_session_factory
from app.services.skilljar_client import SkilljarClient
from app.services.skilljar_sync import sync_inventory

_logger = logging.getLogger(__name__)

router = APIRouter()

# Module-level throttle. Process-local is fine because v1 deploys with
# one API instance per environment (single EC2). If we ever scale out,
# move this to a row in the DB.
_THROTTLE_WINDOW = timedelta(minutes=1)
_last_sync_at: Optional[datetime] = None
_sync_lock = asyncio.Lock()


@router.post("/api/skilljar-inventory/sync")
async def sync_skilljar_inventory() -> dict:
    """Run a full Skilljar inventory sync. Returns counts.

    TODO(KNOW-2259): gate behind the same Google OIDC auth as the rest
    of the app once that ticket lands.
    """
    global _last_sync_at

    settings = get_settings()
    api_key = settings.skilljar_api_key or os.environ.get("SKILLJAR_API_KEY", "")
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="SKILLJAR_API_KEY is not configured",
        )

    now = datetime.now(timezone.utc)
    if _last_sync_at is not None and now - _last_sync_at < _THROTTLE_WINDOW:
        seconds_remaining = int(
            (_THROTTLE_WINDOW - (now - _last_sync_at)).total_seconds()
        )
        raise HTTPException(
            status_code=429,
            detail=f"Skilljar sync throttled — try again in {seconds_remaining}s",
            headers={"Retry-After": str(seconds_remaining)},
        )

    try:
        session_factory = _get_or_create_session_factory()
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    # Single-flight: if a sync is already running, the second caller
    # waits and then sees the throttle window, returning a 429.
    async with _sync_lock:
        async with SkilljarClient(api_key) as client:
            counts = await sync_inventory(
                session_factory=session_factory, client=client
            )
        _last_sync_at = datetime.now(timezone.utc)

    return {
        "synced_at": _last_sync_at.isoformat(),
        "courses": {"seen": counts.courses_seen, "upserted": counts.courses_upserted},
        "lessons": {"seen": counts.lessons_seen, "upserted": counts.lessons_upserted},
        "paths": {"seen": counts.paths_seen, "upserted": counts.paths_upserted},
    }


def reset_throttle_for_tests() -> None:
    """Clear the module-level throttle. For test fixtures only."""
    global _last_sync_at
    _last_sync_at = None
