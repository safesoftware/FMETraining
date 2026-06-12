"""Run management routes (KNOW-2335).

Endpoints:

* ``POST /api/runs``               — create + enqueue a new run.
* ``GET  /api/runs``               — recent runs list.
* ``GET  /api/runs/{run_id}``      — run status + per-step statuses.
* ``GET  /api/versions``           — available content versions.
* ``GET  /api/content-tree``       — LP/course/lesson tree for a version.

The ``POST /api/runs`` handler:
  - Requires a signed-in ``@safe.com`` user (via ``Depends(require_user)``).
  - Validates ``to_version`` (non-empty, matches ``YYYY.N`` format).
  - Validates ``steps`` (subset of 1–6, comma-separated, optional — defaults to
    "1,2,3,5").
  - Validates scope (at least one lesson/course/learning_path unless dry_run).
  - Calls ``generate_run_id()`` for the primary key.
  - Inserts a ``Run(status='queued')`` row; the ``RunScheduler`` auto-dispatches.
  - Returns ``{"run_id": "<id>"}``.
"""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_user
from app.config import get_settings
from app.db.session import get_session
from app.models.runs import Run, RunStep
from app.models.users import User
from app.services.lesson_content_source import LocalFolderSource
from app.services.report_regen import RecommendationsNotFound, regenerate_report
from pipeline.utils import generate_run_id

_logger = logging.getLogger(__name__)

router = APIRouter(tags=["runs"])

# Version format: YYYY.N (e.g. "2026.1", "2025.0")
_VERSION_RE = re.compile(r"^\d{4}\.\d+$")
_VALID_STEPS = frozenset(range(1, 7))  # 1–6


# ---------------------------------------------------------------------------
# Request / response schemas
# ---------------------------------------------------------------------------


class _ScopeIn(BaseModel):
    lessons: list[str] = Field(default_factory=list)
    courses: list[dict[str, str]] = Field(default_factory=list)
    learning_paths: list[str] = Field(default_factory=list)


class _OptionsIn(BaseModel):
    jira_source: str = Field(default="csv", pattern="^(csv|api)$")
    refresh_jira: bool = False
    dry_run: bool = False
    steps: str = Field(default="1,2,3,5,6")

    @field_validator("steps")
    @classmethod
    def _validate_steps(cls, v: str) -> str:
        if not v.strip():
            return "1,2,3,5,6"
        parts = [s.strip() for s in v.split(",") if s.strip()]
        try:
            nums = {int(p) for p in parts}
        except ValueError as exc:
            raise ValueError(f"steps must be comma-separated integers: {v!r}") from exc
        invalid = nums - _VALID_STEPS
        if invalid:
            raise ValueError(f"steps must be subset of 1–6; invalid: {sorted(invalid)}")
        return ",".join(str(n) for n in sorted(nums))


class CreateRunRequest(BaseModel):
    to_version: str
    scope: _ScopeIn = Field(default_factory=_ScopeIn)
    options: _OptionsIn = Field(default_factory=_OptionsIn)

    @field_validator("to_version")
    @classmethod
    def _validate_version(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("to_version is required")
        if not _VERSION_RE.match(v):
            raise ValueError(
                f"to_version must be in YYYY.N format (e.g. '2026.1'); got {v!r}"
            )
        return v


class CreateRunResponse(BaseModel):
    run_id: str


class _RunSummary(BaseModel):
    run_id: str
    status: str
    to_version: Optional[str]
    created_at: datetime
    created_by: Optional[int]


class RunListResponse(BaseModel):
    runs: list[_RunSummary]


class _StepStatus(BaseModel):
    step_num: int
    status: str
    started_at: Optional[datetime]
    finished_at: Optional[datetime]


class RunDetailResponse(BaseModel):
    run_id: str
    status: str
    to_version: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    error_text: Optional[str]
    steps: list[_StepStatus]


class RegenerateReportResponse(BaseModel):
    run_id: str
    report_url: str


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _scope_is_empty(scope: _ScopeIn) -> bool:
    return not scope.lessons and not scope.courses and not scope.learning_paths


def _get_content_source() -> LocalFolderSource:
    settings = get_settings()
    root = Path(settings.lesson_content_root).resolve()
    return LocalFolderSource(root)


# ---------------------------------------------------------------------------
# POST /api/runs
# ---------------------------------------------------------------------------


@router.post(
    "/api/runs",
    response_model=CreateRunResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_run(
    body: CreateRunRequest,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_user),
) -> CreateRunResponse:
    """Create and enqueue a new pipeline run.

    The ``RunScheduler`` (started in ``app.main.lifespan``) polls for
    ``status='queued'`` rows and dispatches automatically — no extra call needed.
    """
    # Scope validation: must have something unless dry_run
    if not body.options.dry_run and _scope_is_empty(body.scope):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "scope must include at least one lesson, course, or learning_path "
                "unless dry_run=true"
            ),
        )

    run_id = generate_run_id()
    now = datetime.now(timezone.utc)

    # Build the scope_json and options_json to persist
    scope_json: dict[str, Any] = {
        "lessons": body.scope.lessons,
        "courses": body.scope.courses,
        "learning_paths": body.scope.learning_paths,
    }
    options_json: dict[str, Any] = {
        "jira_source": body.options.jira_source,
        "refresh_jira": body.options.refresh_jira,
        "dry_run": body.options.dry_run,
        "steps": body.options.steps,
    }

    run = Run(
        id=run_id,
        created_by=user.id,
        to_version=body.to_version,
        scope_json=scope_json,
        options_json=options_json,
        status="queued",
        created_at=now,
    )
    session.add(run)
    await session.commit()

    _logger.info(
        "Queued run %s for user %s → version %s (dry_run=%s, steps=%s)",
        run_id,
        user.email,
        body.to_version,
        body.options.dry_run,
        body.options.steps,
    )

    return CreateRunResponse(run_id=run_id)


# ---------------------------------------------------------------------------
# GET /api/runs
# ---------------------------------------------------------------------------


@router.get(
    "/api/runs",
    response_model=RunListResponse,
)
async def list_runs(
    limit: int = Query(default=50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_user),
) -> RunListResponse:
    """Return the most-recent runs (newest first)."""
    result = await session.execute(
        select(Run)
        .order_by(Run.created_at.desc())
        .limit(limit)
    )
    runs = result.scalars().all()
    return RunListResponse(
        runs=[
            _RunSummary(
                run_id=r.id,
                status=r.status,
                to_version=r.to_version,
                created_at=r.created_at,
                created_by=r.created_by,
            )
            for r in runs
        ]
    )


# ---------------------------------------------------------------------------
# GET /api/runs/{run_id}
# ---------------------------------------------------------------------------


@router.get(
    "/api/runs/{run_id}",
    response_model=RunDetailResponse,
)
async def get_run(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_user),
) -> RunDetailResponse:
    """Return status + per-step statuses for a single run."""
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")

    steps_result = await session.execute(
        select(RunStep)
        .where(RunStep.run_id == run_id)
        .order_by(RunStep.step_num)
    )
    steps = steps_result.scalars().all()

    return RunDetailResponse(
        run_id=run.id,
        status=run.status,
        to_version=run.to_version,
        created_at=run.created_at,
        started_at=run.started_at,
        finished_at=run.finished_at,
        error_text=run.error_text,
        steps=[
            _StepStatus(
                step_num=s.step_num,
                status=s.status,
                started_at=s.started_at,
                finished_at=s.finished_at,
            )
            for s in steps
        ],
    )


# ---------------------------------------------------------------------------
# POST /api/runs/{run_id}/regenerate-report — ported from serve.py run-action
# ---------------------------------------------------------------------------


@router.post(
    "/api/runs/{run_id}/regenerate-report",
    response_model=RegenerateReportResponse,
)
async def regenerate_run_report(
    run_id: str,
    session: AsyncSession = Depends(get_session),
    user: User = Depends(require_user),
) -> RegenerateReportResponse:
    """Regenerate the HTML report for an existing run from its artifacts.

    Ports the legacy launcher's "Regenerate Report" action (``serve.py``
    ``/api/run-action`` → ``pipeline.py --report-only``). Re-runs
    ``build_report`` in-process over the run's existing artifacts — **no OpenAI
    cost** — so report fixes (e.g. the KNOW-2347 lesson-image route) can be
    applied to already-completed runs without a full, paid re-run.

    Guards:
      - 404 if the run isn't in the DB.
      - 409 if the run has no ``update-recommendations-<run_id>.json`` artifact
        (nothing to render yet).
    """
    run = await session.get(Run, run_id)
    if run is None:
        raise HTTPException(status_code=404, detail=f"Run {run_id!r} not found")

    try:
        await regenerate_report(run_id)
    except RecommendationsNotFound as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    _logger.info("User %s regenerated report for run %s", user.email, run_id)
    return RegenerateReportResponse(
        run_id=run_id,
        report_url=f"/report/{run_id}",
    )


# ---------------------------------------------------------------------------
# GET /api/versions — ported from serve.py
# ---------------------------------------------------------------------------


@router.get("/api/versions")
async def list_versions(
    user: User = Depends(require_user),
) -> list[str]:
    """Return version folders available in the lesson content root."""
    source = _get_content_source()
    root = source._repo_root
    if not root.is_dir():
        return []
    versions = sorted(
        [d.name for d in root.iterdir() if d.is_dir() and _VERSION_RE.match(d.name)],
        key=lambda v: [int(x) for x in v.split(".")],
        reverse=True,
    )
    return versions


# ---------------------------------------------------------------------------
# GET /api/content-tree — ported from serve.py
# ---------------------------------------------------------------------------

_COURSE_VERSION_SUFFIX = re.compile(r"\s+\d{4}[\.\d]*$")


def _build_content_tree(root: Path, version: str) -> list:
    """Build the LP/course/lesson tree for a version, mirroring serve.py."""
    version_dir = root / version
    if not version_dir.is_dir():
        return []
    tree = []
    for lp_dir in sorted(version_dir.iterdir()):
        if not lp_dir.is_dir():
            continue
        lp_label = lp_dir.name.replace("-", " ").title()
        courses = []
        for course_dir in sorted(lp_dir.iterdir()):
            if not course_dir.is_dir():
                continue
            course_canonical = _COURSE_VERSION_SUFFIX.sub("", course_dir.name).strip()
            lessons = []
            for lesson_dir in sorted(course_dir.iterdir()):
                if not lesson_dir.is_dir():
                    continue
                if not (lesson_dir / "index.html").exists():
                    continue
                path = "/".join([
                    version,
                    lp_dir.name,
                    course_dir.name,
                    lesson_dir.name,
                    "index.html",
                ])
                label = lesson_dir.name.replace("_", " ").strip()
                lessons.append({"id": lesson_dir.name, "label": label, "path": path})
            if lessons:
                courses.append({
                    "id": course_canonical,
                    "label": course_canonical,
                    "lessons": lessons,
                })
        if courses:
            tree.append({
                "id": lp_dir.name,
                "label": lp_label,
                "courses": courses,
            })
    return tree


@router.get("/api/content-tree")
async def get_content_tree(
    version: str = Query(..., description="Version string, e.g. '2026.1'"),
    user: User = Depends(require_user),
) -> list:
    """Return the LP/course/lesson tree for a version."""
    if not version or not _VERSION_RE.match(version):
        raise HTTPException(
            status_code=400,
            detail="valid version parameter required (e.g. '2026.1')",
        )
    source = _get_content_source()
    return _build_content_tree(source._repo_root, version)
