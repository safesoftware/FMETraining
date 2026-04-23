"""Unit tests for _upload_and_rewrite_images in skilljar_release.py."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

import pytest

from pipeline.skilljar_release import _upload_and_rewrite_images


class TestUploadAndRewriteImages:
    def test_rewrites_relative_src_with_hosted_url(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "photo.png").write_bytes(b"\x89PNG")

        html = '<img src="images/photo.png" alt="test">'

        with patch("pipeline.skilljar_release._create_skilljar_upload_url",
                   return_value=("https://s3.example.com/signed?sig=x", "https://cdn.example.com/photo.png")):
            with patch("pipeline.skilljar_release._put_image_to_s3"):
                result_html, failed = _upload_and_rewrite_images(
                    html, ["images/photo.png"], tmp_path.name, tmp_path.parent, "fake-key",
                )

        assert 'src="https://cdn.example.com/photo.png"' in result_html
        assert failed == []

    def test_adds_to_failed_when_local_file_missing(self, tmp_path):
        html = '<img src="images/missing.gif">'
        result_html, failed = _upload_and_rewrite_images(
            html, ["images/missing.gif"], "lesson/dir", tmp_path, "fake-key",
        )
        paths = [p for p, _ in failed]
        assert "images/missing.gif" in paths
        assert 'src="images/missing.gif"' in result_html  # unchanged

    def test_adds_to_failed_when_upload_raises(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "bad.gif").write_bytes(b"GIF89a")

        html = '<img src="images/bad.gif">'
        with patch("pipeline.skilljar_release._create_skilljar_upload_url",
                   side_effect=RuntimeError("HTTP 403 GET /asset/create_upload_url: Forbidden")):
            result_html, failed = _upload_and_rewrite_images(
                html, ["images/bad.gif"], "", tmp_path, "fake-key",
            )
        paths = [p for p, _ in failed]
        reasons = [r for _, r in failed]
        assert "images/bad.gif" in paths
        assert any("HTTP 403" in r for r in reasons)
        assert 'src="images/bad.gif"' in result_html

    def test_adds_to_failed_when_s3_put_raises(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "slow.png").write_bytes(b"\x89PNG")

        html = '<img src="images/slow.png">'
        with patch("pipeline.skilljar_release._create_skilljar_upload_url",
                   return_value=("https://s3.example.com/signed", "https://cdn.example.com/slow.png")):
            with patch("pipeline.skilljar_release._put_image_to_s3",
                       side_effect=RuntimeError("HTTP 403 PUT to S3: SignatureMismatch")):
                result_html, failed = _upload_and_rewrite_images(
                    html, ["images/slow.png"], "", tmp_path, "fake-key",
                )
        paths = [p for p, _ in failed]
        assert "images/slow.png" in paths

    def test_handles_multiple_images(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "a.png").write_bytes(b"\x89PNG")
        (tmp_path / "images" / "b.gif").write_bytes(b"GIF89a")

        html = '<img src="images/a.png"><img src="images/b.gif">'

        upload_url_calls = iter([
            ("https://s3.example.com/a?sig=1", "https://cdn.example.com/a.png"),
            ("https://s3.example.com/b?sig=2", "https://cdn.example.com/b.gif"),
        ])

        with patch("pipeline.skilljar_release._create_skilljar_upload_url",
                   side_effect=upload_url_calls):
            with patch("pipeline.skilljar_release._put_image_to_s3"):
                result_html, failed = _upload_and_rewrite_images(
                    html, ["images/a.png", "images/b.gif"], "", tmp_path, "fake-key",
                )

        assert 'src="https://cdn.example.com/a.png"' in result_html
        assert 'src="https://cdn.example.com/b.gif"' in result_html
        assert failed == []
