"""Integration tests for ``POST /api/save-lesson``.

Drives the route through FastAPI's ``TestClient`` so the auth gate, the
``Settings``-resolved content root + S3 creds, and the frozen response
contract all get exercised. The image-upload helper is stubbed so no real
S3 / network calls happen.

The route lives in ``app/routes/save_lesson.py`` but is not (yet) wired into
``app.main.create_app`` on this branch, so the fixture registers the router
on the built app explicitly — mirroring how the app will ``include_router``
it once the integrator lands the wiring.
"""
from __future__ import annotations

import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings
from app.routes import save_lesson as save_lesson_route

SAMPLE_LESSON_HTML = (
    Path(__file__).parent.parent / "fixtures" / "sample_lesson.html"
)

# A valid 4+ part source lesson_dir laid down under the content root below.
SRC_VERSION = "2025.0"
LP = "fme-form-basic"
COURSE_FOLDER = "Connect To Data 2025.0"
LESSON = "My Lesson"
LESSON_DIR = f"{SRC_VERSION}/{LP}/{COURSE_FOLDER}/{LESSON}"
EXPECTED_TARGET = f"2026.1/{LP}/Connect To Data 2026.1/{LESSON}/index.html"


@pytest.fixture
def configured_app(
    async_session_factory, seeded_user, authenticate, tmp_path: Path, monkeypatch
):
    """FastAPI app with the SOURCE content root and a SEPARATE writable
    saved-versions root, both at temp trees, image upload stubbed."""
    # Lay down a minimal source lesson tree under the temp content root.
    content_root = tmp_path / "content"
    saved_root = tmp_path / "saved"
    src = content_root / SRC_VERSION / LP / COURSE_FOLDER / LESSON
    src.mkdir(parents=True)
    if SAMPLE_LESSON_HTML.exists():
        shutil.copy(SAMPLE_LESSON_HTML, src / "index.html")
    else:  # defensive: fixture file should exist, but don't hard-depend on it
        (src / "index.html").write_text("<p>source</p>", encoding="utf-8")
    (src / "images").mkdir()
    (src / "images" / "diagram.png").write_bytes(b"\x89PNG fake")

    # Stub the image upload so the route's real write_lesson never touches S3.
    from app.services import lesson_writer

    monkeypatch.setattr(
        lesson_writer,
        "_upload_lesson_images",
        lambda html, lesson_dir, **kwargs: html,
    )

    # Point the auth middleware's user lookup at the test DB so the seeded
    # user authenticates past the /api/* gate (KNOW-2259).
    monkeypatch.setattr(
        "app.main._get_or_create_session_factory",
        lambda: async_session_factory,
    )
    # Source reads come from LESSON_CONTENT_ROOT; the WRITE target is the
    # separate writable SAVED_VERSIONS_ROOT.
    monkeypatch.setenv("LESSON_CONTENT_ROOT", str(content_root))
    monkeypatch.setenv("SAVED_VERSIONS_ROOT", str(saved_root))
    reset_settings()
    try:
        from app.main import create_app  # late import — pulls fresh settings

        app = create_app()
        # Not wired into main.py on this branch; register it here so the
        # endpoint is reachable under the same middleware stack.
        app.include_router(save_lesson_route.router)
        with TestClient(app) as client:
            authenticate(client, seeded_user.id)
            yield client, content_root, saved_root
    finally:
        reset_settings()


# ---- happy path ----------------------------------------------------------

def test_save_writes_file_under_saved_root_not_content_root(configured_app) -> None:
    client, content_root, saved_root = configured_app
    resp = client.post(
        "/api/save-lesson",
        json={
            "lesson_dir": LESSON_DIR,
            "to_version": "2026.1",
            "html_content": "<p>accepted edits</p>",
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body == {"target_path": EXPECTED_TARGET}
    on_disk = saved_root / EXPECTED_TARGET
    assert "accepted edits" in on_disk.read_text(encoding="utf-8")
    # Self-contained saved lesson: no relative images/ dir copied alongside.
    assert not (on_disk.parent / "images").exists()
    # Nothing written under the (read-only under s3mirror) content root.
    assert not (content_root / EXPECTED_TARGET).exists()


# ---- 409 on re-POST without force ----------------------------------------

def test_resave_without_force_returns_409_with_top_level_target_path(
    configured_app,
) -> None:
    client, _, _ = configured_app
    first = client.post(
        "/api/save-lesson",
        json={
            "lesson_dir": LESSON_DIR,
            "to_version": "2026.1",
            "html_content": "<p>v1</p>",
        },
    )
    assert first.status_code == 200, first.text

    second = client.post(
        "/api/save-lesson",
        json={
            "lesson_dir": LESSON_DIR,
            "to_version": "2026.1",
            "html_content": "<p>v2</p>",
        },
    )
    assert second.status_code == 409, second.text
    body = second.json()
    # Frozen contract: top-level target_path (NOT under `detail`) + exists flag.
    assert body["target_path"] == EXPECTED_TARGET
    assert body["exists"] is True
    assert "detail" not in body


# ---- force overwrites ----------------------------------------------------

def test_force_overwrites_existing(configured_app) -> None:
    client, _content_root, saved_root = configured_app
    client.post(
        "/api/save-lesson",
        json={
            "lesson_dir": LESSON_DIR,
            "to_version": "2026.1",
            "html_content": "<p>original</p>",
        },
    )
    resp = client.post(
        "/api/save-lesson",
        json={
            "lesson_dir": LESSON_DIR,
            "to_version": "2026.1",
            "html_content": "<p>replacement</p>",
            "force": True,
        },
    )
    assert resp.status_code == 200, resp.text
    on_disk = saved_root / EXPECTED_TARGET
    saved = on_disk.read_text(encoding="utf-8")
    assert "replacement" in saved
    assert "original" not in saved


# ---- 400 on bad lesson_dir -----------------------------------------------

def test_shallow_lesson_dir_returns_400(configured_app) -> None:
    client, _, _ = configured_app
    resp = client.post(
        "/api/save-lesson",
        json={
            "lesson_dir": "2025.0/lp/course",  # only 3 parts
            "to_version": "2026.1",
            "html_content": "<p>x</p>",
        },
    )
    assert resp.status_code == 400, resp.text
    assert "shallow" in resp.json()["detail"]


def test_missing_fields_returns_400(configured_app) -> None:
    client, _, _ = configured_app
    resp = client.post(
        "/api/save-lesson",
        json={
            "lesson_dir": "  ",
            "to_version": "2026.1",
            "html_content": "<p>x</p>",
        },
    )
    assert resp.status_code == 400, resp.text
    assert "required" in resp.json()["detail"]
