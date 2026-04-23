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

        with patch("pipeline.skilljar_release._upload_asset", return_value="asset1"):
            with patch("pipeline.skilljar_release._wait_for_asset_url",
                       return_value="https://cdn.skilljar.com/photo.png"):
                result_html, failed = _upload_and_rewrite_images(
                    html, ["images/photo.png"], tmp_path.name, tmp_path.parent, "fake-key",
                )

        assert 'src="https://cdn.skilljar.com/photo.png"' in result_html
        assert failed == []

    def test_adds_to_failed_when_local_file_missing(self, tmp_path):
        html = '<img src="images/missing.gif">'
        result_html, failed = _upload_and_rewrite_images(
            html, ["images/missing.gif"], "lesson/dir", tmp_path, "fake-key",
        )
        paths = [p for p, _ in failed]
        assert "images/missing.gif" in paths
        assert 'src="images/missing.gif"' in result_html  # unchanged

    def test_adds_to_failed_with_reason_when_upload_raises(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "bad.gif").write_bytes(b"GIF89a")

        html = '<img src="images/bad.gif">'
        with patch("pipeline.skilljar_release._upload_asset",
                   side_effect=RuntimeError("HTTP 400 POST /assets: bad request")):
            result_html, failed = _upload_and_rewrite_images(
                html, ["images/bad.gif"], "", tmp_path, "fake-key",
            )
        paths = [p for p, _ in failed]
        reasons = [r for _, r in failed]
        assert "images/bad.gif" in paths
        assert any("HTTP 400" in r for r in reasons)
        assert 'src="images/bad.gif"' in result_html

    def test_adds_to_failed_when_url_times_out(self, tmp_path):
        (tmp_path / "images").mkdir()
        (tmp_path / "images" / "slow.png").write_bytes(b"\x89PNG")

        html = '<img src="images/slow.png">'
        with patch("pipeline.skilljar_release._upload_asset", return_value="asset1"):
            with patch("pipeline.skilljar_release._wait_for_asset_url", return_value=None):
                result_html, failed = _upload_and_rewrite_images(
                    html, ["images/slow.png"], "", tmp_path, "fake-key",
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

        with patch("pipeline.skilljar_release._upload_asset",
                   side_effect=["asset_a", "asset_b"]):
            with patch("pipeline.skilljar_release._wait_for_asset_url",
                       side_effect=["https://cdn.skilljar.com/a.png",
                                    "https://cdn.skilljar.com/b.gif"]):
                result_html, failed = _upload_and_rewrite_images(
                    html, ["images/a.png", "images/b.gif"], "", tmp_path, "fake-key",
                )

        assert 'src="https://cdn.skilljar.com/a.png"' in result_html
        assert 'src="https://cdn.skilljar.com/b.gif"' in result_html
        assert failed == []
