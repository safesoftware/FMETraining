"""Shared pytest fixtures for the FME Training Automation test suite."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.models import Base

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SAMPLE_LESSON_HTML = FIXTURES_DIR / "sample_lesson.html"


@pytest.fixture
def sample_lesson_path() -> Path:
    """Return the path to the fixture lesson HTML."""
    return SAMPLE_LESSON_HTML


@pytest.fixture
def sample_lesson_content() -> str:
    """Return the content of the fixture lesson HTML."""
    return SAMPLE_LESSON_HTML.read_text(encoding="utf-8")


@pytest.fixture
def tmp_version_tree(tmp_path: Path) -> dict:
    """
    Create a minimal versioned lesson tree under tmp_path.

    Returns a dict with useful paths and expected values for assertions.

    Tree layout:
      tmp_path/
        2024.2/
          fme-form-basic/
            Connect To Data 2024.2/
              Exercise_ Connect to a Database/
                index.html
                images/
                  workbench_overview.png
              Read and Display Data/
                index.html
    """
    version = "2024.2"
    lp = "fme-form-basic"
    course_folder = "Connect To Data 2024.2"
    course_canonical = "Connect To Data"

    lesson1 = "Exercise_ Connect to a Database"
    lesson2 = "Read and Display Data"

    for lesson in (lesson1, lesson2):
        lesson_dir = tmp_path / version / lp / course_folder / lesson
        lesson_dir.mkdir(parents=True)
        # Copy the sample lesson HTML
        shutil.copy(SAMPLE_LESSON_HTML, lesson_dir / "index.html")
        # Create a dummy image dir
        (lesson_dir / "images").mkdir()

    return {
        "repo_root": tmp_path,
        "version": version,
        "lp": lp,
        "course_folder": course_folder,
        "course_canonical": course_canonical,
        "lessons": [lesson1, lesson2],
        "lesson1_path": f"{version}/{lp}/{course_folder}/{lesson1}/index.html",
    }


# ---- DB fixtures (KNOW-2269 / KNOW-2270 onward) ---------------------------

@pytest.fixture
async def async_session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
    """Per-test SQLite-backed async session factory with the schema applied.

    Each test gets its own engine, so writes from one test never leak into
    another. The Postgres-only column types (JSONB) fall back to JSON via
    the ``with_variant`` declarations in the SQLAlchemy models.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        yield factory
    finally:
        await engine.dispose()
