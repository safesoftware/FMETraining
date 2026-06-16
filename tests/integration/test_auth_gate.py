"""KNOW-2366: the default-deny auth gate covers the whole app.

Regression guard for the finding that only ``/api/*`` was gated -- ``/drafts``,
``/release``, ``/report``, ``/artifacts``, and ``/lesson-content`` were reachable
(and ``/drafts`` + the report HTML leaked content) without a Google login.

Drives the REAL ``create_app()`` route table to prove the public allowlist and
the gate match the intended contract:

* public allowlist (``/``, ``/_ping``, ``/health``) -> reachable anonymously;
* protected browser pages -> anonymous gets a 302 redirect to the sign-in
  landing page;
* protected ``/api/*`` -> anonymous gets a 401 JSON;
* an authenticated user reaches a gated page.
"""

from __future__ import annotations

from typing import AsyncIterator

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.config import reset_settings
from app.db.session import get_session
from app.main import create_app


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def app(async_session_factory, monkeypatch) -> AsyncIterator[FastAPI]:
    # Point the middleware's user lookup at the test DB so a seeded user can
    # authenticate. (The anonymous assertions are rejected before routing, so
    # they don't touch it; this is here for the authenticated case.)
    monkeypatch.setattr(
        "app.main._get_or_create_session_factory",
        lambda: async_session_factory,
    )
    reset_settings()
    try:
        yield create_app()
    finally:
        reset_settings()


async def test_public_paths_reachable_anonymously(app: FastAPI) -> None:
    client = TestClient(app, follow_redirects=False)
    for path in ("/", "/_ping", "/health"):
        resp = client.get(path)
        assert resp.status_code == 200, (path, resp.status_code)


async def test_protected_pages_redirect_anonymous(app: FastAPI) -> None:
    client = TestClient(app, follow_redirects=False)
    for path in (
        "/drafts",
        "/release",
        "/report/20260101T000000-abcd",
        "/lesson-content/2026.1/lp/c/l/images/a.png",
    ):
        resp = client.get(path)
        assert resp.status_code == 302, (path, resp.status_code)
        assert resp.headers["location"] == "/", path


async def test_protected_api_rejects_anonymous(app: FastAPI) -> None:
    client = TestClient(app, follow_redirects=False)
    for path in ("/api/release-status", "/api/drafts"):
        resp = client.get(path)
        assert resp.status_code == 401, (path, resp.status_code)
        assert resp.json()["detail"] == "Authentication required"


async def test_authenticated_user_reaches_gated_page(
    app: FastAPI, async_session_factory, seeded_user, authenticate
) -> None:
    async def _override_get_session() -> AsyncIterator:
        session = async_session_factory()
        try:
            yield session
            await session.commit()
        finally:
            await session.close()

    app.dependency_overrides[get_session] = _override_get_session
    client = TestClient(app, follow_redirects=False)
    authenticate(client, seeded_user.id)
    resp = client.get("/drafts")
    assert resp.status_code == 200, resp.text
