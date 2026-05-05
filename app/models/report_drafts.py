"""``report_lesson_drafts`` table -- per-lesson editor state for the
recommendations / lesson-edits report.

Phase 1a (KNOW-2276) of the report-persistence work. This table holds
the per-recommendation accept/reject decisions and the WYSIWYG body
HTML for one lesson within one pipeline run. Auto-saved by the report
JS as the user works; reset by an explicit "Reset to original" click;
marked with the saved-to-version-folder path when the user pushes a
durable snapshot via ``serve.py``'s legacy ``/api/save-lesson``.

Distinct from ``app.models.skilljar.LessonDraft`` (table
``lesson_drafts``), which is the S3-backed promoted-content draft used
by the Skilljar release pipeline. The two are unrelated.
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
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now
from app.models.runs import JSONType


class ReportLessonDraft(Base):
    """Editor-state row for one lesson inside one report run."""

    __tablename__ = "report_lesson_drafts"
    __table_args__ = (
        UniqueConstraint(
            "run_id", "lesson_dir", name="uq_report_lesson_drafts_run_id_lesson_dir"
        ),
        Index(
            "ix_report_lesson_drafts_run_id_updated_at",
            "run_id",
            "updated_at",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    # "<learning-path>/<course>/<lesson>" identifier matching the
    # ``lesson_dir`` field on each plan in edit-plans-{run_id}.json.
    lesson_dir: Mapped[str] = mapped_column(String(512), nullable=False)

    # { "<change_id>": "accepted" | "rejected" | "pending", ... }
    decisions_json: Mapped[Any] = mapped_column(
        JSONType, nullable=False, default=dict
    )
    # Raw ``#le-lesson-body.innerHTML`` at last auto-save. Preserves the
    # ``tc-wrap`` markup so the editor can round-trip on reload. NULL
    # until the user has typed into the WYSIWYG editor.
    body_html: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    saved_to_version_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    saved_to_version_path: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True
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
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<ReportLessonDraft id={self.id!r} run_id={self.run_id!r} "
            f"lesson_dir={self.lesson_dir!r}>"
        )
