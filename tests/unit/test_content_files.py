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

from app.services.content_files import resolve_content_path


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
