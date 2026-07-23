"""Usage / adoption metrics (KNOW-2166).

Aggregates two signals that do NOT depend on the in-app accept/reject
workflow (reviewers often just read the report, then edit directly in
Skilljar):

* **runs generated** per release cycle, and how many distinct people
  generated them (from ``runs``);
* **report opens** per release cycle -- total opens, distinct viewers, and
  how many distinct runs' reports were opened (from ``report_views``).

Both are grouped by ``runs.to_version`` (the release cycle). Distinct totals
are computed with their own scalar queries rather than summed per-version, so
a user active across two versions is counted once.

Backs ``GET /api/metrics/usage`` and the ``/usage`` panel.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import utc_now
from app.models.report_views import ReportView
from app.models.runs import Run


@dataclass
class VersionUsage:
    """Per-release-cycle usage row."""

    to_version: Optional[str]
    runs: int = 0            # runs generated for this version
    runners: int = 0         # distinct users who generated a run
    reports_opened: int = 0  # distinct runs whose report was opened
    opens: int = 0           # total report opens
    viewers: int = 0         # distinct users who opened a report
    last_open: Optional[datetime] = None


@dataclass
class UsageReport:
    """Whole-fleet usage summary."""

    versions: list[VersionUsage] = field(default_factory=list)
    total_runs: int = 0
    total_runners: int = 0   # distinct across all versions
    total_opens: int = 0
    total_viewers: int = 0   # distinct across all versions
    generated_at: datetime = field(default_factory=utc_now)


async def compute_usage(session: AsyncSession) -> UsageReport:
    """Compute the usage report from ``runs`` + ``report_views``."""
    # Runs + distinct runners per version.
    runs_rows = (
        await session.execute(
            select(
                Run.to_version,
                func.count(Run.id),
                func.count(func.distinct(Run.created_by)),
            ).group_by(Run.to_version)
        )
    ).all()

    # Report opens joined back to the run's version: total opens, distinct
    # viewers, distinct runs opened, most-recent open.
    view_rows = (
        await session.execute(
            select(
                Run.to_version,
                func.count(ReportView.id),
                func.count(func.distinct(ReportView.user_id)),
                func.count(func.distinct(ReportView.run_id)),
                func.max(ReportView.viewed_at),
            )
            .join(Run, Run.id == ReportView.run_id)
            .group_by(Run.to_version)
        )
    ).all()

    by_version: dict[Optional[str], VersionUsage] = {}
    for to_version, runs, runners in runs_rows:
        by_version[to_version] = VersionUsage(
            to_version=to_version, runs=runs, runners=runners
        )
    for to_version, opens, viewers, reports_opened, last_open in view_rows:
        bucket = by_version.get(to_version)
        if bucket is None:
            # Views can exist for a version with no runs row only in odd
            # data states; still surface them.
            bucket = VersionUsage(to_version=to_version)
            by_version[to_version] = bucket
        bucket.opens = opens
        bucket.viewers = viewers
        bucket.reports_opened = reports_opened
        bucket.last_open = last_open

    # Newest release cycle first (string desc works for YYYY.N); runs missing
    # a to_version sort to the end.
    real = sorted(
        (vu for vu in by_version.values() if vu.to_version is not None),
        key=lambda vu: vu.to_version,
        reverse=True,
    )
    unspecified = [vu for vu in by_version.values() if vu.to_version is None]
    versions = real + unspecified

    # Distinct totals across ALL versions (not a sum of per-version distincts).
    total_runs = await session.scalar(select(func.count(Run.id))) or 0
    total_runners = (
        await session.scalar(select(func.count(func.distinct(Run.created_by)))) or 0
    )
    total_opens = await session.scalar(select(func.count(ReportView.id))) or 0
    total_viewers = (
        await session.scalar(
            select(func.count(func.distinct(ReportView.user_id)))
        )
        or 0
    )

    return UsageReport(
        versions=versions,
        total_runs=total_runs,
        total_runners=total_runners,
        total_opens=total_opens,
        total_viewers=total_viewers,
    )
