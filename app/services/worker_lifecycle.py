"""The lifecycle a Fargate worker runs through.

Plan section 3:

- The worker reads ``RUN_ID`` (and optional ``RESUME``, ``MAX_RUN_USD``)
  from env, looks up the corresponding ``runs`` row, and executes pipeline
  steps 1–6, appending to ``run_logs`` and updating ``run_steps``.
- It polls ``runs.status`` between steps so a ``cancel_requested`` from
  the API takes effect within ~1 step boundary.
- It honours the ``RunCostMeter`` ceiling, marking the run
  ``aborted_cost_ceiling`` if the next OpenAI call would push past the cap.

Today's scope (KNOW-2270): wire the lifecycle, the logger, the cost meter,
and the cancellation poll. The body of each step is a **stub** — actual
pipeline integration (rewiring ``pipeline/*`` modules to read inputs from
RDS/S3 and write outputs back) lands in a follow-up ticket. The stub is
real enough to drive the moving parts: it writes log lines, advances
``run_steps`` rows, and respects cancellation.
"""
from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone
from typing import Awaitable, Callable, Optional

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
    and check for cancellation without each step pulling its own session."""

    def __init__(
        self,
        *,
        run_id: str,
        logger: RunLogger,
        cost_meter: RunCostMeter,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self.run_id = run_id
        self.logger = logger
        self.cost_meter = cost_meter
        self._session_factory = session_factory

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
    """
    ceiling = max_run_usd if max_run_usd is not None else float(
        os.environ.get("MAX_RUN_USD", "50")
    )
    cost_meter = RunCostMeter(ceiling_usd=ceiling)
    final_status = TERMINAL_OK
    error_text: Optional[str] = None

    async with RunLogger.attached(
        session_factory, run_id, flush_interval_s=log_flush_interval_s
    ) as run_logger:
        ctx = WorkerContext(
            run_id=run_id,
            logger=run_logger,
            cost_meter=cost_meter,
            session_factory=session_factory,
        )
        await run_logger.log(
            "info",
            f"Worker started (run_id={run_id}, resume={resume}, ceiling=${ceiling:.2f})",
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

                if resume and await _step_already_done(session_factory, run_id, step_num):
                    await run_logger.log(
                        "info", f"[step {step_num}] resume: already done, skipping"
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
            # unexpected exit paths.
            await _finalise_run(session_factory, run_id, final_status, error_text)

    return final_status


# ---- DB helpers ----------------------------------------------------------

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
