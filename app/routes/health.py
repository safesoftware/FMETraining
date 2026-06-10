"""Health check endpoint.

Used by Nginx as a readiness probe (and by `bin/deploy-prod.sh` post-deploy)
and by humans during local dev. No auth — must work before any DB is
reachable.
"""
from __future__ import annotations

from fastapi import APIRouter

from app.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Liveness/readiness probe.

    Returns the build identifier so it's easy to tell which version is live
    when looking at multiple environments. The version comes from the
    `APP_VERSION` env var (CI sets this to the git SHA at image-build time).
    """
    settings = get_settings()
    return {"status": "ok", "version": settings.app_version}
