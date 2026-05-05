"""Sync the Skilljar inventory into our DB.

Plan section 5: ``POST /api/skilljar-inventory/sync`` paginates the
three Skilljar list endpoints and upserts:

- ``skilljar_courses`` (+ ``version_label`` extracted from tags)
- ``skilljar_lessons``
- ``skilljar_published_paths``

This module owns the DB upsert logic. The HTTP client lives in
``app.services.skilljar_client``; the route that calls into here lives
in ``app.routes.skilljar``.

Lesson HTML caching is intentionally NOT done here — that's a follow-up.
The sync endpoint just refreshes the metadata so the Release tab can
build its tree. The cache lands when ``SkilljarContentSource`` ships.
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.skilljar import (
    SkilljarCourse,
    SkilljarLesson,
    SkilljarPublishedPath,
)
from app.services.skilljar_client import SkilljarClient

_logger = logging.getLogger(__name__)

# Course tags look like "version:2026.1"; we extract the value into the
# denormalised ``version_label`` column for cheap filtering.
_VERSION_TAG_RE = re.compile(r"^version:(.+)$")


@dataclass
class SyncCounts:
    """Returned by :func:`sync_inventory` so the API can report what changed.

    Per table we track three numbers:
    - ``*_seen``     — total rows Skilljar returned.
    - ``*_inserted`` — rows that were brand new in our DB.
    - ``*_updated``  — rows we already had whose content changed (any
                      field other than ``fetched_at``).

    Rows whose only change is ``fetched_at`` aren't counted as updated —
    that would make every sync look like every row changed, which is
    useless as a "did anything actually change?" signal.
    """

    courses_seen: int = 0
    courses_inserted: int = 0
    courses_updated: int = 0
    lessons_seen: int = 0
    lessons_inserted: int = 0
    lessons_updated: int = 0
    paths_seen: int = 0
    paths_inserted: int = 0
    paths_updated: int = 0


def _extract_version_label(course: dict) -> Optional[str]:
    """Pull a ``version:<x>`` tag off a Skilljar course.

    Skilljar's course schema has a ``tags`` field (list of strings). We
    iterate, return the first ``version:`` match, or None.
    """
    tags = course.get("tags") or []
    for tag in tags:
        if not isinstance(tag, str):
            continue
        m = _VERSION_TAG_RE.match(tag.strip())
        if m:
            return m.group(1).strip()
    return None


async def sync_inventory(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    client: SkilljarClient,
) -> SyncCounts:
    """Run a full sync. Idempotent — re-running on unchanged data does
    not increment ``*_inserted`` or ``*_updated``."""
    counts = SyncCounts()

    (
        counts.courses_seen,
        counts.courses_inserted,
        counts.courses_updated,
    ) = await _sync_courses(session_factory, client.list_courses())
    (
        counts.lessons_seen,
        counts.lessons_inserted,
        counts.lessons_updated,
    ) = await _sync_lessons(session_factory, client.list_lessons())
    (
        counts.paths_seen,
        counts.paths_inserted,
        counts.paths_updated,
    ) = await _sync_published_paths(
        session_factory, client.list_published_paths()
    )

    _logger.info(
        "Skilljar sync complete: courses=%d (+%d/~%d) lessons=%d (+%d/~%d) "
        "paths=%d (+%d/~%d)",
        counts.courses_seen, counts.courses_inserted, counts.courses_updated,
        counts.lessons_seen, counts.lessons_inserted, counts.lessons_updated,
        counts.paths_seen, counts.paths_inserted, counts.paths_updated,
    )
    return counts


# ---------------------------------------------------------------------------
# Per-table upsert loops
# ---------------------------------------------------------------------------


async def _sync_courses(
    session_factory: async_sessionmaker[AsyncSession],
    rows: AsyncIterator[dict],
) -> tuple[int, int, int]:
    seen = 0
    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc)
    async for row in rows:
        seen += 1
        course_id = str(row.get("id") or "").strip()
        if not course_id:
            _logger.warning("Skilljar course payload missing id: %r", row)
            continue
        new_title = row.get("title")
        new_slug = row.get("slug")
        new_version = _extract_version_label(row)
        async with session_factory() as session:
            existing = await session.get(SkilljarCourse, course_id)
            if existing is None:
                session.add(
                    SkilljarCourse(
                        skilljar_course_id=course_id,
                        title=new_title,
                        slug=new_slug,
                        version_label=new_version,
                        raw_meta_json=row,
                        fetched_at=now,
                    )
                )
                inserted += 1
            else:
                changed = (
                    existing.title != new_title
                    or existing.slug != new_slug
                    or existing.version_label != new_version
                    or existing.raw_meta_json != row
                )
                existing.title = new_title
                existing.slug = new_slug
                existing.version_label = new_version
                existing.raw_meta_json = row
                existing.fetched_at = now
                if changed:
                    updated += 1
            await session.commit()
    return seen, inserted, updated


async def _sync_lessons(
    session_factory: async_sessionmaker[AsyncSession],
    rows: AsyncIterator[dict],
) -> tuple[int, int, int]:
    seen = 0
    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc)
    async for row in rows:
        seen += 1
        lesson_id = str(row.get("id") or "").strip()
        if not lesson_id:
            _logger.warning("Skilljar lesson payload missing id: %r", row)
            continue
        course_id = row.get("course_id") or row.get("course")
        if isinstance(course_id, dict):
            course_id = course_id.get("id")
        course_id = str(course_id).strip() if course_id else None

        # last_modified_remote: Skilljar exposes ``modified_at`` (ISO 8601).
        modified_raw = row.get("modified_at") or row.get("updated_at")
        last_modified: Optional[datetime] = None
        if modified_raw:
            try:
                last_modified = datetime.fromisoformat(
                    modified_raw.replace("Z", "+00:00")
                )
            except (TypeError, ValueError):
                last_modified = None

        new_title = row.get("title")
        new_slug = row.get("slug")
        async with session_factory() as session:
            # Skip the FK link if we haven't synced the parent course yet —
            # the SET NULL FK column allows it. The narrow case where this
            # leaves a permanently NULL FK is "lesson references a course
            # that was deleted from Skilljar between the courses fetch and
            # the lessons fetch" — rare, and the next sync repairs it.
            course_fk = course_id if await _course_exists(session, course_id) else None
            existing = await session.get(SkilljarLesson, lesson_id)
            if existing is None:
                session.add(
                    SkilljarLesson(
                        skilljar_lesson_id=lesson_id,
                        course_id=course_fk,
                        title=new_title,
                        slug=new_slug,
                        last_modified_remote=last_modified,
                        fetched_at=now,
                    )
                )
                inserted += 1
            else:
                changed = (
                    existing.course_id != course_fk
                    or existing.title != new_title
                    or existing.slug != new_slug
                    or existing.last_modified_remote != last_modified
                )
                existing.course_id = course_fk
                existing.title = new_title
                existing.slug = new_slug
                existing.last_modified_remote = last_modified
                existing.fetched_at = now
                if changed:
                    updated += 1
            await session.commit()
    return seen, inserted, updated


async def _course_exists(session: AsyncSession, course_id: Optional[str]) -> bool:
    if course_id is None:
        return False
    return (
        await session.scalar(
            select(SkilljarCourse.skilljar_course_id).where(
                SkilljarCourse.skilljar_course_id == course_id
            )
        )
    ) is not None


async def _sync_published_paths(
    session_factory: async_sessionmaker[AsyncSession],
    rows: AsyncIterator[dict],
) -> tuple[int, int, int]:
    seen = 0
    inserted = 0
    updated = 0
    now = datetime.now(timezone.utc)
    async for row in rows:
        seen += 1
        path_id = str(row.get("id") or "").strip()
        if not path_id:
            _logger.warning("Skilljar published_path payload missing id: %r", row)
            continue
        course_ids = _extract_course_ids(row)
        new_title = row.get("title")
        new_slug = row.get("slug")
        async with session_factory() as session:
            existing = await session.get(SkilljarPublishedPath, path_id)
            if existing is None:
                session.add(
                    SkilljarPublishedPath(
                        skilljar_path_id=path_id,
                        title=new_title,
                        slug=new_slug,
                        course_ids_json=course_ids,
                        fetched_at=now,
                    )
                )
                inserted += 1
            else:
                changed = (
                    existing.title != new_title
                    or existing.slug != new_slug
                    or existing.course_ids_json != course_ids
                )
                existing.title = new_title
                existing.slug = new_slug
                existing.course_ids_json = course_ids
                existing.fetched_at = now
                if changed:
                    updated += 1
            await session.commit()
    return seen, inserted, updated


def _extract_course_ids(path_row: dict) -> list[str]:
    """Skilljar's published-path payload exposes ``courses`` as a list of
    course objects (each with ``id``) OR a list of bare ids — handle both.
    """
    courses = path_row.get("courses") or path_row.get("course_ids") or []
    out: list[str] = []
    for c in courses:
        if isinstance(c, dict):
            cid = c.get("id")
        else:
            cid = c
        if cid is not None:
            out.append(str(cid))
    return out
