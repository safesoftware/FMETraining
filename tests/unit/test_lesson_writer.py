"""Unit tests for app.services.lesson_writer.

Covers the three ported helpers:
  * compute_target_path — version/course remapping + shallow-path guard
  * sanitize_lesson_html — track-changes chrome stripping
  * write_lesson — disk write under content_root, image copy, exists/force

The image-upload helper is stubbed so no S3 / network is touched.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services import lesson_writer
from app.services.lesson_writer import (
    compute_target_path,
    sanitize_lesson_html,
    write_lesson,
)


# ---- compute_target_path -------------------------------------------------

def test_compute_target_path_maps_version_and_course_suffix() -> None:
    result = compute_target_path(
        "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson", "2026.1"
    )
    assert result == Path(
        "2026.1/fme-form-basic/Connect To Data 2026.1/My Lesson"
    )


def test_compute_target_path_keeps_nested_lesson_folder() -> None:
    # >4 parts: the lesson "folder" is everything past the course.
    result = compute_target_path(
        "2025.0/lp/Course 2025.0/Section/Lesson", "2026.1"
    )
    assert result == Path("2026.1/lp/Course 2026.1/Section/Lesson")


def test_compute_target_path_course_without_version_suffix() -> None:
    # No trailing " 2025.0" on the course folder → canonical name unchanged.
    result = compute_target_path("2025.0/lp/Plain Course/Lesson", "2026.1")
    assert result == Path("2026.1/lp/Plain Course 2026.1/Lesson")


@pytest.mark.parametrize(
    "shallow",
    ["", "2025.0", "2025.0/lp", "2025.0/lp/course"],
)
def test_compute_target_path_too_shallow_raises(shallow: str) -> None:
    with pytest.raises(ValueError, match="too shallow"):
        compute_target_path(shallow, "2026.1")


# ---- sanitize_lesson_html ------------------------------------------------

def test_sanitize_strips_tc_chrome_keeps_content() -> None:
    html = (
        '<p>Real content here.</p>'
        '<div class="tc-popup"><button class="tc-accept">Accept</button>'
        '<span class="tc-explanation">why</span></div>'
        '<a class="card-link" href="#">card</a>'
    )
    out = sanitize_lesson_html(html)
    assert "Real content here." in out
    assert "tc-popup" not in out
    assert "tc-accept" not in out
    assert "tc-explanation" not in out
    assert "card-link" not in out


def test_sanitize_strips_tab_links_and_jira_colour_links() -> None:
    html = (
        '<p>before <a href="?tab=changes">jump</a> after</p>'
        '<a href="https://jira/KNOW-1" style="color:#93c5fd">KNOW-1</a>'
        '<a href="https://example.com">keep me</a>'
    )
    out = sanitize_lesson_html(html)
    assert "?tab=changes" not in out
    assert "color:#93c5fd" not in out
    assert "KNOW-1" not in out
    # A normal link must survive.
    assert 'href="https://example.com"' in out
    assert "keep me" in out


def test_sanitize_removes_empty_paragraphs_but_keeps_br_spacers() -> None:
    html = "<p>text</p><p></p><p><br/></p><p>  </p>"
    out = sanitize_lesson_html(html)
    assert "<p>text</p>" in out
    # The intentional <p><br/></p> spacer survives.
    assert "<br" in out
    # No truly-empty paragraphs remain.
    assert "<p></p>" not in out


# ---- write_lesson --------------------------------------------------------

@pytest.fixture
def no_s3(monkeypatch):
    """Stub the image upload so write_lesson never touches S3/network.

    Returns the html unchanged (the default no-upload path), but also guards
    against accidental real calls.
    """
    calls = {"n": 0}

    def _stub(html, lesson_dir, **kwargs):
        calls["n"] += 1
        return html

    monkeypatch.setattr(lesson_writer, "_upload_lesson_images", _stub)
    return calls


def _write(tree, *, force=False, html="<p>edited body</p>"):
    return write_lesson(
        f"{tree['version']}/{tree['lp']}/{tree['course_folder']}/{tree['lessons'][0]}",
        "2026.1",
        html,
        force=force,
        content_root=tree["repo_root"],
        s3_bucket="b",
        s3_key_id="k",
        s3_secret="s",
        s3_region="us-west-2",
    )


def test_write_lesson_writes_file_under_content_root(tmp_version_tree, no_s3) -> None:
    rel = _write(tmp_version_tree)
    assert rel == (
        f"2026.1/{tmp_version_tree['lp']}/"
        f"{tmp_version_tree['course_canonical']} 2026.1/"
        f"{tmp_version_tree['lessons'][0]}/index.html"
    )
    written = tmp_version_tree["repo_root"] / rel
    assert written.read_text(encoding="utf-8").find("edited body") != -1


def test_write_lesson_copies_source_images(tmp_version_tree, no_s3) -> None:
    # Seed an image in the source lesson's images/ dir.
    src_images = (
        tmp_version_tree["repo_root"]
        / tmp_version_tree["version"]
        / tmp_version_tree["lp"]
        / tmp_version_tree["course_folder"]
        / tmp_version_tree["lessons"][0]
        / "images"
    )
    (src_images / "diagram.png").write_bytes(b"\x89PNG fake")

    rel = _write(tmp_version_tree)
    target_image = (
        (tmp_version_tree["repo_root"] / rel).parent / "images" / "diagram.png"
    )
    assert target_image.read_bytes() == b"\x89PNG fake"


def test_write_lesson_copies_images_without_metadata(
    tmp_version_tree, no_s3, monkeypatch
) -> None:
    """Regression (found in QA): the image copy must NOT preserve metadata.

    ``shutil.copytree``'s default ``copy2`` calls ``copystat`` (timestamps /
    permissions / xattrs), which raises EPERM ("Operation not permitted") on
    bind-mounted, non-owner filesystems — Docker volumes, WSL2 mounts, and the
    prod ``/content`` mount all hit it. Force ``copystat`` to fail the way those
    mounts do; ``write_lesson`` must still succeed and copy the image bytes
    (it uses ``shutil.copyfile``, which never calls ``copystat``).
    """
    import shutil

    src_images = (
        tmp_version_tree["repo_root"]
        / tmp_version_tree["version"]
        / tmp_version_tree["lp"]
        / tmp_version_tree["course_folder"]
        / tmp_version_tree["lessons"][0]
        / "images"
    )
    (src_images / "diagram.png").write_bytes(b"\x89PNG fake")

    def _eperm(*_a, **_k):
        raise PermissionError(1, "Operation not permitted")

    # The old shutil.copytree(copy2) path would hit this and fail; copyfile
    # never calls copystat, so the save must still succeed.
    monkeypatch.setattr(shutil, "copystat", _eperm)

    rel = _write(tmp_version_tree)  # must NOT raise
    target_image = (
        (tmp_version_tree["repo_root"] / rel).parent / "images" / "diagram.png"
    )
    assert target_image.read_bytes() == b"\x89PNG fake"


def test_write_lesson_raises_when_exists_without_force(tmp_version_tree, no_s3) -> None:
    _write(tmp_version_tree)  # first write
    with pytest.raises(FileExistsError) as excinfo:
        _write(tmp_version_tree)  # second write, no force
    # The relative target path is stashed on the exception for the route to echo.
    assert excinfo.value.filename.endswith("/index.html")
    assert "2026.1" in excinfo.value.filename


def test_write_lesson_overwrites_with_force(tmp_version_tree, no_s3) -> None:
    rel = _write(tmp_version_tree, html="<p>first</p>")
    written = tmp_version_tree["repo_root"] / rel
    assert "first" in written.read_text(encoding="utf-8")

    rel2 = _write(tmp_version_tree, force=True, html="<p>second</p>")
    assert rel2 == rel
    assert "second" in written.read_text(encoding="utf-8")
    assert "first" not in written.read_text(encoding="utf-8")


def test_write_lesson_shallow_dir_raises_value_error(tmp_version_tree, no_s3) -> None:
    with pytest.raises(ValueError, match="too shallow"):
        write_lesson(
            "2025.0/lp/course",  # only 3 parts
            "2026.1",
            "<p>x</p>",
            force=False,
            content_root=tmp_version_tree["repo_root"],
            s3_bucket="b",
            s3_key_id="k",
            s3_secret="s",
            s3_region="us-west-2",
        )
