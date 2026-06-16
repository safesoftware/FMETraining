"""Unit tests for app.services.lesson_writer.

Covers the ported helpers:
  * compute_target_path — version/course remapping + shallow-path guard
  * saved_lesson_index_path — path math rooted at the WRITABLE saved store
  * sanitize_lesson_html — track-changes chrome stripping
  * write_lesson — writes a self-contained index.html under saved_versions_root
    (NOT content_root), reading SOURCE images via the content resolver and
    rehosting them to permanent URLs.

The image-upload helper is stubbed so no S3 / network is touched.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services import lesson_writer
from app.services.lesson_writer import (
    compute_target_path,
    sanitize_lesson_html,
    saved_lesson_index_path,
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


# ---- saved_lesson_index_path ---------------------------------------------

def test_saved_lesson_index_path_joins_root_and_target() -> None:
    root = Path("/var/lib/fme-train/drafts")
    result = saved_lesson_index_path(
        root, "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson", "2026.1"
    )
    assert result == (
        root
        / "2026.1"
        / "fme-form-basic"
        / "Connect To Data 2026.1"
        / "My Lesson"
        / "index.html"
    )


def test_saved_lesson_index_path_is_under_saved_root_not_content_root() -> None:
    # Path math must root at the passed (writable) store, never anywhere else.
    saved = Path("/writable/saved")
    result = saved_lesson_index_path(saved, "2025.0/lp/Course/Lesson", "2026.1")
    assert str(result).startswith(str(saved))
    assert result.name == "index.html"


def test_saved_lesson_index_path_shallow_dir_raises() -> None:
    with pytest.raises(ValueError, match="too shallow"):
        saved_lesson_index_path(Path("/saved"), "2025.0/lp/course", "2026.1")


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


def _write(tree, saved_root, *, force=False, html="<p>edited body</p>"):
    return write_lesson(
        f"{tree['version']}/{tree['lp']}/{tree['course_folder']}/{tree['lessons'][0]}",
        "2026.1",
        html,
        force=force,
        saved_versions_root=saved_root,
        s3_bucket="b",
        s3_key_id="k",
        s3_secret="s",
        s3_region="us-west-2",
    )


def test_write_lesson_writes_file_under_saved_root_not_content_root(
    tmp_version_tree, tmp_path, no_s3
) -> None:
    saved_root = tmp_path / "saved"
    rel = _write(tmp_version_tree, saved_root)
    assert rel == (
        f"2026.1/{tmp_version_tree['lp']}/"
        f"{tmp_version_tree['course_canonical']} 2026.1/"
        f"{tmp_version_tree['lessons'][0]}/index.html"
    )
    # Written under the WRITABLE saved store...
    written = saved_root / rel
    assert "edited body" in written.read_text(encoding="utf-8")
    # ...and NOTHING under the content root (the source tree's repo_root).
    assert not (tmp_version_tree["repo_root"] / rel).exists()


def test_write_lesson_does_not_copy_source_images_dir(
    tmp_version_tree, tmp_path, no_s3
) -> None:
    """The saved index.html is self-contained (permanent URLs); there is no
    relative images/ dir copied alongside it."""
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

    saved_root = tmp_path / "saved"
    rel = _write(tmp_version_tree, saved_root)
    target_images = (saved_root / rel).parent / "images"
    assert not target_images.exists()


def test_write_lesson_rehosts_images_to_permanent_urls(
    tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """write_lesson hands the html to upload_lesson_images, whose rewritten
    output (permanent URLs, no relative images/) is what lands on disk."""
    def _rehost(html, lesson_dir, **kwargs):
        return html.replace(
            'src="images/diagram.png"',
            'src="https://s3.us-west-2.amazonaws.com/bucket/skilljar-uploads/abc-diagram.png"',
        )

    monkeypatch.setattr(lesson_writer, "_upload_lesson_images", _rehost)

    saved_root = tmp_path / "saved"
    rel = _write(
        tmp_version_tree, saved_root,
        html='<p><img src="images/diagram.png"></p>',
    )
    saved = (saved_root / rel).read_text(encoding="utf-8")
    assert 'src="images/diagram.png"' not in saved
    assert "amazonaws.com/bucket/skilljar-uploads/abc-diagram.png" in saved


def test_write_lesson_raises_when_exists_without_force(
    tmp_version_tree, tmp_path, no_s3
) -> None:
    saved_root = tmp_path / "saved"
    _write(tmp_version_tree, saved_root)  # first write
    with pytest.raises(FileExistsError) as excinfo:
        _write(tmp_version_tree, saved_root)  # second write, no force
    # The relative target path is stashed on the exception for the route to echo.
    assert excinfo.value.filename.endswith("/index.html")
    assert "2026.1" in excinfo.value.filename


def test_write_lesson_overwrites_with_force(tmp_version_tree, tmp_path, no_s3) -> None:
    saved_root = tmp_path / "saved"
    rel = _write(tmp_version_tree, saved_root, html="<p>first</p>")
    written = saved_root / rel
    assert "first" in written.read_text(encoding="utf-8")

    rel2 = _write(tmp_version_tree, saved_root, force=True, html="<p>second</p>")
    assert rel2 == rel
    assert "second" in written.read_text(encoding="utf-8")
    assert "first" not in written.read_text(encoding="utf-8")


def test_write_lesson_shallow_dir_raises_value_error(
    tmp_version_tree, tmp_path, no_s3
) -> None:
    with pytest.raises(ValueError, match="too shallow"):
        write_lesson(
            "2025.0/lp/course",  # only 3 parts
            "2026.1",
            "<p>x</p>",
            force=False,
            saved_versions_root=tmp_path / "saved",
            s3_bucket="b",
            s3_key_id="k",
            s3_secret="s",
            s3_region="us-west-2",
        )


# ---- write_lesson, hermetic CONTENT_SOURCE=s3mirror ----------------------

class _StubContentSource:
    """In-memory ContentSource stub: canned HTML + image bytes, no network."""

    def __init__(self, images: dict[str, bytes]) -> None:
        self._images = images

    def get_lesson_html(self, lesson_dir):  # pragma: no cover - unused here
        return "<p>source html</p>"

    def lesson_html_exists(self, lesson_dir):  # pragma: no cover
        return True

    def list_lesson_images(self, lesson_dir):
        return sorted(self._images)

    def read_image_bytes(self, lesson_dir, filename):
        from pipeline.content_source import LessonContentNotFound

        filename = filename[len("images/"):] if filename.startswith("images/") else filename
        try:
            return self._images[filename]
        except KeyError:
            raise LessonContentNotFound(f"{lesson_dir}/images/{filename}: missing")

    def image_exists(self, lesson_dir, filename):
        filename = filename[len("images/"):] if filename.startswith("images/") else filename
        return filename in self._images

    def list_versions(self):  # pragma: no cover
        return ["2026.1"]

    def discover_lessons(self, version, learning_path=None):  # pragma: no cover
        return []

    def list_learning_paths(self, version):  # pragma: no cover
        return []

    def list_courses(self, version, learning_path):  # pragma: no cover
        return []


def test_write_lesson_s3mirror_rehosts_and_writes_under_saved_root(
    tmp_path, monkeypatch
) -> None:
    """Hermetic s3mirror path: source images come from a stubbed content
    source, _s3_put is mocked. The saved index.html lands under a tmp
    saved_versions_root with rehosted S3 URLs (no relative images/), and
    NOTHING is written under the content root."""
    from pipeline import content_source as cs
    from pipeline import lesson_image_upload

    stub = _StubContentSource({"diagram.png": b"\x89PNG mirror-bytes"})
    monkeypatch.setattr(cs, "get_content_source", lambda: stub)
    # lesson_image_upload imported get_content_source by name at module load.
    monkeypatch.setattr(lesson_image_upload, "get_content_source", lambda: stub)

    captured = {}

    def fake_s3_put(file_path, bucket, key_id, secret, region):
        captured["name"] = Path(file_path).name
        captured["bytes"] = Path(file_path).read_bytes()
        url = f"https://s3.{region}.amazonaws.com/{bucket}/skilljar-uploads/abc-{Path(file_path).name}"
        return url, f"skilljar-uploads/abc-{Path(file_path).name}"

    monkeypatch.setattr(lesson_image_upload, "_s3_put", fake_s3_put)

    saved_root = tmp_path / "saved"
    content_root = tmp_path / "content"  # deliberately empty / unused

    lesson_dir = "2025.0/fme-form-basic/Connect To Data 2025.0/My Lesson"
    rel = write_lesson(
        lesson_dir,
        "2026.1",
        '<p>edited <img src="images/diagram.png"></p>',
        force=False,
        saved_versions_root=saved_root,
        s3_bucket="bucket",
        s3_key_id="k",
        s3_secret="s",
        s3_region="us-west-2",
    )

    # Image bytes came from the stubbed mirror source.
    assert captured["bytes"] == b"\x89PNG mirror-bytes"
    assert captured["name"] == "diagram.png"

    written = saved_root / rel
    saved = written.read_text(encoding="utf-8")
    # Rehosted permanent URL, no relative images/ reference left.
    assert "s3.us-west-2.amazonaws.com/bucket/skilljar-uploads/abc-diagram.png" in saved
    assert 'src="images/diagram.png"' not in saved
    # No relative images/ dir alongside the saved index.html.
    assert not (written.parent / "images").exists()
    # NOTHING written under the content root.
    assert not content_root.exists() or not any(content_root.rglob("*"))
