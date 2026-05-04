"""FastAPI application factory and ASGI entrypoint.

Phase 0 (KNOW-2258) wires:
    - settings via pydantic-settings
    - static + Jinja2 templates
    - placeholder index + health routes
    - a lifespan hook with a startup log line that DB wiring will hook into later

Auth, DB sessions, run endpoints, and the run scheduler all land in
sibling tickets and will be `app.include_router(...)`'d in here as they ship.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.routes import health, index

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"


def _configure_logging(level: str) -> None:
    """Configure root logging once on app construction.

    Uvicorn installs its own handlers; we set ours up before include so app
    code logs at the configured level regardless of how the process started.
    """
    logging.basicConfig(
        level=level.upper(),
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """App startup / shutdown hook.

    Phase 0: just log startup. Future tickets will plug DB engine creation,
    background scheduler launch, and connection-pool warmup in here.
    """
    settings = get_settings()
    logger.info(
        "fme-training-automation starting (env=%s, version=%s)",
        settings.environment,
        settings.app_version,
    )
    # TODO(KNOW-2260): initialise the SQLAlchemy engine + session factory here.
    # TODO(KNOW-2261): start the run scheduler background task here.
    yield
    logger.info("fme-training-automation shutting down")


def create_app() -> FastAPI:
    """Build the FastAPI app. Importing `app` at module level uses this."""
    settings = get_settings()
    _configure_logging(settings.log_level)

    fastapi_app = FastAPI(
        title="FME Training Automation",
        version=settings.app_version,
        lifespan=lifespan,
    )

    # Static assets — HTMX, Alpine, app.css. Vendored locally; no CDN.
    fastapi_app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )

    # Routes
    fastapi_app.include_router(health.router)
    fastapi_app.include_router(index.router)

    # TODO(future ticket): add CORSMiddleware with explicit `allow_origins`
    # before the first JSON-only API endpoint goes live. Use the App Runner
    # domain in production and `http://localhost:8000` in dev — never `"*"`.
    # See docs/plans/2026-04-29-multi-user-web-app.md (auth section).

    return fastapi_app


app = create_app()
