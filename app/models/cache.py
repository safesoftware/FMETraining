"""Shared content cache tables.

Plan section 2:

    content_cache(fingerprint PK = sha256, kind, model, prompt_version,
                  s3_key, payload_summary_json, created_at, last_hit_at,
                  hit_count, created_by_run_id)
                  -- kinds: assessment_pair, edit_plan_lesson,
                  -- manifest_lesson, changelog_filter, image_upload
    s3_image_cache(content_sha256 PK, s3_url, content_type, byte_size,
                   first_uploaded_at, hit_count)
    jira_cache(filter_id PK, fetched_at, payload_s3_key, issue_count)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base, utc_now

JSONType = JSON().with_variant(JSONB(), "postgresql")


class ContentCache(Base):
    """OpenAI / pipeline output cache, keyed by deterministic fingerprint.

    See plan section 4 for the fingerprint formula.
    """

    __tablename__ = "content_cache"

    fingerprint: Mapped[str] = mapped_column(String(64), primary_key=True)
    # assessment_pair | edit_plan_lesson | manifest_lesson |
    # changelog_filter | image_upload
    kind: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    model: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    prompt_version: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    s3_key: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    payload_summary_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    last_hit_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_by_run_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<ContentCache fp={self.fingerprint!r} kind={self.kind!r} hits={self.hit_count!r}>"


class S3ImageCache(Base):
    """Dedup table for lesson images uploaded to the public S3 image bucket."""

    __tablename__ = "s3_image_cache"

    content_sha256: Mapped[str] = mapped_column(String(64), primary_key=True)
    s3_url: Mapped[str] = mapped_column(String(1024), nullable=False)
    content_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    byte_size: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    first_uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    hit_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<S3ImageCache sha={self.content_sha256[:8]!r} hits={self.hit_count!r}>"


class JiraCache(Base):
    """Cached Jira filter response metadata; payload lives in S3."""

    __tablename__ = "jira_cache"

    filter_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    payload_s3_key: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    issue_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<JiraCache filter={self.filter_id!r} count={self.issue_count!r}>"
