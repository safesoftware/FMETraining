"""``jobs`` table -- replaces ``data/update-job.json``.

Plan section 2:

    jobs(id, owner FK->users, to_version, scope_json, updated_at)
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base, utc_now

JSONType = JSON().with_variant(JSONB(), "postgresql")


class Job(Base):
    """A user's saved pipeline configuration (one per owner)."""

    __tablename__ = "jobs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    owner: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    to_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    scope_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Job id={self.id!r} owner={self.owner!r} to_version={self.to_version!r}>"
