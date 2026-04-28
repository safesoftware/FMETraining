"""Unit tests for _upload_and_rewrite_images in skilljar_release.py."""

from __future__ import annotations

from unittest.mock import patch

from pipeline.skilljar_release import _upload_and_rewrite_images

_S3_ARGS = dict(s3_bucket="test-bucket", s3_key_id="fake-id", s3_secret="fake-secret")
_S3_KEY = "skilljar-uploads/abc12345-photo.png"
_S3_PUBLIC_URL = "https://s3.us-east-1.amazonaws.com/test-bucket/" + _S3_KEY


class TestUploadAndRewriteImages:
    def test_rewrites_relative_src_with_public_s3_url(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "photo.png").write_bytes(b"\x89PNG")

        html = '<img src="images/photo.png" alt="test">'

        with patch("pipeline.skilljar_release._s3_put",
                   return_value=(_S3_PUBLIC_URL, _S3_KEY)):
            result_html, failed = _upload_and_rewrite_images(
                html, ["images/photo.png"], tmp_path.name, tmp_path.parent,
                "fake-api-key", **_S3_ARGS,
            )

        assert f'src="{_S3_PUBLIC_URL}"' in result_html
        assert failed == []

    def test_returns_unchanged_html_when_s3_not_configured(self, tmp_path):
        html = '<img src="images/photo.png">'
        result_html, failed = _upload_and_rewrite_images(
            html, ["images/photo.png"], "some/dir", tmp_path, "fake-api-key",
        )
        assert result_html == html
        paths = [p for p, _ in failed]
        assert "images/photo.png" in paths
        reasons = [r for _, r in failed]
        assert any("S3 not configured" in r for r in reasons)

    def test_adds_to_failed_when_local_file_missing(self, tmp_path):
        html = '<img src="images/missing.gif">'
        result_html, failed = _upload_and_rewrite_images(
            html, ["images/missing.gif"], "lesson/dir", tmp_path, "fake-key", **_S3_ARGS,
        )
        paths = [p for p, _ in failed]
        assert "images/missing.gif" in paths
        assert 'src="images/missing.gif"' in result_html  # unchanged

    def test_adds_to_failed_when_s3_put_raises(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "bad.gif").write_bytes(b"GIF89a")

        html = '<img src="images/bad.gif">'
        with patch("pipeline.skilljar_release._s3_put",
                   side_effect=RuntimeError("HTTP 403 PUT s3://test-bucket/...: Forbidden")):
            result_html, failed = _upload_and_rewrite_images(
                html, ["images/bad.gif"], "", tmp_path, "fake-key", **_S3_ARGS,
            )
        paths = [p for p, _ in failed]
        reasons = [r for _, r in failed]
        assert "images/bad.gif" in paths
        assert any("HTTP 403" in r for r in reasons)
        assert 'src="images/bad.gif"' in result_html

    def test_handles_multiple_images(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "a.png").write_bytes(b"\x89PNG")
        (tmp_path / "images" / "b.gif").write_bytes(b"GIF89a")

        html = '<img src="images/a.png"><img src="images/b.gif">'

        with patch("pipeline.skilljar_release._s3_put",
                   side_effect=[
                       ("https://s3.us-east-1.amazonaws.com/test-bucket/a.png", "skilljar-uploads/a.png"),
                       ("https://s3.us-east-1.amazonaws.com/test-bucket/b.gif", "skilljar-uploads/b.gif"),
                   ]):
            result_html, failed = _upload_and_rewrite_images(
                html, ["images/a.png", "images/b.gif"], "", tmp_path,
                "fake-key", **_S3_ARGS,
            )

        assert 'src="https://s3.us-east-1.amazonaws.com/test-bucket/a.png"' in result_html
        assert 'src="https://s3.us-east-1.amazonaws.com/test-bucket/b.gif"' in result_html
        assert failed == []

    def test_skilljar_asset_endpoint_not_called(self, tmp_path):
        """Regression: the previous flow used /v1/assets which returns 1-hour-signed URLs,
        breaking lessons after expiry. We must NOT call those helpers any more."""
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "x.png").write_bytes(b"\x89PNG")

        html = '<img src="images/x.png">'
        with patch("pipeline.skilljar_release._s3_put",
                   return_value=(_S3_PUBLIC_URL, _S3_KEY)) as mock_put:
            _upload_and_rewrite_images(
                html, ["images/x.png"], "", tmp_path, "fake-key", **_S3_ARGS,
            )
        # _create_asset_from_url and _wait_for_asset_url are no longer imported here,
        # so we just assert _s3_put was called and no S3 delete happened (the file
        # stays in the bucket as a permanent host).
        mock_put.assert_called_once()
