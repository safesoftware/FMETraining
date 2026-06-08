"""Skilljar canonical content tables, lesson drafts, locks, and history.

Implements the **revised** plan (2026-04-29) which replaces the older
``skilljar_mapping`` / monolithic ``skilljar_inventory`` shape with:

* ``skilljar_courses`` / ``skilljar_lessons`` / ``skilljar_published_paths``
  -- canonical content synced from the Skilljar REST API.
* ``lesson_drafts`` -- in-flight next-version lessons stored in S3.
* ``release_locks`` / ``release_history`` -- keyed on a string
  ``target_id`` of the form ``"lesson:<skilljar_lesson_id>"`` (existing
  Skilljar lesson) or ``"draft:<lesson_drafts.id>"`` (net-new lesson).

Plan section 2:

    skilljar_courses(skilljar_course_id PK, title, slug, version_label,
                     raw_meta_json, fetched_at)
    skilljar_lessons(skilljar_lesson_id PK, course_id FK, title, slug,
                     content_s3_key, content_html_hash,
                     last_modified_remote, fetched_at)
    skilljar_published_paths(skilljar_path_id PK, title, slug,
                             course_ids_json, fetched_at)
    lesson_drafts(id PK, to_version, source_skilljar_lesson_id NULLABLE,
                  path, s3_key, created_by, updated_by, created_at,
                  updated_at, run_id NULLABLE, status)
    release_locks(target_id PK, locked_by, locked_at, expires_at,
                  run_id, intent)
    release_history(id PK, target_id, skilljar_lesson_id NULLABLE,
                    draft_id NULLABLE, run_id, user_id, started_at,
                    finished_at, before_hash, after_hash, status,
                    conflict_warning_json NULLABLE)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base, utc_now

JSONType = JSON().with_variant(JSONB(), "postgresql")


# ---------------------------------------------------------------------------
# Canonical Skilljar content
# ---------------------------------------------------------------------------


class SkilljarCourse(Base):
    """One row per Skilljar course we know about."""

    __tablename__ = "skilljar_courses"

    skilljar_course_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    # Version comes from a course tag/label (e.g. "version:2026.1"); we
    # extract it during sync and denormalise it here for fast filtering.
    version_label: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    raw_meta_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SkilljarCourse id={self.skilljar_course_id!r} version={self.version_label!r}>"


class SkilljarLesson(Base):
    """One row per Skilljar lesson; ``content_s3_key`` points at the
    cached HTML in ``s3://.../skilljar-content/{lesson_id}/{ts}.html``.
    """

    __tablename__ = "skilljar_lessons"
    __table_args__ = (
        Index("ix_skilljar_lessons_course_id", "course_id"),
    )

    skilljar_lesson_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    course_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("skilljar_courses.skilljar_course_id", ondelete="SET NULL"),
        nullable=True,
    )
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    content_s3_key: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    content_html_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    last_modified_remote: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SkilljarLesson id={self.skilljar_lesson_id!r} course={self.course_id!r}>"


class SkilljarPublishedPath(Base):
    """A learning path (``/v1/published-paths``) -- many lessons->one path.

    ``course_ids_json`` is the ordered list of Skilljar course IDs that
    belong to this path. Stored denormalised because the relationship
    is many-to-many and the order matters for UI display.
    """

    __tablename__ = "skilljar_published_paths"

    skilljar_path_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    course_ids_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<SkilljarPublishedPath id={self.skilljar_path_id!r} title={self.title!r}>"


# ---------------------------------------------------------------------------
# Lesson drafts (replaces local 2026.1/.../index.html writes)
# ---------------------------------------------------------------------------


class LessonDraft(Base):
    """In-flight next-version lesson stored in
    ``s3://.../drafts/{to_version}/{path}/index.html``.
    """

    __tablename__ = "lesson_drafts"
    __table_args__ = (
        # UNIQUE on (to_version, path) so two concurrent POSTs to
        # /api/drafts can't race the existence check and create
        # duplicate rows for the same lesson. The route catches the
        # resulting IntegrityError and retries as an UPDATE.
        UniqueConstraint(
            "to_version", "path", name="uq_lesson_drafts_to_version_path",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    to_version: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    # NULL when this is a brand-new lesson with no Skilljar parent.
    source_skilljar_lesson_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("skilljar_lessons.skilljar_lesson_id", ondelete="SET NULL"),
        nullable=True,
    )
    # "<learning-path>/<course>/<lesson>" Skilljar-taxonomy triple.
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)

    created_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    updated_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    # Run that last wrote this draft (may be NULL for hand-edited drafts).
    run_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    # draft | promoted | archived
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="draft", index=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<LessonDraft id={self.id!r} to_version={self.to_version!r} path={self.path!r}>"


# ---------------------------------------------------------------------------
# Locks + history (keyed on string target_id)
# ---------------------------------------------------------------------------


class ReleaseLock(Base):
    """Advisory lock on a release target.

    ``target_id`` is the string composite key:

    * ``"lesson:<skilljar_lesson_id>"`` for existing Skilljar lessons.
    * ``"draft:<lesson_drafts.id>"``    for net-new lessons being
                                         pushed for the first time.
    """

    __tablename__ = "release_locks"

    target_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    locked_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    locked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    run_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    intent: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ReleaseLock target={self.target_id!r} expires={self.expires_at!r}>"


class ReleaseHistory(Base):
    """Append-only audit row for every Skilljar push attempt."""

    __tablename__ = "release_history"
    __table_args__ = (
        Index("ix_release_history_target_id", "target_id"),
        Index("ix_release_history_skilljar_lesson_id", "skilljar_lesson_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    target_id: Mapped[str] = mapped_column(String(128), nullable=False)
    skilljar_lesson_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("skilljar_lessons.skilljar_lesson_id", ondelete="SET NULL"),
        nullable=True,
    )
    draft_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("lesson_drafts.id", ondelete="SET NULL"),
        nullable=True,
    )
    run_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    before_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    after_hash: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)

    # success | failed | conflict_override | aborted
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="success")

    # Populated when the user pushed past a hash mismatch.
    conflict_warning_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ReleaseHistory id={self.id!r} target={self.target_id!r} status={self.status!r}>"
