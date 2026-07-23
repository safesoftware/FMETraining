"""Usage / adoption metrics (KNOW-2166).

* ``GET /api/metrics/usage`` — JSON usage report (runs + report opens per
  release cycle, with distinct-user counts).
* ``GET /usage``            — the "Usage" panel, an HTML view of the same
  data (mirrors the ``/drafts`` dashboard).

Both require a signed-in user. The numbers come from
``app.services.usage_metrics.compute_usage`` and do NOT depend on the in-app
accept/reject workflow — they measure whether the tool is run and whether its
reports are opened during the release cycle.
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.requests import Request

from app.auth.dependencies import require_user
from app.db.session import get_session
from app.services import usage_metrics as svc
from app.templates import templates

router = APIRouter(tags=["metrics"])


class VersionUsageOut(BaseModel):
    to_version: Optional[str]
    runs: int
    runners: int
    reports_opened: int
    opens: int
    viewers: int
    last_open: Optional[datetime]


class UsageReportOut(BaseModel):
    versions: list[VersionUsageOut]
    total_runs: int
    total_runners: int
    total_opens: int
    total_viewers: int
    generated_at: datetime


@router.get("/api/metrics/usage", response_model=UsageReportOut)
async def usage_metrics(
    _user=Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> UsageReportOut:
    report = await svc.compute_usage(session)
    return UsageReportOut(
        versions=[
            VersionUsageOut(
                to_version=v.to_version,
                runs=v.runs,
                runners=v.runners,
                reports_opened=v.reports_opened,
                opens=v.opens,
                viewers=v.viewers,
                last_open=v.last_open,
            )
            for v in report.versions
        ],
        total_runs=report.total_runs,
        total_runners=report.total_runners,
        total_opens=report.total_opens,
        total_viewers=report.total_viewers,
        generated_at=report.generated_at,
    )


@router.get("/usage", response_class=HTMLResponse)
async def usage_page(
    request: Request,
    _user=Depends(require_user),
    session: AsyncSession = Depends(get_session),
) -> HTMLResponse:
    report = await svc.compute_usage(session)
    return templates.TemplateResponse(request, "usage.html", {"report": report})
