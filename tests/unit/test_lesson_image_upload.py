"""Unit tests for pipeline/lesson_image_upload.py.

Covers extract_and_upload_data_uris (data: URI pass) and upload_lesson_images
(orchestrator that also handles relative paths and expiring pre-signed URLs).
"""

from __future__ import annotations

import base64
from unittest.mock import patch

import pytest

from pipeline.lesson_image_upload import (
    extract_and_upload_data_uris,
    upload_lesson_images,
)

_S3_ARGS = dict(
    s3_bucket="test-bucket",
    s3_key_id="fake-id",
    s3_secret="fake-secret",
    s3_region="us-east-1",
)

_PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 16
_PNG_B64 = base64.b64encode(_PNG_BYTES).decode()
_PNG_DATA_URI = f"data:image/png;base64,{_PNG_B64}"

_JPG_BYTES = b"\xff\xd8\xff" + b"\x00" * 8
_JPG_B64 = base64.b64encode(_JPG_BYTES).decode()
_JPG_DATA_URI = f"data:image/jpeg;base64,{_JPG_B64}"

_EXPIRING_URL = (
    "https://everpath-course-content.s3.amazonaws.com/instructor/x/assets/123/"
    "abc-foo.png?AWSAccessKeyId=AKIA&Signature=sig%3D&Expires=1777324413"
)


# ----- extract_and_upload_data_uris -----------------------------------------

class TestExtractAndUploadDataUris:
    def test_no_data_uris_returns_html_unchanged(self):
        html = '<p>hello <img src="images/foo.png"> world <img src="https://cdn.example.com/x.jpg"></p>'
        result_html, log = extract_and_upload_data_uris(html, **_S3_ARGS)
        assert result_html == html
        assert log == []

    def test_single_data_uri_uploads_and_rewrites(self):
        html = f'<p>see <img src="{_PNG_DATA_URI}" alt="diagram"> for details.</p>'
        public_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/abc-pasted-x.png"

        with patch("pipeline.lesson_image_upload._s3_put",
                   return_value=(public_url, "skilljar-uploads/abc-pasted-x.png")) as mock_put:
            result_html, log = extract_and_upload_data_uris(html, **_S3_ARGS)

        assert _PNG_DATA_URI not in result_html
        assert f'src="{public_url}"' in result_html
        assert mock_put.call_count == 1
        assert len(log) == 1
        assert log[0]["url"] == public_url

    def test_duplicate_data_uris_uploaded_once(self):
        html = (
            f'<p><img src="{_PNG_DATA_URI}"> and again '
            f'<img src="{_PNG_DATA_URI}" class="thumb"></p>'
        )
        public_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/abc-pasted-x.png"
        with patch("pipeline.lesson_image_upload._s3_put",
                   return_value=(public_url, "skilljar-uploads/abc-pasted-x.png")) as mock_put:
            result_html, log = extract_and_upload_data_uris(html, **_S3_ARGS)
        assert result_html.count(f'src="{public_url}"') == 2
        assert mock_put.call_count == 1
        assert len(log) == 1

    def test_two_distinct_data_uris_both_uploaded(self):
        html = f'<p><img src="{_PNG_DATA_URI}"><img src="{_JPG_DATA_URI}"></p>'
        urls = iter([
            ("https://s3.us-east-1.amazonaws.com/test-bucket/png.png", "k1"),
            ("https://s3.us-east-1.amazonaws.com/test-bucket/jpg.jpg", "k2"),
        ])
        with patch("pipeline.lesson_image_upload._s3_put",
                   side_effect=lambda *a, **kw: next(urls)):
            result_html, log = extract_and_upload_data_uris(html, **_S3_ARGS)
        assert "test-bucket/png.png" in result_html
        assert "test-bucket/jpg.jpg" in result_html
        assert len(log) == 2

    def test_upload_failure_raises(self):
        html = f'<p><img src="{_PNG_DATA_URI}"></p>'
        with patch("pipeline.lesson_image_upload._s3_put",
                   side_effect=RuntimeError("HTTP 403 PUT s3://...: Forbidden")):
            with pytest.raises(RuntimeError, match="HTTP 403"):
                extract_and_upload_data_uris(html, **_S3_ARGS)

    def test_missing_s3_credentials_raises(self):
        html = f'<p><img src="{_PNG_DATA_URI}"></p>'
        args = {**_S3_ARGS, "s3_bucket": ""}
        with pytest.raises(RuntimeError, match="AWS_S3_BUCKET"):
            extract_and_upload_data_uris(html, **args)

    def test_missing_credentials_with_no_data_uris_does_not_raise(self):
        html = '<p>no images</p>'
        args = {**_S3_ARGS, "s3_bucket": ""}
        result_html, log = extract_and_upload_data_uris(html, **args)
        assert result_html == html
        assert log == []

    def test_invalid_base64_raises(self):
        html = '<img src="data:image/png;base64,!!!not-valid-base64!!!">'
        with patch("pipeline.lesson_image_upload._s3_put"):
            with pytest.raises(RuntimeError, match="Invalid base64"):
                extract_and_upload_data_uris(html, **_S3_ARGS)

    def test_single_quoted_src_supported(self):
        html = f"<img src='{_PNG_DATA_URI}'>"
        public_url = "https://s3.us-east-1.amazonaws.com/test-bucket/x.png"
        with patch("pipeline.lesson_image_upload._s3_put",
                   return_value=(public_url, "skilljar-uploads/x.png")):
            result_html, _ = extract_and_upload_data_uris(html, **_S3_ARGS)
        assert public_url in result_html


# ----- upload_lesson_images (the orchestrator) ------------------------------

class TestUploadLessonImages:
    def _setup_lesson(self, tmp_path):
        """Create a fake repo with a lesson dir and images/ folder."""
        lesson_dir = "ver/lp/course/lesson"
        images_dir = tmp_path / lesson_dir / "images"
        images_dir.mkdir(parents=True)
        return lesson_dir, images_dir

    def test_relative_path_uploaded_from_local_images_folder(self, tmp_path):
        lesson_dir, images_dir = self._setup_lesson(tmp_path)
        (images_dir / "foo.png").write_bytes(b"\x89PNG fake")
        html = '<p><img src="images/foo.png" alt="x"></p>'
        s3_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/foo.png"

        with patch("pipeline.skilljar_release._s3_put",
                   return_value=(s3_url, "skilljar-uploads/foo.png")) as mock_put:
            result_html, log = upload_lesson_images(
                html, lesson_dir=lesson_dir, repo_root=tmp_path, **_S3_ARGS,
            )

        assert s3_url in result_html
        assert 'src="images/foo.png"' not in result_html
        mock_put.assert_called_once()
        assert any(e.get("source") == "relative" for e in log)

    def test_expiring_everpath_url_replaced_via_local_file_match(self, tmp_path):
        lesson_dir, images_dir = self._setup_lesson(tmp_path)
        (images_dir / "abc-foo.png").write_bytes(b"\x89PNG fake")
        html = f'<p><img src="{_EXPIRING_URL}"></p>'
        s3_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/abc-foo.png"

        with patch("pipeline.lesson_image_upload._s3_put",
                   return_value=(s3_url, "skilljar-uploads/abc-foo.png")):
            result_html, log = upload_lesson_images(
                html, lesson_dir=lesson_dir, repo_root=tmp_path, **_S3_ARGS,
            )

        assert _EXPIRING_URL not in result_html
        assert s3_url in result_html
        assert any(e.get("source") == "expiring_url" for e in log)

    def test_expiring_url_html_encoded_ampersands_replaced(self, tmp_path):
        lesson_dir, images_dir = self._setup_lesson(tmp_path)
        (images_dir / "abc-foo.png").write_bytes(b"\x89PNG fake")
        html = (
            '<p><img src="https://everpath-course-content.s3.amazonaws.com/x/'
            'assets/1/abc-foo.png?AWSAccessKeyId=K&amp;Signature=s&amp;Expires=1"></p>'
        )
        s3_url = "https://s3.us-east-1.amazonaws.com/test-bucket/skilljar-uploads/abc-foo.png"
        with patch("pipeline.lesson_image_upload._s3_put",
                   return_value=(s3_url, "skilljar-uploads/abc-foo.png")):
            result_html, _ = upload_lesson_images(
                html, lesson_dir=lesson_dir, repo_root=tmp_path, **_S3_ARGS,
            )
        assert "everpath-course-content" not in result_html
        assert s3_url in result_html

    def test_expiring_url_no_local_match_raises_with_filename(self, tmp_path):
        lesson_dir, _ = self._setup_lesson(tmp_path)
        html = f'<p><img src="{_EXPIRING_URL}"></p>'
        with pytest.raises(RuntimeError, match="abc-foo.png"):
            upload_lesson_images(
                html, lesson_dir=lesson_dir, repo_root=tmp_path, **_S3_ARGS,
            )

    def test_permanent_s3_url_left_alone(self, tmp_path):
        lesson_dir, _ = self._setup_lesson(tmp_path)
        permanent = "https://s3.us-east-1.amazonaws.com/FMETraining/skilljar-uploads/abc-x.png"
        html = f'<p><img src="{permanent}"></p>'
        with patch("pipeline.lesson_image_upload._s3_put") as mock_put, \
             patch("pipeline.skilljar_release._s3_put") as mock_put_release:
            result_html, log = upload_lesson_images(
                html, lesson_dir=lesson_dir, repo_root=tmp_path, **_S3_ARGS,
            )
        assert result_html == html
        assert log == []
        mock_put.assert_not_called()
        mock_put_release.assert_not_called()

    def test_mixed_passes_run_in_order(self, tmp_path):
        """Cover all three passes in one HTML document."""
        lesson_dir, images_dir = self._setup_lesson(tmp_path)
        (images_dir / "rel.png").write_bytes(b"\x89PNG fake-rel")
        (images_dir / "abc-foo.png").write_bytes(b"\x89PNG fake-exp")
        html = (
            f'<p><img src="{_PNG_DATA_URI}"></p>'
            f'<p><img src="images/rel.png"></p>'
            f'<p><img src="{_EXPIRING_URL}"></p>'
            f'<p><img src="https://s3.us-east-1.amazonaws.com/Other/keep.png"></p>'
        )

        # All three passes call _s3_put — pass 1 in lesson_image_upload, pass 2
        # via skilljar_release, pass 3 in lesson_image_upload again.
        urls = iter([
            ("https://s3.us-east-1.amazonaws.com/test-bucket/data-uri.png", "k1"),
            ("https://s3.us-east-1.amazonaws.com/test-bucket/rel.png", "k2"),
            ("https://s3.us-east-1.amazonaws.com/test-bucket/abc-foo.png", "k3"),
        ])
        def fake_put(*a, **kw):
            return next(urls)

        with patch("pipeline.lesson_image_upload._s3_put", side_effect=fake_put), \
             patch("pipeline.skilljar_release._s3_put", side_effect=fake_put):
            result_html, log = upload_lesson_images(
                html, lesson_dir=lesson_dir, repo_root=tmp_path, **_S3_ARGS,
            )

        assert _PNG_DATA_URI not in result_html
        assert "images/rel.png" not in result_html
        assert _EXPIRING_URL not in result_html
        assert "https://s3.us-east-1.amazonaws.com/Other/keep.png" in result_html
        assert any(e.get("source") == "data_uri" for e in log)
        assert any(e.get("source") == "relative" for e in log)
        assert any(e.get("source") == "expiring_url" for e in log)

    def test_no_uploads_needed_returns_html_unchanged(self, tmp_path):
        lesson_dir, _ = self._setup_lesson(tmp_path)
        html = '<p>plain text and <img src="https://example.com/x.png"></p>'
        with patch("pipeline.lesson_image_upload._s3_put") as mock_put:
            result_html, log = upload_lesson_images(
                html, lesson_dir=lesson_dir, repo_root=tmp_path, **_S3_ARGS,
            )
        assert result_html == html
        assert log == []
        mock_put.assert_not_called()
