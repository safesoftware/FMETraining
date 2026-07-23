"""``report_views`` table -- one row per report open (KNOW-2166 usage metric).

Append-only event log: each authenticated ``GET /report/{run_id}`` inserts a
row recording *who* opened *which* run's report and *when*. This captures the
"referring to the edits" behaviour that today leaves no trace -- the report
HTML is a static ``/artifacts`` file, and the in-app accept/reject workflow is
often skipped (reviewers read the report, then edit directly in the Skilljar
WYSIWYG). Aggregating these rows by run + release version + user yields a
usage/adoption metric that does **not** depend on the full in-app workflow.

Distinct from the request-level access log (uvicorn / nginx): those lines
carry no user identity, because the app sits behind an nginx reverse proxy so
every client appears as ``127.0.0.1``. This table attributes each view to a
signed-in ``@safe.com`` user via the FK to ``users``.

Writes are best-effort (see ``app/routes/report.py``): a failure to record a
view never blocks the redirect to the report.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class ReportView(Base):
    """One row per authenticated open of a run's HTML report."""

    __tablename__ = "report_views"

    # BigInteger on Postgres for room to grow; Integer on SQLite so the
    # column maps to ROWID and autoincrement works in unit tests (mirrors
    # ``RunLog``).
    id: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer(), "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    run_id: Mapped[str] = mapped_column(
        String(64),
        ForeignKey("runs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Nullable + SET NULL so removing a user preserves the historical view
    # (the event still happened); indexed for per-user aggregation.
    user_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, index=True
    )

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return (
            f"<ReportView id={self.id!r} run_id={self.run_id!r} "
            f"user_id={self.user_id!r}>"
        )
