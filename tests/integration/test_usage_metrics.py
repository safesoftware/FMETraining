"""Integration tests for the usage metrics endpoint + panel (KNOW-2166).

Covers ``GET /api/metrics/usage`` (JSON) and ``GET /usage`` (HTML panel),
including auth gating and the distinct-not-summed totals semantics.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from httpx import ASGITransport, AsyncClient
from starlette.middleware.sessions import SessionMiddleware

from app.auth import AuthMiddleware
from app.db.session import get_session
from app.models.report_views import ReportView
from app.models.runs import Run
from app.routes import metrics as metrics_routes
from tests.conftest import auth_cookie_for, seed_active_user

SESSION_SECRET = "test-session-key-know-2166-usage"
_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "static"


def _make_app(session_factory) -> FastAPI:
    app = FastAPI()
    app.add_middleware(AuthMiddleware, session_factory=session_factory)
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET,
        session_cookie="fme_session",
        same_site="lax",
        https_only=False,
    )
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

    async def _get_session_override():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    app.include_router(metrics_routes.router)
    return app


async def _seed_dataset(session_factory) -> dict:
    """Two users, three runs across two versions, four report opens.

    2026.1: run1 (alice), run2 (bob); opens: alice x2 + bob x1 on run1.
    2025.0: run3 (alice); opens: alice x1 on run3.
    """
    alice = await seed_active_user(session_factory, email="alice@safe.com")
    bob = await seed_active_user(session_factory, email="bob@safe.com")
    async with session_factory() as s:
        s.add_all(
            [
                Run(id="run1", status="done", to_version="2026.1", created_by=alice.id),
                Run(id="run2", status="done", to_version="2026.1", created_by=bob.id),
                Run(id="run3", status="done", to_version="2025.0", created_by=alice.id),
            ]
        )
        await s.commit()
        s.add_all(
            [
                ReportView(run_id="run1", user_id=alice.id),
                ReportView(run_id="run1", user_id=alice.id),
                ReportView(run_id="run1", user_id=bob.id),
                ReportView(run_id="run3", user_id=alice.id),
            ]
        )
        await s.commit()
    return {"alice": alice, "bob": bob}


@pytest.mark.asyncio
async def test_usage_api_requires_auth(async_session_factory) -> None:
    app = _make_app(async_session_factory)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        resp = await c.get("/api/metrics/usage")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_usage_api_aggregates(async_session_factory) -> None:
    app = _make_app(async_session_factory)
    data = await _seed_dataset(async_session_factory)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        c.cookies.set(
            "fme_session",
            auth_cookie_for(data["alice"].id, secret=SESSION_SECRET),
        )
        resp = await c.get("/api/metrics/usage")

    assert resp.status_code == 200
    body = resp.json()

    # Totals are DISTINCT across versions, not summed: alice is active in both
    # versions but must count once (total_viewers == 2, not 3).
    assert body["total_runs"] == 3
    assert body["total_runners"] == 2
    assert body["total_opens"] == 4
    assert body["total_viewers"] == 2

    by_ver = {v["to_version"]: v for v in body["versions"]}
    assert by_ver["2026.1"]["runs"] == 2
    assert by_ver["2026.1"]["runners"] == 2
    assert by_ver["2026.1"]["opens"] == 3
    assert by_ver["2026.1"]["viewers"] == 2
    # run2's report was never opened → only 1 distinct run opened this cycle.
    assert by_ver["2026.1"]["reports_opened"] == 1
    assert by_ver["2026.1"]["last_open"] is not None

    assert by_ver["2025.0"]["runs"] == 1
    assert by_ver["2025.0"]["runners"] == 1
    assert by_ver["2025.0"]["opens"] == 1
    assert by_ver["2025.0"]["viewers"] == 1
    assert by_ver["2025.0"]["reports_opened"] == 1


@pytest.mark.asyncio
async def test_usage_api_versions_sorted_newest_first(async_session_factory) -> None:
    app = _make_app(async_session_factory)
    data = await _seed_dataset(async_session_factory)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        c.cookies.set(
            "fme_session", auth_cookie_for(data["alice"].id, secret=SESSION_SECRET)
        )
        resp = await c.get("/api/metrics/usage")
    versions = [v["to_version"] for v in resp.json()["versions"]]
    assert versions == ["2026.1", "2025.0"]


@pytest.mark.asyncio
async def test_usage_api_empty(async_session_factory) -> None:
    app = _make_app(async_session_factory)
    user = await seed_active_user(async_session_factory, email="empty@safe.com")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        c.cookies.set("fme_session", auth_cookie_for(user.id, secret=SESSION_SECRET))
        resp = await c.get("/api/metrics/usage")
    assert resp.status_code == 200
    body = resp.json()
    assert body["versions"] == []
    assert body["total_runs"] == 0
    assert body["total_opens"] == 0
    assert body["total_viewers"] == 0


@pytest.mark.asyncio
async def test_usage_page_renders(async_session_factory) -> None:
    app = _make_app(async_session_factory)
    data = await _seed_dataset(async_session_factory)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        c.cookies.set(
            "fme_session", auth_cookie_for(data["alice"].id, secret=SESSION_SECRET)
        )
        resp = await c.get("/usage")
    assert resp.status_code == 200
    assert "Usage" in resp.text
    assert "2026.1" in resp.text
    assert "distinct viewers" in resp.text


@pytest.mark.asyncio
async def test_usage_page_requires_auth(async_session_factory) -> None:
    app = _make_app(async_session_factory)
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://testserver", follow_redirects=False
    ) as c:
        resp = await c.get("/usage")
    # Middleware bounces an unauthenticated browser navigation to the landing page.
    assert resp.status_code == 302
    assert resp.headers["location"] == "/"
