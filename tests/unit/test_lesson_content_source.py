"""Tests for the LessonContentSource abstraction + LocalFolderSource impl."""
from __future__ import annotations

from pathlib import Path

import pytest

from app.services.lesson_content_source import (
    LessonContentSource,
    LessonRef,
    LocalFolderSource,
    SkilljarContentSource,
)


# ---- LessonRef ------------------------------------------------------------

def test_lesson_ref_is_hashable_and_frozen() -> None:
    """Frozen dataclasses can be used as dict keys / set members."""
    ref = LessonRef(source_id="local:x", title="x")
    {ref}  # set membership — would raise if unhashable
    with pytest.raises(Exception):  # FrozenInstanceError
        ref.title = "different"  # type: ignore[misc]


# ---- LocalFolderSource ----------------------------------------------------

@pytest.mark.asyncio
async def test_list_lessons_walks_version_layout(tmp_path: Path) -> None:
    # Build: 2025.0/lp1/Course A 2025.0/Lesson 1/index.html
    lesson_dir = tmp_path / "2025.0" / "lp1" / "Course A 2025.0" / "Lesson 1"
    lesson_dir.mkdir(parents=True)
    (lesson_dir / "index.html").write_text("<p>hi</p>", encoding="utf-8")

    source = LocalFolderSource(tmp_path)
    refs = await source.list_lessons()

    assert len(refs) == 1
    ref = refs[0]
    assert ref.title == "Lesson 1"
    assert ref.course_title == "Course A"  # version suffix stripped
    assert ref.learning_path_title == "lp1"
    assert ref.version == "2025.0"
    assert ref.source_id == "local:2025.0/lp1/Course A 2025.0/Lesson 1"


@pytest.mark.asyncio
async def test_list_lessons_filters_by_version(tmp_path: Path) -> None:
    for v in ("2024.2", "2025.0", "2026.1"):
        ld = tmp_path / v / "lp" / f"C {v}" / "L"
        ld.mkdir(parents=True)
        (ld / "index.html").write_text("x", encoding="utf-8")

    refs = await LocalFolderSource(tmp_path).list_lessons(version="2025.0")
    versions = {r.version for r in refs}
    assert versions == {"2025.0"}


@pytest.mark.asyncio
async def test_list_lessons_skips_non_version_dirs(tmp_path: Path) -> None:
    """Sibling dirs that aren't version-shaped (data/, scripts/, .git/, etc.)
    must not be walked."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "junk.txt").write_text("not a lesson", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("[core]", encoding="utf-8")

    valid = tmp_path / "2025.0" / "lp" / "Course 2025.0" / "L"
    valid.mkdir(parents=True)
    (valid / "index.html").write_text("real lesson", encoding="utf-8")

    refs = await LocalFolderSource(tmp_path).list_lessons()
    assert len(refs) == 1


@pytest.mark.asyncio
async def test_get_html_round_trip(tmp_path: Path) -> None:
    lesson_dir = tmp_path / "2025.0" / "lp" / "Course 2025.0" / "L"
    lesson_dir.mkdir(parents=True)
    (lesson_dir / "index.html").write_text("<p>contents</p>", encoding="utf-8")

    source = LocalFolderSource(tmp_path)
    refs = await source.list_lessons()
    html = await source.get_html(refs[0].source_id)
    assert html == "<p>contents</p>"


@pytest.mark.asyncio
async def test_get_html_rejects_unknown_source_id(tmp_path: Path) -> None:
    source = LocalFolderSource(tmp_path)
    with pytest.raises(LookupError):
        await source.get_html("skilljar:abc123")


@pytest.mark.asyncio
async def test_get_html_rejects_path_traversal(tmp_path: Path) -> None:
    """A crafted source_id with ``..`` must not escape the repo root."""
    (tmp_path / "secret.txt").write_text("not for you", encoding="utf-8")
    source = LocalFolderSource(tmp_path)
    with pytest.raises(LookupError):
        await source.get_html("local:../secret.txt")
    # Going up and back into a sibling.
    with pytest.raises(LookupError):
        await source.get_html("local:../../etc/passwd")


@pytest.mark.asyncio
async def test_get_html_missing_file_raises_lookup_error(tmp_path: Path) -> None:
    source = LocalFolderSource(tmp_path)
    with pytest.raises(LookupError):
        await source.get_html("local:nope/nada/nothing")


# ---- SkilljarContentSource ------------------------------------------------

@pytest.mark.asyncio
async def test_skilljar_content_source_raises_until_implemented() -> None:
    """Selecting SkilljarContentSource accidentally must fail loudly,
    not silently return empty data."""
    src = SkilljarContentSource()
    with pytest.raises(NotImplementedError):
        await src.list_lessons()
    with pytest.raises(NotImplementedError):
        await src.get_html("skilljar:abc")


# ---- ABC sanity -----------------------------------------------------------

def test_concrete_sources_inherit_the_abc() -> None:
    assert issubclass(LocalFolderSource, LessonContentSource)
    assert issubclass(SkilljarContentSource, LessonContentSource)
