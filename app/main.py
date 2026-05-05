"""FastAPI application factory and ASGI entrypoint.

Phase 0 wires:
    - settings via pydantic-settings (KNOW-2258)
    - static + Jinja2 templates (KNOW-2258)
    - placeholder index + health routes (KNOW-2258)
    - SQLAlchemy session factory (KNOW-2260)
    - run scheduler background task (KNOW-2269)

Auth and run endpoints land in sibling tickets and will be
`app.include_router(...)`'d in here as they ship.
"""
from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Optional

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.config import get_settings
from app.db.engine import _get_or_create_session_factory
from app.routes import health, index
from app.services.run_scheduler import RunScheduler
from app.services.task_dispatcher import (
    InProcessTaskDispatcher,
    StubTaskDispatcher,
    TaskDispatcher,
)
from app.services.worker_lifecycle import run_worker

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


def _build_dispatcher(
    kind: str,
    session_factory: async_sessionmaker[AsyncSession],
) -> TaskDispatcher:
    """Pick a TaskDispatcher per ``Settings.task_dispatcher``.

    Production wiring of ``EcsRunTaskDispatcher`` lands once the Fargate
    cluster is deployed. For now we expose 'stub' (tests / disabled) and
    'in-process' (local dev).
    """
    kind = (kind or "").strip().lower()
    if kind == "stub":
        return StubTaskDispatcher()
    if kind in ("in-process", "inprocess", "local"):
        async def _worker_callable(run_id: str) -> None:
            await run_worker(run_id, session_factory=session_factory)
        return InProcessTaskDispatcher(_worker_callable)
    if kind == "ecs":
        raise NotImplementedError(
            "ECS dispatcher will be wired in once the Fargate cluster lands "
            "(Part C step 3 of the deployment plan)."
        )
    raise ValueError(f"Unknown task_dispatcher: {kind!r}")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """App startup / shutdown hook.

    Brings up the DB engine + session factory, then the run scheduler.
    On shutdown, stops the scheduler so background tasks drain cleanly.
    """
    settings = get_settings()
    logger.info(
        "fme-training-automation starting (env=%s, version=%s)",
        settings.environment,
        settings.app_version,
    )

    scheduler: Optional[RunScheduler] = None

    # DB + scheduler only come up if a DATABASE_URL is configured. In a
    # totally unconfigured local environment (no compose, no .env) the app
    # still serves /health and /static so devs can poke at it.
    if settings.database_url or os.environ.get("DATABASE_URL"):
        try:
            session_factory = _get_or_create_session_factory()
        except RuntimeError as exc:
            logger.warning("DB not ready, scheduler disabled: %s", exc)
        else:
            dispatcher = _build_dispatcher(settings.task_dispatcher, session_factory)
            scheduler = RunScheduler(
                session_factory=session_factory,
                dispatcher=dispatcher,
                concurrency=settings.run_concurrency,
                poll_interval_s=settings.scheduler_poll_interval_s,
            )
            await scheduler.start()
    else:
        logger.warning("DATABASE_URL not set; skipping DB + scheduler startup")

    try:
        yield
    finally:
        if scheduler is not None:
            await scheduler.stop()
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
