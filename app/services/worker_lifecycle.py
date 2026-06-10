"""The lifecycle a per-run background worker runs through.

Plan section 3:

- The worker reads ``RUN_ID`` (and optional ``RESUME``, ``MAX_RUN_USD``)
  from env, looks up the corresponding ``runs`` row, and executes pipeline
  steps 1–6, appending to ``run_logs`` and updating ``run_steps``.
- It polls ``runs.status`` between steps so a ``cancel_requested`` from
  the API takes effect within ~1 step boundary.
- It honours the ``RunCostMeter`` ceiling, marking the run
  ``aborted_cost_ceiling`` if the next OpenAI call would push past the cap.

In production each worker runs as a templated systemd unit
(``fme-train-worker@<run_id>.service``); in local dev it can also run
in-process via :class:`InProcessTaskDispatcher`.

Today's scope (KNOW-2270): wire the lifecycle, the logger, the cost meter,
and the cancellation poll. The body of each step is a **stub** — actual
pipeline integration (rewiring ``pipeline/*`` modules to read inputs from
Postgres / object storage and write outputs back) lands in a follow-up ticket. The stub is
real enough to drive the moving parts: it writes log lines, advances
``run_steps`` rows, and respects cancellation.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.runs import Run, RunStep
from app.services.run_cost_meter import CostCeilingExceeded, RunCostMeter
from app.services.run_logger import RunLogger

_logger = logging.getLogger(__name__)


# Final terminal statuses.
TERMINAL_OK = "done"
TERMINAL_CANCELLED = "cancelled"
TERMINAL_ERROR = "error"
TERMINAL_COST_ABORTED = "aborted_cost_ceiling"

# How often the worker polls runs.status for an external cancel signal.
_CANCEL_POLL_S = 1.0

# Pipeline step IDs the worker tracks. v1 keeps the step contract from the
# legacy CLI: 1=manifest, 2=changelog, 3+4=assessment (combined), 5=report,
# 6=edit-suggestions.
PIPELINE_STEPS: tuple[int, ...] = (1, 2, 3, 4, 5, 6)


# A pluggable per-step body. The default is a stub; the real pipeline
# wiring will replace this in a follow-up ticket. Tests inject a custom
# callable to assert lifecycle behaviour without sleeping.
StepBody = Callable[[int, "WorkerContext"], Awaitable[None]]


class WorkerContext:
    """State passed into each step body. Lets steps log, record token usage,
    and check for cancellation without each step pulling its own session.

    New in KNOW-2334: the context is enriched with the Run row fields so that
    step bodies can access scope/options/to_version without a separate DB query.
    ``scratch`` is a plain dict for cross-step in-memory state (e.g. the full
    manifest/changelog dicts that carry Jira descriptions — these are never
    written to disk).
    """

    def __init__(
        self,
        *,
        run_id: str,
        logger: RunLogger,
        cost_meter: RunCostMeter,
        session_factory: async_sessionmaker[AsyncSession],
        # KNOW-2334: populated from the Run row in run_worker
        scope: Optional[dict] = None,
        options: Optional[dict] = None,
        to_version: Optional[str] = None,
        created_by: Optional[int] = None,
        job: Optional[dict] = None,
        requested_steps: Optional[frozenset[int]] = None,
        scratch: Optional[dict] = None,
    ) -> None:
        self.run_id = run_id
        self.logger = logger
        self.cost_meter = cost_meter
        self._session_factory = session_factory

        # KNOW-2334 enrichments
        self.scope: dict = scope or {}
        self.options: dict = options or {}
        self.to_version: Optional[str] = to_version
        self.created_by: Optional[int] = created_by
        # Legacy job dict shape: {"to_version": ..., "scope": ...}
        self.job: dict = job or {}
        # Steps that should actually run (default: all 1..6). Populated once
        # at the top of run_worker from options["steps"].
        self.requested_steps: frozenset[int] = (
            requested_steps if requested_steps is not None else frozenset(PIPELINE_STEPS)
        )
        # Cross-step scratch pad (manifests, changelogs, descriptions in
        # memory; never serialised to disk).
        self.scratch: dict[str, Any] = scratch if scratch is not None else {}

    async def is_cancelled(self) -> bool:
        async with self._session_factory() as session:
            status = await session.scalar(
                select(Run.status).where(Run.id == self.run_id)
            )
        return status == "cancel_requested"


async def _stub_step_body(step_num: int, ctx: WorkerContext) -> None:
    """Placeholder until the real pipeline integration ships.

    Writes a few log lines, briefly yields control, and returns. Enough to
    exercise the lifecycle (log batching, run_steps transitions, cancel
    polling) end-to-end in tests and local dev.
    """
    await ctx.logger.log("info", f"[step {step_num}] starting")
    # Yield so cancellation can interleave even in fast tests.
    await asyncio.sleep(0)
    await ctx.logger.log("info", f"[step {step_num}] complete (stub)")


def _parse_requested_steps(options: dict) -> frozenset[int]:
    """Parse ``options["steps"]`` into a frozenset of step ints.

    Accepts:
      - ``"1,2,3"`` → {1, 2, 3}
      - ``"1-3"``   → {1, 2, 3}   (simple range, for convenience)
      - ``None`` / missing → all of PIPELINE_STEPS

    Invalid tokens are silently skipped (non-fatal — we default to all steps).
    """
    raw = (options or {}).get("steps")
    if not raw:
        return frozenset(PIPELINE_STEPS)
    result: set[int] = set()
    for token in str(raw).split(","):
        token = token.strip()
        if "-" in token:
            parts = token.split("-", 1)
            try:
                lo, hi = int(parts[0]), int(parts[1])
                result.update(range(lo, hi + 1))
            except (ValueError, IndexError):
                pass
        else:
            try:
                result.add(int(token))
            except ValueError:
                pass
    # Intersect with valid steps so garbage input can't inject phantom steps.
    valid = frozenset(PIPELINE_STEPS)
    return result & valid if result else valid


async def run_worker(
    run_id: str,
    *,
    session_factory: async_sessionmaker[AsyncSession],
    max_run_usd: Optional[float] = None,
    resume: bool = False,
    step_body: StepBody = _stub_step_body,
    log_flush_interval_s: float = 0.2,
) -> str:
    """Drive the lifecycle for a single run. Returns the final status.

    Marks the run with one of:
      - TERMINAL_OK            — all steps completed
      - TERMINAL_CANCELLED     — observed cancel_requested between steps
      - TERMINAL_COST_ABORTED  — cost meter blew the ceiling
      - TERMINAL_ERROR         — an unhandled exception during a step

    KNOW-2334: loads the Run row once at startup and enriches WorkerContext
    with scope/options/to_version/job/requested_steps/scratch. Steps not in
    requested_steps are marked 'skipped' without calling step_body.
    Steps 3 and 4 are treated as a unit: assessment runs at 3, step 4 is a
    confirmation no-op (logs + marks done immediately).
    """
    ceiling = max_run_usd if max_run_usd is not None else float(
        os.environ.get("MAX_RUN_USD", "50")
    )
    cost_meter = RunCostMeter(ceiling_usd=ceiling)
    final_status = TERMINAL_OK
    error_text: Optional[str] = None

    # ---- Load Run row once -------------------------------------------------
    async with session_factory() as session:
        run_row = await session.get(Run, run_id)

    if run_row is None:
        _logger.error("run_worker: Run %s not found in DB", run_id)
        return TERMINAL_ERROR

    scope: dict = run_row.scope_json or {}
    options: dict = run_row.options_json or {}
    to_version: Optional[str] = run_row.to_version
    created_by: Optional[int] = run_row.created_by
    job: dict = {"to_version": to_version, "scope": scope}
    requested_steps = _parse_requested_steps(options)

    async with RunLogger.attached(
        session_factory, run_id, flush_interval_s=log_flush_interval_s
    ) as run_logger:
        ctx = WorkerContext(
            run_id=run_id,
            logger=run_logger,
            cost_meter=cost_meter,
            session_factory=session_factory,
            scope=scope,
            options=options,
            to_version=to_version,
            created_by=created_by,
            job=job,
            requested_steps=requested_steps,
            scratch={},
        )
        await run_logger.log(
            "info",
            f"Worker started (run_id={run_id}, resume={resume}, "
            f"ceiling=${ceiling:.2f}, to_version={to_version!r}, "
            f"requested_steps={sorted(requested_steps)})",
        )

        try:
            for step_num in PIPELINE_STEPS:
                if await ctx.is_cancelled():
                    final_status = TERMINAL_CANCELLED
                    await run_logger.log(
                        "warning",
                        f"Cancellation requested before step {step_num}; stopping.",
                    )
                    break

                # KNOW-2334: honour options["steps"] skip list
                if step_num not in requested_steps:
                    await run_logger.log(
                        "info",
                        f"[step {step_num}] not in requested_steps={sorted(requested_steps)}; skipping",
                    )
                    await _skip_step(session_factory, run_id, step_num)
                    continue

                if resume and await _step_already_done(session_factory, run_id, step_num):
                    await run_logger.log(
                        "info", f"[step {step_num}] resume: already done, skipping"
                    )
                    continue

                # KNOW-2334: step 4 is a no-op confirmation when step 3 ran
                if step_num == 4 and 3 in requested_steps:
                    await run_logger.log(
                        "info",
                        "[step 4] assessment confirmation (step 3+4 unit); marking done",
                    )
                    await _start_step(session_factory, run_id, step_num)
                    await _finish_step(
                        session_factory, run_id, step_num, "done", cost_meter
                    )
                    continue

                await _start_step(session_factory, run_id, step_num)
                try:
                    await step_body(step_num, ctx)
                except CostCeilingExceeded as exc:
                    final_status = TERMINAL_COST_ABORTED
                    error_text = str(exc)
                    await run_logger.log(
                        "error",
                        f"[step {step_num}] aborted by cost ceiling: {exc}",
                    )
                    await _finish_step(
                        session_factory, run_id, step_num, "error", cost_meter
                    )
                    break
                except Exception as exc:  # noqa: BLE001
                    final_status = TERMINAL_ERROR
                    error_text = f"{type(exc).__name__}: {exc}"
                    _logger.exception(
                        "Worker step %d for run %s raised", step_num, run_id
                    )
                    await run_logger.log(
                        "error", f"[step {step_num}] crashed: {error_text}"
                    )
                    await _finish_step(
                        session_factory, run_id, step_num, "error", cost_meter
                    )
                    break
                except BaseException as exc:
                    # KeyboardInterrupt / asyncio.CancelledError / SystemExit.
                    # Persist the run as 'error' on the way out, then re-raise
                    # so the caller (asyncio runner / signal handler) sees
                    # the cancellation it sent us. Without this, a worker
                    # killed by SIGTERM would record status='done' because
                    # final_status defaults to TERMINAL_OK.
                    final_status = TERMINAL_ERROR
                    error_text = (
                        f"Worker interrupted by {type(exc).__name__}"
                        + (f": {exc}" if str(exc) else "")
                    )
                    _logger.warning(
                        "Worker step %d for run %s interrupted: %s",
                        step_num, run_id, type(exc).__name__,
                    )
                    raise
                else:
                    await _finish_step(
                        session_factory, run_id, step_num, "done", cost_meter
                    )

            # If we fell out of the loop without setting a non-OK status, all
            # steps completed normally.
            await run_logger.log(
                "info", f"Worker exiting with status={final_status}"
            )
        finally:
            # Always best-effort flip the run's final status, even on
            # unexpected exit paths (incl. BaseException re-raises above).
            await _finalise_run(session_factory, run_id, final_status, error_text)

    return final_status


# ---- DB helpers ----------------------------------------------------------

async def _skip_step(
    session_factory: async_sessionmaker[AsyncSession],
    run_id: str,
    step_num: int,
) -> None:
    """Upsert a RunStep row with status='skipped'."""
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        existing = await session.get(RunStep, (run_id, step_num))
        if existing is None:
            session.add(
                RunStep(
                    run_id=run_id,
                    step_num=step_num,
                    status="skipped",
                    started_at=now,
                    finished_at=now,
                )
            )
        else:
            existing.status = "skipped"
            existing.started_at = now
            existing.finished_at = now
        await session.commit()


async def _step_already_done(
    session_factory: async_sessionmaker[AsyncSession],
    run_id: str,
    step_num: int,
) -> bool:
    async with session_factory() as session:
        status = await session.scalar(
            select(RunStep.status).where(
                RunStep.run_id == run_id, RunStep.step_num == step_num
            )
        )
    return status == "done"


async def _start_step(
    session_factory: async_sessionmaker[AsyncSession],
    run_id: str,
    step_num: int,
) -> None:
    now = datetime.now(timezone.utc)
    async with session_factory() as session:
        existing = await session.get(RunStep, (run_id, step_num))
        if existing is None:
            session.add(
                RunStep(
                    run_id=run_id,
                    step_num=step_num,
                    status="running",
                    started_at=now,
                )
            )
        else:
            existing.status = "running"
            existing.started_at = now
            existing.finished_at = None
        await session.commit()


async def _finish_step(
    session_factory: async_sessionmaker[AsyncSession],
    run_id: str,
    step_num: int,
    status: str,
    cost_meter: RunCostMeter,
) -> None:
    async with session_factory() as session:
        await session.execute(
            update(RunStep)
            .where(RunStep.run_id == run_id, RunStep.step_num == step_num)
            .values(
                status=status,
                finished_at=datetime.now(timezone.utc),
                token_usage_json=cost_meter.snapshot(),
            )
        )
        await session.commit()


async def _finalise_run(
    session_factory: async_sessionmaker[AsyncSession],
    run_id: str,
    status: str,
    error_text: Optional[str],
) -> None:
    async with session_factory() as session:
        await session.execute(
            update(Run)
            .where(Run.id == run_id)
            .values(
                status=status,
                finished_at=datetime.now(timezone.utc),
                error_text=error_text,
            )
        )
        await session.commit()
