"""Release page render test (WS-D, sprint/ws-d).

Mirrors ``tests/unit/test_drafts_page.py``: builds the app via
``create_app()``, authenticates a seeded user, and asserts the key
controls + workflow copy are present on ``GET /release`` and that the nav
on ``GET /`` now links to ``/release``.

The page itself is a public browser route (the ``AuthMiddleware`` only
gates ``/api/*``); the data it calls lives behind the frozen
``/api/release-*`` contract. We authenticate anyway so the test exercises
the same ``create_app() + authenticate`` path the contract endpoints use.
"""

from __future__ import annotations

from typing import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings
from app.main import create_app


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def client(
    async_session_factory, seeded_user, authenticate, monkeypatch
) -> AsyncIterator[TestClient]:
    # Point the auth middleware's session lookup at the test DB so the
    # seeded user authenticates (the page is public, but this keeps the
    # fixture identical to the contract-endpoint integration tests).
    monkeypatch.setattr(
        "app.main._get_or_create_session_factory",
        lambda: async_session_factory,
    )
    reset_settings()
    try:
        app = create_app()
        with TestClient(app) as test_client:
            authenticate(test_client, seeded_user.id)
            yield test_client
    finally:
        reset_settings()


async def test_release_page_renders_controls(client: TestClient) -> None:
    res = client.get("/release")
    assert res.status_code == 200, res.text
    body = res.text

    # Version input/picker + check-status control.
    assert 'id="to-version"' in body
    assert 'id="check-status-btn"' in body

    # Plan preview control.
    assert 'id="preview-plan-btn"' in body

    # Execute + dry-run toggle (default on).
    assert 'id="execute-btn"' in body
    assert 'id="dry-run-toggle"' in body
    assert "checked" in body  # dry-run defaults ON

    # Link draft course form.
    assert 'id="link-draft-btn"' in body
    assert 'id="course-prefix"' in body
    assert 'id="skilljar-course-id"' in body

    # Calls the frozen contract endpoints.
    assert "/api/release-status" in body
    assert "/api/release-plan" in body
    assert "/api/release-execute" in body
    assert "/api/release-log" in body
    assert "/api/link-draft-course" in body

    # Reads errors from `detail`, not `error`.
    assert "detail" in body

    # The manual-publish note is required.
    assert "publish the draft manually in Skilljar" in body


async def test_release_page_no_tag_ui(client: TestClient) -> None:
    # Explicit acceptance: NO tag UI on the release page.
    res = client.get("/release")
    assert res.status_code == 200
    body = res.text.lower()
    assert "swap tag" not in body
    assert "manage tag" not in body


async def test_nav_includes_release_link(client: TestClient) -> None:
    res = client.get("/")
    assert res.status_code == 200
    assert 'href="/release"' in res.text
