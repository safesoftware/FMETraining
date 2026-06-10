"""Smoke test for the FastAPI skeleton (KNOW-2258).

Intentionally tiny — KNOW-2265 owns the real test suite. This is just enough
to fail loudly if /health stops returning 200, the static mount is missing,
or the index template stops rendering HTMX/Alpine references.
"""
from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "version" in body


def test_index_renders_with_htmx_and_alpine() -> None:
    with TestClient(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    html = response.text
    # Unauthenticated: the index is the launch UI's signed-out state, which
    # gives a clear sign-in entry point (KNOW-2335 replaced the Phase-0
    # placeholder). Returns 200, not 401.
    assert "/auth/login" in html
    # Static script references — proves both vendor files are wired in (base.html).
    assert "/static/htmx.min.js" in html
    assert "/static/alpine.min.js" in html


def test_ping_returns_pong() -> None:
    """The HTMX demo button targets this endpoint; keep the contract stable."""
    with TestClient(app) as client:
        response = client.get("/_ping")
    assert response.status_code == 200
    assert response.text == "pong"
