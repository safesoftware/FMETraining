"""Integration tests for ``POST /api/skilljar-inventory/sync``.

Drives the route through FastAPI's ``TestClient`` so the throttle, the
single-flight lock, and the response shape all get exercised. The
Skilljar HTTP layer is monkey-patched to return a stub client so no
real API calls happen.
"""
from __future__ import annotations

from typing import AsyncIterator

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings
from app.routes import skilljar as skilljar_route


# ---- stubs ---------------------------------------------------------------

class _StubSkilljarClient:
    """Honors the same async-context-manager + list_*() interface that
    the real client exposes, so the route's `async with` works."""

    def __init__(self, *args, **kwargs) -> None:
        self.aclosed = False

    async def __aenter__(self) -> "_StubSkilljarClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        self.aclosed = True

    async def aclose(self) -> None:
        self.aclosed = True

    async def list_courses(self) -> AsyncIterator[dict]:
        yield {"id": "c1", "title": "Course 1", "tags": ["version:2026.1"]}

    async def list_lessons(self) -> AsyncIterator[dict]:
        yield {"id": "l1", "course_id": "c1", "title": "Lesson 1"}

    async def list_published_paths(self) -> AsyncIterator[dict]:
        yield {"id": "p1", "title": "Path 1", "courses": ["c1"]}


@pytest.fixture
def configured_app(async_session_factory, seeded_user, authenticate, monkeypatch):
    """Build the FastAPI app with the test session factory + stub client wired in."""
    # Reset throttle so this test isn't dependent on prior test runs.
    skilljar_route.reset_throttle_for_tests()

    monkeypatch.setattr(
        skilljar_route, "SkilljarClient", _StubSkilljarClient
    )
    monkeypatch.setattr(
        skilljar_route, "_get_or_create_session_factory",
        lambda: async_session_factory,
    )
    # Point the auth middleware's user lookup at the same test DB so the
    # seeded user authenticates past the /api/* gate (KNOW-2259).
    monkeypatch.setattr(
        "app.main._get_or_create_session_factory",
        lambda: async_session_factory,
    )
    # Pretend we have an API key configured.
    monkeypatch.setenv("SKILLJAR_API_KEY", "test-key-not-used")
    reset_settings()
    try:
        from app.main import create_app  # late import — pulls fresh settings
        app = create_app()
        with TestClient(app) as client:
            authenticate(client, seeded_user.id)
            yield client
    finally:
        reset_settings()


# ---- happy path ---------------------------------------------------------

def test_sync_endpoint_returns_counts(configured_app) -> None:
    response = configured_app.post("/api/skilljar-inventory/sync")
    assert response.status_code == 200, response.text
    body = response.json()
    assert "synced_at" in body
    assert body["courses"] == {"seen": 1, "inserted": 1, "updated": 0}
    assert body["lessons"] == {"seen": 1, "inserted": 1, "updated": 0}
    assert body["paths"] == {"seen": 1, "inserted": 1, "updated": 0}


# ---- throttle + reset ---------------------------------------------------

def test_second_call_within_throttle_window_returns_429(configured_app) -> None:
    first = configured_app.post("/api/skilljar-inventory/sync")
    assert first.status_code == 200

    second = configured_app.post("/api/skilljar-inventory/sync")
    assert second.status_code == 429
    assert "Retry-After" in second.headers
    assert int(second.headers["Retry-After"]) > 0


def test_reset_throttle_for_tests_clears_state(configured_app) -> None:
    """The escape hatch exists so test fixtures can reset module-level
    state between tests. Verifying it actually does."""
    first = configured_app.post("/api/skilljar-inventory/sync")
    assert first.status_code == 200

    skilljar_route.reset_throttle_for_tests()

    after_reset = configured_app.post("/api/skilljar-inventory/sync")
    assert after_reset.status_code == 200, after_reset.text


# ---- missing API key ----------------------------------------------------

def test_missing_api_key_returns_503(
    async_session_factory, seeded_user, authenticate, monkeypatch
) -> None:
    """If SKILLJAR_API_KEY is unset the endpoint should fail loudly with
    503, not crash inside the client."""
    skilljar_route.reset_throttle_for_tests()
    monkeypatch.setattr(
        skilljar_route, "SkilljarClient", _StubSkilljarClient
    )
    monkeypatch.setattr(
        skilljar_route, "_get_or_create_session_factory",
        lambda: async_session_factory,
    )
    # Authenticate past the /api/* gate (KNOW-2259): point the middleware's
    # user lookup at the test DB so the seeded user resolves.
    monkeypatch.setattr(
        "app.main._get_or_create_session_factory",
        lambda: async_session_factory,
    )

    # Force both lookup paths to "no key": pydantic-settings reads from
    # .env at Settings() construction, so just delenv-ing isn't enough
    # if a real .env on disk has the key set. Patch ``get_settings``
    # itself to return a stub with no key, and clear the env var too.
    monkeypatch.delenv("SKILLJAR_API_KEY", raising=False)

    class _NoKeySettings:
        skilljar_api_key = None
        environment = "test"
        app_version = "test"
        log_level = "INFO"
        run_concurrency = 2
        scheduler_poll_interval_s = 2.0
        task_dispatcher = "stub"
        database_url = None

    monkeypatch.setattr(skilljar_route, "get_settings", lambda: _NoKeySettings())

    reset_settings()
    try:
        from app.main import create_app
        app = create_app()
        with TestClient(app) as client:
            authenticate(client, seeded_user.id)
            response = client.post("/api/skilljar-inventory/sync")
        assert response.status_code == 503
        assert "SKILLJAR_API_KEY" in response.json()["detail"]
    finally:
        reset_settings()
