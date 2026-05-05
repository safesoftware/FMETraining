"""Integration test for Skilljar inventory sync.

Drives :func:`app.services.skilljar_sync.sync_inventory` against an
in-memory SQLite + a stubbed ``SkilljarClient`` so the upsert paths,
version-tag extraction, FK linking, and idempotency all get exercised
without hitting the real API.
"""
from __future__ import annotations

from typing import AsyncIterator

import pytest
from sqlalchemy import select

from app.models.skilljar import (
    SkilljarCourse,
    SkilljarLesson,
    SkilljarPublishedPath,
)
from app.services.skilljar_sync import (
    _extract_version_label,
    sync_inventory,
)


# ---- stub client ---------------------------------------------------------

class _StubSkilljarClient:
    """Minimal duck-type that ``sync_inventory`` knows how to call into."""

    def __init__(
        self,
        *,
        courses: list[dict],
        lessons: list[dict],
        published_paths: list[dict],
    ) -> None:
        self._courses = courses
        self._lessons = lessons
        self._published_paths = published_paths

    async def list_courses(self) -> AsyncIterator[dict]:
        for c in self._courses:
            yield c

    async def list_lessons(self) -> AsyncIterator[dict]:
        for l in self._lessons:
            yield l

    async def list_published_paths(self) -> AsyncIterator[dict]:
        for p in self._published_paths:
            yield p


# ---- version tag extraction ---------------------------------------------

def test_extract_version_label_picks_first_version_tag() -> None:
    course = {"tags": ["topic:fme-form", "version:2026.1", "version:should-not-pick"]}
    assert _extract_version_label(course) == "2026.1"


def test_extract_version_label_returns_none_when_no_tag() -> None:
    assert _extract_version_label({"tags": ["topic:fme-form"]}) is None
    assert _extract_version_label({}) is None


# ---- happy path: end-to-end sync ----------------------------------------

@pytest.mark.asyncio
async def test_full_sync_upserts_all_three_tables(async_session_factory) -> None:
    client = _StubSkilljarClient(
        courses=[
            {"id": "c1", "title": "Connect To Data", "slug": "connect-to-data",
             "tags": ["topic:fme-form", "version:2026.1"]},
            {"id": "c2", "title": "Filter Features", "slug": "filter-features",
             "tags": ["version:2025.0"]},
        ],
        lessons=[
            {"id": "l1", "course_id": "c1", "title": "Connect to a Database",
             "slug": "connect-database", "modified_at": "2026-04-12T10:00:00Z"},
            {"id": "l2", "course_id": "c1", "title": "Connect to a Web Service",
             "slug": "connect-web-service"},
            {"id": "l3", "course_id": "c2", "title": "Tester Transformer",
             "slug": "tester"},
        ],
        published_paths=[
            {"id": "p1", "title": "FME Form Basic", "slug": "fme-form-basic",
             "courses": [{"id": "c1"}, {"id": "c2"}]},
        ],
    )

    counts = await sync_inventory(
        session_factory=async_session_factory, client=client
    )

    assert counts.courses_seen == 2 and counts.courses_upserted == 2
    assert counts.lessons_seen == 3 and counts.lessons_upserted == 3
    assert counts.paths_seen == 1 and counts.paths_upserted == 1

    async with async_session_factory() as session:
        courses = (await session.scalars(select(SkilljarCourse))).all()
        lessons = (await session.scalars(select(SkilljarLesson))).all()
        paths = (await session.scalars(select(SkilljarPublishedPath))).all()

    by_id = {c.skilljar_course_id: c for c in courses}
    assert by_id["c1"].version_label == "2026.1"
    assert by_id["c2"].version_label == "2025.0"
    assert by_id["c1"].title == "Connect To Data"

    lesson_by_id = {l.skilljar_lesson_id: l for l in lessons}
    # FK link populated because the parent course was synced first.
    assert lesson_by_id["l1"].course_id == "c1"
    assert lesson_by_id["l1"].last_modified_remote is not None

    assert len(paths) == 1
    assert paths[0].course_ids_json == ["c1", "c2"]


# ---- FK fallback: lesson references a course we don't have ---------------

@pytest.mark.asyncio
async def test_lesson_with_unknown_course_id_gets_null_fk(async_session_factory) -> None:
    """Edge case: lesson references a course not in this sync. The FK is
    nullable on purpose; we set it to NULL rather than failing the whole
    sync."""
    client = _StubSkilljarClient(
        courses=[],  # no courses synced
        lessons=[
            {"id": "orphan", "course_id": "ghost-course", "title": "Orphan"},
        ],
        published_paths=[],
    )
    counts = await sync_inventory(
        session_factory=async_session_factory, client=client
    )
    assert counts.lessons_upserted == 1
    async with async_session_factory() as session:
        l = await session.get(SkilljarLesson, "orphan")
    assert l is not None
    assert l.course_id is None  # FK left null


# ---- idempotency --------------------------------------------------------

@pytest.mark.asyncio
async def test_re_sync_is_idempotent(async_session_factory) -> None:
    """Running sync twice on the same data must not duplicate rows."""
    client = _StubSkilljarClient(
        courses=[{"id": "c1", "title": "C1", "tags": ["version:2026.1"]}],
        lessons=[{"id": "l1", "course_id": "c1", "title": "L1"}],
        published_paths=[{"id": "p1", "title": "P1", "courses": ["c1"]}],
    )

    await sync_inventory(session_factory=async_session_factory, client=client)
    await sync_inventory(session_factory=async_session_factory, client=client)

    async with async_session_factory() as session:
        c_count = len((await session.scalars(select(SkilljarCourse))).all())
        l_count = len((await session.scalars(select(SkilljarLesson))).all())
        p_count = len((await session.scalars(select(SkilljarPublishedPath))).all())
    assert (c_count, l_count, p_count) == (1, 1, 1)


# ---- update path: existing row gets refreshed ---------------------------

@pytest.mark.asyncio
async def test_re_sync_updates_changed_title(async_session_factory) -> None:
    initial = _StubSkilljarClient(
        courses=[{"id": "c1", "title": "Old Title", "tags": ["version:2026.1"]}],
        lessons=[],
        published_paths=[],
    )
    updated = _StubSkilljarClient(
        courses=[{"id": "c1", "title": "New Title", "tags": ["version:2026.1"]}],
        lessons=[],
        published_paths=[],
    )

    await sync_inventory(session_factory=async_session_factory, client=initial)
    await sync_inventory(session_factory=async_session_factory, client=updated)

    async with async_session_factory() as session:
        course = await session.get(SkilljarCourse, "c1")
    assert course.title == "New Title"


# ---- empty inventory ----------------------------------------------------

@pytest.mark.asyncio
async def test_empty_payload_is_a_clean_no_op(async_session_factory) -> None:
    client = _StubSkilljarClient(courses=[], lessons=[], published_paths=[])
    counts = await sync_inventory(
        session_factory=async_session_factory, client=client
    )
    assert counts.courses_seen == 0
    assert counts.lessons_seen == 0
    assert counts.paths_seen == 0
