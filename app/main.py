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
from starlette.middleware.sessions import SessionMiddleware

from app.auth import AuthMiddleware, init_google_oauth
from app.config import get_settings
from app.db.engine import _get_or_create_session_factory
from app.routes import (
    auth,
    drafts,
    health,
    index,
    lesson_content,
    release_page,
    report,
    report_drafts,
    runs,
    save_lesson,
    skilljar,
    skilljar_release,
    sse,
)
from app.services.pipeline_runner import make_step_body
from app.services.run_scheduler import RunScheduler
from app.services.task_dispatcher import (
    InProcessTaskDispatcher,
    StubTaskDispatcher,
    SystemdTaskDispatcher,
    TaskDispatcher,
)
from app.services.worker_lifecycle import run_worker

logger = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).resolve().parent / "static"
# KNOW-2334: artifacts_root is now driven by Settings; the legacy constant
# pointing at <repo_root>/artifacts is kept as a fallback for the static mount
# path (will be resolved at app-creation time).
_LEGACY_ARTIFACTS_DIR = Path(__file__).resolve().parent.parent / "artifacts"


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

    Production uses ``systemd`` (``SystemdTaskDispatcher``); local dev uses
    ``in-process``; tests use ``stub``.
    """
    kind = (kind or "").strip().lower()
    if kind == "stub":
        return StubTaskDispatcher()
    if kind in ("in-process", "inprocess", "local"):
        # KNOW-2334: inject the real pipeline step body so in-process workers
        # run the actual pipeline, not the stub.
        _real_step_body = make_step_body()

        async def _worker_callable(run_id: str) -> None:
            await run_worker(
                run_id,
                session_factory=session_factory,
                step_body=_real_step_body,
            )
        return InProcessTaskDispatcher(_worker_callable)
    if kind == "systemd":
        return SystemdTaskDispatcher()
    raise ValueError(
        f"Unknown task_dispatcher: {kind!r}. "
        "Supported values: 'stub', 'in-process', 'systemd'."
    )


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

    # ---- Auth middleware stack ----------------------------------------
    # SessionMiddleware signs the cookie via itsdangerous. We only mount
    # it when a signing key is configured; without one, sign-in routes
    # won't work but the app still serves /health and /static so
    # configuration mistakes are easy to diagnose.
    if settings.session_signing_key:
        # Note ordering: in Starlette, the FIRST-added middleware is the
        # INNERMOST. AuthMiddleware needs to run AFTER SessionMiddleware
        # populates scope["session"], so it must be added first.
        try:
            session_fac = _get_or_create_session_factory()
        except RuntimeError:
            session_fac = None
        fastapi_app.add_middleware(AuthMiddleware, session_factory=session_fac)
        # SessionMiddleware hardcodes httponly=True (it doesn't expose
        # the kwarg), which is what we want -- the session cookie holds
        # the user's identity and must never be reachable from JS.
        fastapi_app.add_middleware(
            SessionMiddleware,
            secret_key=settings.session_signing_key,
            session_cookie="fme_session",
            max_age=14 * 24 * 60 * 60,  # 14-day rolling expiry
            same_site="lax",
            https_only=settings.environment == "production",
            path="/",
        )
        # Register the Google OAuth client (no-op if creds missing).
        init_google_oauth(settings)
    else:
        logger.warning(
            "SESSION_SIGNING_KEY not set; auth disabled. Set it in .env "
            "before deploying."
        )

    # Static assets — HTMX, Alpine, app.css. Vendored locally; no CDN.
    fastapi_app.mount(
        "/static",
        StaticFiles(directory=str(STATIC_DIR)),
        name="static",
    )

    # Same-origin mount for the static report HTML emitted by
    # ``pipeline/report.py``. Lets the report's embedded JS auto-save to
    # the FastAPI editor-state endpoints without CORS plumbing.
    # KNOW-2276 (Phase 1a). Phase 2 will move the report into a Jinja
    # template + this mount goes away.
    # KNOW-2340: serve the configured Settings.artifacts_root (where the worker
    # writes). Create it at startup so the mount always points at the real dir —
    # without this, a missing dir on first boot fell back to <repo>/artifacts and
    # completed-run reports 404'd. Legacy dir is only a last resort if the
    # configured root can't be created (e.g. a permissions problem).
    artifacts_dir = Path(settings.artifacts_root)
    try:
        artifacts_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        logger.warning(
            "could not create artifacts_root %s; falling back to %s",
            artifacts_dir,
            _LEGACY_ARTIFACTS_DIR,
        )
        artifacts_dir = _LEGACY_ARTIFACTS_DIR
    if artifacts_dir.exists():
        fastapi_app.mount(
            "/artifacts",
            StaticFiles(directory=str(artifacts_dir)),
            name="artifacts",
        )

    # Routes
    fastapi_app.include_router(health.router)
    fastapi_app.include_router(index.router)
    fastapi_app.include_router(auth.router)
    fastapi_app.include_router(drafts.router)
    fastapi_app.include_router(report_drafts.router)
    fastapi_app.include_router(report.router)
    # KNOW-2347: serve lesson content images the report references, so they
    # don't 404 against the /artifacts mount (which only serves artifacts_root).
    fastapi_app.include_router(lesson_content.router)
    fastapi_app.include_router(runs.router)
    fastapi_app.include_router(skilljar.router)
    # release-sprint (feature/publish-in-app): stub routers wired once at the
    # foundation so the parallel WS agents never contend on main.py.
    fastapi_app.include_router(save_lesson.router)
    fastapi_app.include_router(skilljar_release.router)
    fastapi_app.include_router(release_page.router)
    fastapi_app.include_router(sse.router)

    # TODO(future ticket): add CORSMiddleware with explicit `allow_origins`
    # before the first JSON-only API endpoint goes live. Use the App Runner
    # domain in production and `http://localhost:8000` in dev — never `"*"`.
    # See docs/plans/2026-04-29-multi-user-web-app.md (auth section).

    return fastapi_app


app = create_app()
