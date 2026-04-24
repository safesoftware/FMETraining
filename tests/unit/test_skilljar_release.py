"""Unit tests for _upload_and_rewrite_images in skilljar_release.py."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from pipeline.skilljar_release import _upload_and_rewrite_images

_S3_ARGS = dict(s3_bucket="test-bucket", s3_key_id="fake-id", s3_secret="fake-secret")
_S3_KEY = "skilljar-uploads/abc12345-photo.png"


class TestUploadAndRewriteImages:
    def test_rewrites_relative_src_with_hosted_url(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "photo.png").write_bytes(b"\x89PNG")

        html = '<img src="images/photo.png" alt="test">'

        with patch("pipeline.skilljar_release._s3_put",
                   return_value=("https://s3.example.com/photo.png", _S3_KEY)):
            with patch("pipeline.skilljar_release._create_asset_from_url", return_value="asset1"):
                with patch("pipeline.skilljar_release._wait_for_asset_url",
                           return_value="https://cdn.skilljar.com/photo.png"):
                    with patch("pipeline.skilljar_release._s3_delete"):
                        result_html, failed = _upload_and_rewrite_images(
                            html, ["images/photo.png"], tmp_path.name, tmp_path.parent,
                            "fake-api-key", **_S3_ARGS,
                        )

        assert 'src="https://cdn.skilljar.com/photo.png"' in result_html
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
            with patch("pipeline.skilljar_release._s3_delete"):
                result_html, failed = _upload_and_rewrite_images(
                    html, ["images/bad.gif"], "", tmp_path, "fake-key", **_S3_ARGS,
                )
        paths = [p for p, _ in failed]
        reasons = [r for _, r in failed]
        assert "images/bad.gif" in paths
        assert any("HTTP 403" in r for r in reasons)
        assert 'src="images/bad.gif"' in result_html

    def test_adds_to_failed_when_url_times_out(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "slow.png").write_bytes(b"\x89PNG")

        html = '<img src="images/slow.png">'
        with patch("pipeline.skilljar_release._s3_put",
                   return_value=("https://s3.example.com/slow.png", _S3_KEY)):
            with patch("pipeline.skilljar_release._create_asset_from_url", return_value="asset1"):
                with patch("pipeline.skilljar_release._wait_for_asset_url", return_value=None):
                    with patch("pipeline.skilljar_release._s3_delete"):
                        result_html, failed = _upload_and_rewrite_images(
                            html, ["images/slow.png"], "", tmp_path, "fake-key", **_S3_ARGS,
                        )
        paths = [p for p, _ in failed]
        reasons = [r for _, r in failed]
        assert "images/slow.png" in paths
        assert any("timed out" in r for r in reasons)

    def test_handles_multiple_images(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "a.png").write_bytes(b"\x89PNG")
        (tmp_path / "images" / "b.gif").write_bytes(b"GIF89a")

        html = '<img src="images/a.png"><img src="images/b.gif">'

        with patch("pipeline.skilljar_release._s3_put",
                   side_effect=[
                       ("https://s3.example.com/a.png", "skilljar-uploads/a.png"),
                       ("https://s3.example.com/b.gif", "skilljar-uploads/b.gif"),
                   ]):
            with patch("pipeline.skilljar_release._create_asset_from_url",
                       side_effect=["asset_a", "asset_b"]):
                with patch("pipeline.skilljar_release._wait_for_asset_url",
                           side_effect=["https://cdn.skilljar.com/a.png",
                                        "https://cdn.skilljar.com/b.gif"]):
                    with patch("pipeline.skilljar_release._s3_delete"):
                        result_html, failed = _upload_and_rewrite_images(
                            html, ["images/a.png", "images/b.gif"], "", tmp_path,
                            "fake-key", **_S3_ARGS,
                        )

        assert 'src="https://cdn.skilljar.com/a.png"' in result_html
        assert 'src="https://cdn.skilljar.com/b.gif"' in result_html
        assert failed == []

    def test_s3_cleanup_called_even_when_skilljar_fails(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "img.png").write_bytes(b"\x89PNG")

        html = '<img src="images/img.png">'
        with patch("pipeline.skilljar_release._s3_put",
                   return_value=("https://s3.example.com/img.png", _S3_KEY)) as mock_put:
            with patch("pipeline.skilljar_release._create_asset_from_url",
                       side_effect=RuntimeError("Skilljar error")):
                with patch("pipeline.skilljar_release._s3_delete") as mock_delete:
                    _upload_and_rewrite_images(
                        html, ["images/img.png"], "", tmp_path, "fake-key", **_S3_ARGS,
                    )

        mock_put.assert_called_once()
        mock_delete.assert_called_once_with(_S3_KEY, "test-bucket", "fake-id", "fake-secret", "us-east-1")
