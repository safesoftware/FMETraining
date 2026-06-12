"""Run lifecycle tables: ``runs``, ``run_steps``, ``run_logs``.

Plan section 2:

    runs(id PK = run_id, created_by FK->users, to_version, scope_json,
         options_json, status, started_at, finished_at,
         fargate_task_arn, error_text, parent_run_id NULLABLE)
    run_steps(run_id, step_num, status, started_at, finished_at,
              token_usage_json, artifact_keys_json)
    run_logs(id PK, run_id, ts, level, message)        -- append-only
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    PrimaryKeyConstraint,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import JSON

from app.models.base import Base, utc_now

# Use Postgres JSONB on Postgres, fall back to generic JSON elsewhere
# (e.g. SQLite during unit tests). The dialect picker keeps a single
# column type definition working in both worlds.
JSONType = JSON().with_variant(JSONB(), "postgresql")


class Run(Base):
    """A single pipeline run, replacing today's ``artifacts/runs.json``.

    The primary key is the human-readable ``run_id`` string (e.g.
    ``20260317T155430-28a8``) so existing artifacts and report URLs
    keep working post-migration.
    """

    __tablename__ = "runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    created_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    to_version: Mapped[Optional[str]] = mapped_column(String(32), nullable=True, index=True)
    scope_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)
    options_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)

    # queued | running | done | error | cancelled | cancel_requested |
    # aborted_cost_ceiling
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued", index=True)

    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )
    # When the HTML report was last (re)generated for this run. Set by the
    # manual "Regen Report" action (KNOW-2348) so Recent Runs can show an
    # "Updated" timestamp distinct from created_at.
    report_regenerated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    fargate_task_arn: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    error_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    parent_run_id: Mapped[Optional[str]] = mapped_column(
        String(64),
        ForeignKey("runs.id", ondelete="SET NULL"),
        nullable=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<Run id={self.id!r} status={self.status!r}>"


class RunStep(Base):
    """One row per (run, step_num). Composite PK lets Alembic generate
    a clean unique key without a synthetic id.
    """

    __tablename__ = "run_steps"
    __table_args__ = (
        PrimaryKeyConstraint("run_id", "step_num", name="pk_run_steps"),
    )

    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_num: Mapped[int] = mapped_column(Integer, nullable=False)
    # pending | running | done | error | skipped
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    started_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    finished_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    token_usage_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)
    artifact_keys_json: Mapped[Optional[Any]] = mapped_column(JSONType, nullable=True)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<RunStep run_id={self.run_id!r} step_num={self.step_num!r} status={self.status!r}>"


class RunLog(Base):
    """Append-only log line for live SSE streaming."""

    __tablename__ = "run_logs"
    __table_args__ = (
        Index("ix_run_logs_run_id_id", "run_id", "id"),
    )

    # BigInteger on Postgres for room to grow; Integer on SQLite so the
    # column maps to ROWID and autoincrement works in unit tests.
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    ts: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    # debug | info | warning | error
    level: Mapped[str] = mapped_column(String(16), nullable=False, default="info")
    message: Mapped[str] = mapped_column(Text, nullable=False)

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<RunLog id={self.id!r} run_id={self.run_id!r} level={self.level!r}>"
