"""Integration tests for /api/drafts.

Drives the route end-to-end with a tmp drafts root and an in-memory
SQLite session. Skips the live storage initialisation by patching the
``_get_or_create_session_factory`` import target on the route module
to use the test session factory.
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings
from app.routes import drafts as drafts_route


@pytest.fixture
def configured_app(async_session_factory, tmp_path: Path, monkeypatch):
    """FastAPI app with the drafts root pointed at a temp dir + DB at SQLite."""
    monkeypatch.setattr(
        drafts_route,
        "_get_or_create_session_factory",
        lambda: async_session_factory,
    )
    monkeypatch.setenv("DRAFTS_ROOT", str(tmp_path))
    reset_settings()
    try:
        from app.main import create_app
        app = create_app()
        with TestClient(app) as client:
            yield client, tmp_path
    finally:
        reset_settings()


# ---- POST happy path -----------------------------------------------------

def test_save_draft_creates_row_and_file(configured_app) -> None:
    client, root = configured_app
    body = {
        "to_version": "2026.1",
        "path": "fme-form-basic/Connect To Data 2026.1/Lesson 1",
        "html_content": "<p>my draft</p>",
    }
    resp = client.post("/api/drafts", json=body)
    assert resp.status_code == 201, resp.text
    summary = resp.json()
    assert summary["to_version"] == "2026.1"
    assert summary["path"] == body["path"]
    assert summary["status"] == "draft"
    # File landed where expected.
    on_disk = (
        root / "2026.1" / "fme-form-basic" / "Connect To Data 2026.1" / "Lesson 1" / "index.html"
    )
    assert on_disk.read_text() == "<p>my draft</p>"


# ---- POST is idempotent on (to_version, path) ----------------------------

def test_re_save_updates_existing_row(configured_app) -> None:
    client, _ = configured_app
    body = {
        "to_version": "2026.1",
        "path": "lp/course/lesson",
        "html_content": "first",
    }
    first = client.post("/api/drafts", json=body).json()
    second = client.post(
        "/api/drafts",
        json={**body, "html_content": "second"},
    ).json()
    assert first["id"] == second["id"]  # same row, updated
    # And the new content is what GET returns.
    detail = client.get(f"/api/drafts/{second['id']}").json()
    assert detail["html_content"] == "second"


# ---- GET list + filters --------------------------------------------------

def test_list_drafts_filters_by_to_version(configured_app) -> None:
    client, _ = configured_app
    client.post("/api/drafts", json={
        "to_version": "2025.0", "path": "a/b/c", "html_content": "x"
    })
    client.post("/api/drafts", json={
        "to_version": "2026.1", "path": "a/b/c", "html_content": "y"
    })
    client.post("/api/drafts", json={
        "to_version": "2026.1", "path": "d/e/f", "html_content": "z"
    })

    all_drafts = client.get("/api/drafts").json()
    just_2026 = client.get("/api/drafts", params={"to_version": "2026.1"}).json()
    assert len(all_drafts) == 3
    assert len(just_2026) == 2
    assert {d["path"] for d in just_2026} == {"a/b/c", "d/e/f"}


def test_list_filters_by_status(configured_app) -> None:
    client, _ = configured_app
    saved = client.post("/api/drafts", json={
        "to_version": "2026.1", "path": "lp/c/l", "html_content": "x"
    }).json()
    # Archive it.
    archive_resp = client.delete(f"/api/drafts/{saved['id']}")
    assert archive_resp.status_code == 204

    drafts_only = client.get("/api/drafts", params={"status": "draft"}).json()
    archived_only = client.get("/api/drafts", params={"status": "archived"}).json()
    assert drafts_only == []
    assert len(archived_only) == 1
    assert archived_only[0]["id"] == saved["id"]


# ---- GET single ----------------------------------------------------------

def test_get_draft_returns_html_body(configured_app) -> None:
    client, _ = configured_app
    saved = client.post("/api/drafts", json={
        "to_version": "2026.1", "path": "lp/c/l", "html_content": "<p>body</p>"
    }).json()
    detail = client.get(f"/api/drafts/{saved['id']}")
    assert detail.status_code == 200
    body = detail.json()
    assert body["id"] == saved["id"]
    assert body["html_content"] == "<p>body</p>"


def test_get_unknown_draft_returns_404(configured_app) -> None:
    client, _ = configured_app
    resp = client.get("/api/drafts/999999")
    assert resp.status_code == 404


def test_get_when_file_missing_returns_404(configured_app) -> None:
    """If the row exists but the on-disk HTML is gone (someone manually
    deleted it), surface as 404 — the draft is effectively missing."""
    client, root = configured_app
    saved = client.post("/api/drafts", json={
        "to_version": "2026.1", "path": "lp/c/l", "html_content": "x"
    }).json()
    # Wipe the file out of band.
    Path(saved["s3_key"]).unlink()
    resp = client.get(f"/api/drafts/{saved['id']}")
    assert resp.status_code == 404


# ---- DELETE / archive ----------------------------------------------------

def test_archive_marks_status_but_keeps_file(configured_app) -> None:
    client, _ = configured_app
    saved = client.post("/api/drafts", json={
        "to_version": "2026.1", "path": "lp/c/l", "html_content": "x"
    }).json()
    on_disk = Path(saved["s3_key"])
    assert on_disk.exists()

    resp = client.delete(f"/api/drafts/{saved['id']}")
    assert resp.status_code == 204
    # File is preserved (audit trail).
    assert on_disk.exists()


def test_re_save_after_archive_un_archives(configured_app) -> None:
    """A user editing an archived draft should bring it back to active."""
    client, _ = configured_app
    saved = client.post("/api/drafts", json={
        "to_version": "2026.1", "path": "lp/c/l", "html_content": "x"
    }).json()
    client.delete(f"/api/drafts/{saved['id']}")

    re_saved = client.post("/api/drafts", json={
        "to_version": "2026.1", "path": "lp/c/l", "html_content": "y"
    }).json()
    assert re_saved["status"] == "draft"


def test_archive_refuses_promoted_drafts(configured_app, async_session_factory) -> None:
    """Promoted drafts (already pushed to Skilljar) must not be archivable
    via this endpoint — would confuse the Release tab."""
    import asyncio

    client, _ = configured_app
    saved = client.post("/api/drafts", json={
        "to_version": "2026.1", "path": "lp/c/l", "html_content": "x"
    }).json()

    # Manually flip the row to status='promoted' to simulate a prior push.
    async def _promote() -> None:
        from app.models.skilljar import LessonDraft
        async with async_session_factory() as session:
            row = await session.get(LessonDraft, saved["id"])
            row.status = "promoted"
            await session.commit()
    asyncio.get_event_loop().run_until_complete(_promote())

    resp = client.delete(f"/api/drafts/{saved['id']}")
    assert resp.status_code == 409


# ---- POST validation -----------------------------------------------------

def test_save_rejects_path_traversal(configured_app) -> None:
    client, _ = configured_app
    resp = client.post("/api/drafts", json={
        "to_version": "2026.1",
        "path": "../escape",
        "html_content": "x",
    })
    assert resp.status_code == 400


def test_save_rejects_invalid_to_version(configured_app) -> None:
    client, _ = configured_app
    resp = client.post("/api/drafts", json={
        "to_version": "abc",
        "path": "lp/c/l",
        "html_content": "x",
    })
    assert resp.status_code == 400
