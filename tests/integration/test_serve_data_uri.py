"""
Integration tests for serve.py data-URI upload wiring.

Spins up a real _ThreadedHTTPServer in a background thread, posts to
/api/save-lesson and /api/skilljar-push with data:image base64 payloads,
and asserts that the upload helpers are invoked and the rewritten HTML
flows through to disk and to push_with_version_check.
"""

from __future__ import annotations

import base64
import json
import shutil
import threading
import urllib.request
from pathlib import Path
from unittest.mock import patch

import pytest

import serve
from serve import _Handler, _ThreadedHTTPServer


_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_PNG_B64 = base64.b64encode(_PNG_BYTES).decode()
_PNG_DATA_URI = f"data:image/png;base64,{_PNG_B64}"


@pytest.fixture
def http_server():
    """Start serve.py's HTTP server on an ephemeral port; yield base URL."""
    server = _ThreadedHTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.shutdown()
        server.server_close()


@pytest.fixture
def isolated_repo(tmp_path, monkeypatch):
    """Point serve.REPO_ROOT at a temp dir with a minimal source lesson layout."""
    src = tmp_path / "2025.0" / "fme-form-basic" / "Connect To Data 2025.0" / "My Lesson"
    src.mkdir(parents=True)
    (src / "index.html").write_text("<p>source</p>", encoding="utf-8")
    monkeypatch.setattr(serve, "REPO_ROOT", tmp_path)
    yield tmp_path


def _post_json(url: str, body: dict) -> tuple[int, dict]:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url, data=data, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body_bytes = exc.read()
        try:
            return exc.code, json.loads(body_bytes.decode())
        except json.JSONDecodeError:
            return exc.code, {"raw": body_bytes.decode("utf-8", errors="replace")}


_CONFIG_PATCHES = {
    "AWS_S3_BUCKET": "test-bucket",
    "AWS_ACCESS_KEY_ID": "fake-id",
    "AWS_SECRET_ACCESS_KEY": "fake-secret",
    "AWS_S3_REGION": "us-east-1",
    "SKILLJAR_API_KEY": "fake-api-key",
}


class TestSaveLessonWithDataUri:
    def test_data_uri_replaced_with_s3_url_on_disk(self, http_server, isolated_repo):
        public_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/x.png"
        html_with_uri = f'<p>diagram: <img src="{_PNG_DATA_URI}" alt="d"></p>'

        with patch.multiple("pipeline.config", **_CONFIG_PATCHES), \
             patch("pipeline.data_uri_upload._s3_put",
                   return_value=(public_url, "skilljar-uploads/x.png")):
            status, body = _post_json(
                f"{http_server}/api/save-lesson",
                {
                    "lesson_dir": "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson",
                    "to_version": "2026.1",
                    "html_content": html_with_uri,
                },
            )

        assert status == 200, body
        target = isolated_repo / body["target_path"]
        assert target.exists()
        saved = target.read_text(encoding="utf-8")
        assert _PNG_DATA_URI not in saved
        assert public_url in saved

    def test_no_data_uris_no_upload_called(self, http_server, isolated_repo):
        html = '<p>plain text, no images</p>'
        with patch("pipeline.data_uri_upload._s3_put") as mock_put:
            status, body = _post_json(
                f"{http_server}/api/save-lesson",
                {
                    "lesson_dir": "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson",
                    "to_version": "2026.1",
                    "html_content": html,
                },
            )
        assert status == 200, body
        mock_put.assert_not_called()
        target = isolated_repo / body["target_path"]
        assert "<p>plain text, no images</p>" in target.read_text(encoding="utf-8")

    def test_empty_paragraphs_around_images_stripped(self, http_server, isolated_repo):
        public_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/x.png"
        # Pattern from real contenteditable paste output: <p><img/></p><p></p>
        html_with_uri = (
            f'<p>before</p><p><img src="{_PNG_DATA_URI}"/></p><p></p>'
            f'<p>after</p>'
        )
        with patch.multiple("pipeline.config", **_CONFIG_PATCHES), \
             patch("pipeline.data_uri_upload._s3_put",
                   return_value=(public_url, "skilljar-uploads/x.png")):
            status, body = _post_json(
                f"{http_server}/api/save-lesson",
                {
                    "lesson_dir": "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson",
                    "to_version": "2026.1",
                    "html_content": html_with_uri,
                },
            )
        assert status == 200, body
        saved = (isolated_repo / body["target_path"]).read_text(encoding="utf-8")
        assert "<p></p>" not in saved
        assert public_url in saved

    def test_upload_failure_returns_500(self, http_server, isolated_repo):
        html_with_uri = f'<p><img src="{_PNG_DATA_URI}"></p>'

        with patch.multiple("pipeline.config", **_CONFIG_PATCHES), \
             patch("pipeline.data_uri_upload._s3_put",
                   side_effect=RuntimeError("HTTP 403: Forbidden")):
            status, body = _post_json(
                f"{http_server}/api/save-lesson",
                {
                    "lesson_dir": "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson",
                    "to_version": "2026.1",
                    "html_content": html_with_uri,
                },
            )

        assert status == 500
        assert "HTTP 403" in body.get("error", "")
        # File should NOT have been written when upload failed.
        target = isolated_repo / "2026.1" / "fme-form-basic" / "Connect To Data 2026.1" / "My Lesson" / "index.html"
        assert not target.exists()


class TestSkilljarPushWithDataUri:
    def test_data_uri_replaced_before_push(self, http_server, isolated_repo):
        public_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/x.png"
        html_with_uri = f'<p><img src="{_PNG_DATA_URI}"></p>'

        captured_html = {}

        def fake_push(lesson_dir, html, to_version, api_key, mapping, mapping_path, repo_root):
            captured_html["html"] = html
            return {
                "ok": True,
                "skilljar_lesson_id": "lid-1",
                "course_created": False,
                "lesson_created": False,
                "local_path": "2026.1/fme-form-basic/Connect To Data 2026.1/My Lesson/index.html",
                "error": None,
            }

        with patch.multiple("pipeline.config", **_CONFIG_PATCHES), \
             patch("pipeline.data_uri_upload._s3_put",
                   return_value=(public_url, "skilljar-uploads/x.png")), \
             patch("pipeline.skilljar_push.push_with_version_check", side_effect=fake_push), \
             patch("pipeline.skilljar_push.load_mapping", return_value={}):
            status, body = _post_json(
                f"{http_server}/api/skilljar-push",
                {
                    "lesson_dir": "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson",
                    "to_version": "2026.1",
                    "html": html_with_uri,
                },
            )

        assert status == 200, body
        assert _PNG_DATA_URI not in captured_html["html"]
        assert public_url in captured_html["html"]

    def test_push_upload_failure_returns_500_without_calling_push(self, http_server, isolated_repo):
        html_with_uri = f'<p><img src="{_PNG_DATA_URI}"></p>'

        with patch.multiple("pipeline.config", **_CONFIG_PATCHES), \
             patch("pipeline.data_uri_upload._s3_put",
                   side_effect=RuntimeError("Network error PUT s3://...")), \
             patch("pipeline.skilljar_push.push_with_version_check") as mock_push, \
             patch("pipeline.skilljar_push.load_mapping", return_value={}):
            status, body = _post_json(
                f"{http_server}/api/skilljar-push",
                {
                    "lesson_dir": "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson",
                    "to_version": "2026.1",
                    "html": html_with_uri,
                },
            )

        assert status == 500
        assert "Network error" in body.get("error", "")
        mock_push.assert_not_called()
