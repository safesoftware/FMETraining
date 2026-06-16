"""GET /lesson-content/{rel_path} serves lesson images (KNOW-2347).

The report points <img> at a stable same-origin /lesson-content/... URL; this
route streams the file from Settings.lesson_content_root (the same root the
pipeline reads lesson HTML from). KNOW-2366: it is gated by the default-deny
AuthMiddleware (lesson content isn't public) — a signed-in browser sends the
session cookie on the same-origin <img> request, so images still load.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.auth import AuthMiddleware
from app.config import reset_settings
from app.routes.lesson_content import router


def _write(root, rel, data=b"PNGBYTES"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


@pytest.fixture
def content_client(tmp_path, monkeypatch):
    monkeypatch.setenv("LESSON_CONTENT_ROOT", str(tmp_path))
    reset_settings()
    app = FastAPI()
    app.include_router(router)
    try:
        yield TestClient(app), tmp_path
    finally:
        reset_settings()


def test_serves_existing_image(content_client):
    client, root = content_client
    rel = "2025.1/lp/Course 2025.1/Lesson A/images/foo.png"
    _write(root, rel, b"PNGBYTES")
    resp = client.get("/lesson-content/" + rel)
    assert resp.status_code == 200
    # KNOW-2360: served as bytes via the content source (not FileResponse), with
    # the content type detected from the extension.
    assert resp.content == b"PNGBYTES"
    assert resp.headers["content-type"] == "image/png"


def test_serves_image_with_spaces_in_path(content_client):
    client, root = content_client
    rel = (
        "2025.1/fme-form-advanced/Improve Data Quality 2025.1/"
        "Exercise_ Handle Nulls/images/1724357278124.png"
    )
    _write(root, rel, b"SPACED")
    resp = client.get("/lesson-content/" + rel)
    assert resp.status_code == 200
    assert resp.content == b"SPACED"


def test_missing_image_returns_404(content_client):
    client, _root = content_client
    resp = client.get("/lesson-content/2025.1/lp/c/l/images/missing.png")
    assert resp.status_code == 404


def test_route_is_gated_under_auth_middleware(tmp_path, monkeypatch):
    """KNOW-2366: /lesson-content/ is NOT public — it carries lesson content,
    so the default-deny AuthMiddleware 302-redirects an anonymous request to
    the sign-in page. (A signed-in browser sends the session cookie on the
    same-origin <img> request, so images still load for authenticated users.)
    """
    monkeypatch.setenv("LESSON_CONTENT_ROOT", str(tmp_path))
    reset_settings()
    rel = "2025.1/lp/c/l/images/a.png"
    _write(tmp_path, rel, b"Z")
    app = FastAPI()
    app.add_middleware(AuthMiddleware, session_factory=None)
    app.include_router(router)
    try:
        resp = TestClient(app, follow_redirects=False).get(
            "/lesson-content/" + rel
        )
        assert resp.status_code == 302
        assert resp.headers["location"] == "/"
    finally:
        reset_settings()
