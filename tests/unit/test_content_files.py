"""Resolver mapping a relative lesson-content path to a local file (KNOW-2347).

Backs ``GET /lesson-content/{rel_path}`` so the deployed app can serve the
lesson images the report references, instead of relying on a relative
``../{lesson_dir}/...`` URL that only resolved under the old "serve from
project root" model and 404'd after the EC2 cutover.

The resolver must refuse to escape the content root (``..`` segments, absolute
paths, symlinks) — it serves a public, unauthenticated route.
"""
from __future__ import annotations

import pytest

from app.services.content_files import read_content_bytes, resolve_content_path
from pipeline.content_source import LocalFolderSource


def _write(root, rel, data=b"PNGBYTES"):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(data)
    return p


def test_resolves_existing_file(tmp_path):
    rel = "2025.1/lp/Course 2025.1/Lesson A/images/foo.png"
    _write(tmp_path, rel, b"REALPNG")
    resolved = resolve_content_path(rel, content_root=tmp_path)
    assert resolved == (tmp_path / rel).resolve()
    assert resolved.read_bytes() == b"REALPNG"


def test_resolves_path_with_spaces(tmp_path):
    # Spaces in lesson/course names have historically broken image paths (ISSUES #61).
    rel = (
        "2025.1/fme-form-advanced/Improve Data Quality 2025.1/"
        "Exercise_ Handle Nulls/images/1724357278124.png"
    )
    _write(tmp_path, rel, b"X")
    assert resolve_content_path(rel, content_root=tmp_path).read_bytes() == b"X"


def test_missing_file_raises_lookup_error(tmp_path):
    with pytest.raises(LookupError):
        resolve_content_path("2025.1/nope/images/missing.png", content_root=tmp_path)


def test_parent_traversal_is_rejected(tmp_path):
    content_root = tmp_path / "content"
    content_root.mkdir()
    (tmp_path / "secret.txt").write_text("top secret")
    with pytest.raises(LookupError):
        resolve_content_path("../secret.txt", content_root=content_root)


def test_absolute_path_is_rejected(tmp_path):
    # Path("/root") / "/etc/passwd" == Path("/etc/passwd") — must not escape.
    with pytest.raises(LookupError):
        resolve_content_path("/etc/passwd", content_root=tmp_path)


# ---------------------------------------------------------------------------
# read_content_bytes — backend-agnostic served-bytes entry point (KNOW-2360).
# Exercised here over a LocalFolderSource on a tmp tree; the same code path
# serves the S3-mirror backend (no local file) unchanged.
# ---------------------------------------------------------------------------

LESSON = "2025.1/fme-form-advanced/Improve Data Quality 2025.1/Exercise_ Handle Nulls"


def _source(tmp_path):
    return LocalFolderSource(tmp_path)


def test_read_content_bytes_serves_image(tmp_path):
    _write(tmp_path, f"{LESSON}/images/1724357278124.png", b"\x89PNGREAL")
    data, media_type = read_content_bytes(
        f"{LESSON}/images/1724357278124.png", source=_source(tmp_path)
    )
    assert data == b"\x89PNGREAL"
    assert media_type == "image/png"


def test_read_content_bytes_serves_image_with_spaces(tmp_path):
    _write(tmp_path, "2025.1/lp/Course 2025.1/Lesson A/images/foo.jpg", b"JPG")
    data, media_type = read_content_bytes(
        "2025.1/lp/Course 2025.1/Lesson A/images/foo.jpg", source=_source(tmp_path)
    )
    assert data == b"JPG"
    assert media_type == "image/jpeg"


def test_read_content_bytes_serves_lesson_html(tmp_path):
    _write(tmp_path, f"{LESSON}/index.html", b"<html>hi</html>")
    data, media_type = read_content_bytes(
        f"{LESSON}/index.html", source=_source(tmp_path)
    )
    assert data == b"<html>hi</html>"
    assert media_type == "text/html; charset=utf-8"


def test_read_content_bytes_missing_image_raises(tmp_path):
    with pytest.raises(LookupError):
        read_content_bytes(f"{LESSON}/images/missing.png", source=_source(tmp_path))


def test_read_content_bytes_rejects_traversal(tmp_path):
    (tmp_path.parent / "secret.txt").write_text("top secret")
    with pytest.raises(LookupError):
        read_content_bytes("../secret.txt/images/x.png", source=_source(tmp_path))


def test_read_content_bytes_rejects_absolute(tmp_path):
    with pytest.raises(LookupError):
        read_content_bytes("/etc/passwd/images/x", source=_source(tmp_path))


def test_read_content_bytes_rejects_non_lesson_path(tmp_path):
    # Only images + index.html are served; an arbitrary file 404s even if present.
    _write(tmp_path, "2025.1/lp/c/l/notes.txt", b"NOPE")
    with pytest.raises(LookupError):
        read_content_bytes("2025.1/lp/c/l/notes.txt", source=_source(tmp_path))
