"""Integration tests for the ``report_views`` usage metric (KNOW-2166).

``GET /report/{run_id}`` records one best-effort row per authenticated open
so the team can measure "was a report generated AND opened, in which release
cycle, by whom" without depending on the in-app accept/reject workflow.

These use the SQLite async harness from ``conftest``. The report router does
its DB write through the module-level ``session_factory`` (mirroring the auth
routes), so tests point that symbol at the test factory.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from starlette.middleware.sessions import SessionMiddleware

from app.auth import AuthMiddleware
from app.models.report_views import ReportView
from app.models.runs import Run
from app.routes import report as report_routes
from tests.conftest import auth_cookie_for, seed_active_user

SESSION_SECRET = "test-session-key-know-2166"


def _make_app(session_factory) -> FastAPI:
    """Minimal app: auth gate + session cookie + the report redirect router."""
    app = FastAPI()
    app.add_middleware(AuthMiddleware, session_factory=session_factory)
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET,
        session_cookie="fme_session",
        same_site="lax",
        https_only=False,
    )
    # The report router writes report_views via its module-level
    # ``session_factory`` (same pattern as auth routes). Point it at the test
    # factory so the write lands in the test DB.
    report_routes.session_factory = session_factory  # type: ignore[assignment]
    app.include_router(report_routes.router)
    return app


async def _seed_run(session_factory, run_id: str, *, created_by: int | None = None) -> None:
    async with session_factory() as session:
        session.add(Run(id=run_id, status="done", to_version="2026.1", created_by=created_by))
        await session.commit()


@pytest.fixture(autouse=True)
def _restore_report_factory():
    """Restore the report router's ``session_factory`` after each test so a
    patched (e.g. failing) factory never leaks into a later test."""
    original = report_routes.session_factory
    yield
    report_routes.session_factory = original


@pytest.mark.asyncio
async def test_authenticated_view_records_row(async_session_factory) -> None:
    """A signed-in open of a report writes one attributed report_views row and
    still 302-redirects to the static artifact."""
    app = _make_app(async_session_factory)
    user = await seed_active_user(async_session_factory, email="viewer@safe.com")
    run_id = "20260317T155430-28a8"
    await _seed_run(async_session_factory, run_id, created_by=user.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", follow_redirects=False
    ) as c:
        c.cookies.set(
            "fme_session", auth_cookie_for(user.id, secret=SESSION_SECRET, epoch=user.epoch)
        )
        resp = await c.get(f"/report/{run_id}")

    assert resp.status_code == 302
    assert resp.headers["location"] == f"/artifacts/{run_id}/report-{run_id}.html"

    async with async_session_factory() as session:
        views = (await session.scalars(select(ReportView))).all()
    assert len(views) == 1
    assert views[0].run_id == run_id
    assert views[0].user_id == user.id
    assert views[0].viewed_at is not None


@pytest.mark.asyncio
async def test_multiple_opens_append_rows(async_session_factory) -> None:
    """report_views is append-only: two opens by the same user = two rows."""
    app = _make_app(async_session_factory)
    user = await seed_active_user(async_session_factory, email="repeat@safe.com")
    run_id = "20260409T205350-9ec0"
    await _seed_run(async_session_factory, run_id, created_by=user.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", follow_redirects=False
    ) as c:
        c.cookies.set(
            "fme_session", auth_cookie_for(user.id, secret=SESSION_SECRET, epoch=user.epoch)
        )
        await c.get(f"/report/{run_id}")
        await c.get(f"/report/{run_id}?tab=lesson-edits")

    async with async_session_factory() as session:
        views = (await session.scalars(select(ReportView))).all()
    assert len(views) == 2
    assert {v.user_id for v in views} == {user.id}


@pytest.mark.asyncio
async def test_query_string_preserved_and_view_recorded(async_session_factory) -> None:
    """The deep-link query string is still forwarded, and the view is recorded."""
    app = _make_app(async_session_factory)
    user = await seed_active_user(async_session_factory, email="deeplink@safe.com")
    run_id = "20260610T120000-abcd"
    await _seed_run(async_session_factory, run_id, created_by=user.id)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", follow_redirects=False
    ) as c:
        c.cookies.set(
            "fme_session", auth_cookie_for(user.id, secret=SESSION_SECRET, epoch=user.epoch)
        )
        resp = await c.get(f"/report/{run_id}?tab=lesson-edits")

    assert resp.status_code == 302
    assert resp.headers["location"] == (
        f"/artifacts/{run_id}/report-{run_id}.html?tab=lesson-edits"
    )
    async with async_session_factory() as session:
        views = (await session.scalars(select(ReportView))).all()
    assert len(views) == 1


@pytest.mark.asyncio
async def test_unauthenticated_open_is_gated_and_records_nothing(
    async_session_factory,
) -> None:
    """No session cookie -> AuthMiddleware bounces to the landing page before
    the handler runs, so no report_views row is written."""
    app = _make_app(async_session_factory)
    run_id = "20260610T120000-abcd"
    await _seed_run(async_session_factory, run_id)

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", follow_redirects=False
    ) as c:
        resp = await c.get(f"/report/{run_id}")

    assert resp.status_code == 302
    assert resp.headers["location"] == "/"  # bounced to sign-in, not the artifact

    async with async_session_factory() as session:
        views = (await session.scalars(select(ReportView))).all()
    assert views == []


@pytest.mark.asyncio
async def test_recording_failure_does_not_break_redirect(async_session_factory) -> None:
    """If the view write blows up, the redirect to the report still succeeds
    (best-effort recording)."""
    app = _make_app(async_session_factory)
    user = await seed_active_user(async_session_factory, email="resilient@safe.com")
    run_id = "20260610T120000-abcd"
    await _seed_run(async_session_factory, run_id, created_by=user.id)

    # Auth hydration uses the middleware's own factory (async_session_factory);
    # only the report router's write path gets the exploding factory.
    def _boom(*args, **kwargs):
        raise RuntimeError("db is down")

    report_routes.session_factory = _boom  # type: ignore[assignment]

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", follow_redirects=False
    ) as c:
        c.cookies.set(
            "fme_session", auth_cookie_for(user.id, secret=SESSION_SECRET, epoch=user.epoch)
        )
        resp = await c.get(f"/report/{run_id}")

    assert resp.status_code == 302
    assert resp.headers["location"] == f"/artifacts/{run_id}/report-{run_id}.html"
