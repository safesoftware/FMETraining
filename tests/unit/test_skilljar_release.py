"""Unit tests for _inline_images in skilljar_release.py."""

from __future__ import annotations

import base64
from pathlib import Path

import pytest

from pipeline.skilljar_release import _inline_images


class TestInlineImages:
    def test_rewrites_relative_src_with_data_uri(self, tmp_path):
        (tmp_path / "images").mkdir()
        img_bytes = b"\x89PNG\r\n\x1a\n"
        (tmp_path / "images" / "photo.png").write_bytes(img_bytes)

        html = '<img src="images/photo.png" alt="test">'
        result_html, failed = _inline_images(
            html, ["images/photo.png"], tmp_path.name, tmp_path.parent,
        )

        expected_b64 = base64.b64encode(img_bytes).decode("ascii")
        assert f'src="data:image/png;base64,{expected_b64}"' in result_html
        assert failed == []

    def test_adds_to_failed_when_local_file_missing(self, tmp_path):
        html = '<img src="images/missing.gif">'
        result_html, failed = _inline_images(
            html, ["images/missing.gif"], "lesson/dir", tmp_path,
        )
        assert failed == ["images/missing.gif"]
        assert 'src="images/missing.gif"' in result_html  # unchanged

    def test_handles_multiple_images(self, tmp_path):
        (tmp_path / "images").mkdir()
        png_bytes = b"\x89PNG"
        gif_bytes = b"GIF89a"
        (tmp_path / "images" / "a.png").write_bytes(png_bytes)
        (tmp_path / "images" / "b.gif").write_bytes(gif_bytes)

        html = '<img src="images/a.png"><img src="images/b.gif">'
        result_html, failed = _inline_images(
            html, ["images/a.png", "images/b.gif"], "", tmp_path,
        )

        png_b64 = base64.b64encode(png_bytes).decode("ascii")
        gif_b64 = base64.b64encode(gif_bytes).decode("ascii")
        assert f'src="data:image/png;base64,{png_b64}"' in result_html
        assert f'src="data:image/gif;base64,{gif_b64}"' in result_html
        assert failed == []

    def test_unknown_mime_type_uses_octet_stream(self, tmp_path):
        (tmp_path / "images").mkdir()
        raw_bytes = b"\xde\xad\xbe\xef"
        (tmp_path / "images" / "file.unk123").write_bytes(raw_bytes)

        html = '<img src="images/file.unk123">'
        result_html, failed = _inline_images(
            html, ["images/file.unk123"], "", tmp_path,
        )

        b64 = base64.b64encode(raw_bytes).decode("ascii")
        assert f'src="data:application/octet-stream;base64,{b64}"' in result_html
        assert failed == []

    def test_leaves_html_unchanged_when_all_files_missing(self, tmp_path):
        html = '<img src="images/a.png"><img src="images/b.gif">'
        result_html, failed = _inline_images(
            html, ["images/a.png", "images/b.gif"], "", tmp_path,
        )
        assert result_html == html
        assert sorted(failed) == ["images/a.png", "images/b.gif"]
