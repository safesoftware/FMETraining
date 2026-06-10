"""Tests for the worker lifecycle.

Drives ``run_worker`` against in-memory SQLite with a custom step body so
each lifecycle branch (happy path, mid-run cancel, cost-ceiling abort,
crashing step, resume) can be exercised deterministically.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Awaitable, Callable

import pytest
from sqlalchemy import select

from app.models.runs import Run, RunLog, RunStep
from app.services.run_cost_meter import CostCeilingExceeded
from app.services.worker_lifecycle import (
    PIPELINE_STEPS,
    TERMINAL_CANCELLED,
    TERMINAL_COST_ABORTED,
    TERMINAL_ERROR,
    TERMINAL_OK,
    WorkerContext,
    run_worker,
)


async def _seed_run(
    session_factory,
    run_id: str = "r-test",
    status: str = "running",
    *,
    options: dict | None = None,
) -> None:
    async with session_factory() as session:
        session.add(
            Run(
                id=run_id,
                status=status,
                scope_json={},
                options_json=options or {},
                created_at=datetime.now(timezone.utc),
                started_at=datetime.now(timezone.utc) if status == "running" else None,
            )
        )
        await session.commit()


# ---- happy path ----------------------------------------------------------

@pytest.mark.asyncio
async def test_happy_path_runs_all_steps_and_marks_done(async_session_factory) -> None:
    await _seed_run(async_session_factory, "r-ok")

    async def quick_step(step_num: int, ctx: WorkerContext) -> None:
        await ctx.logger.log("info", f"step {step_num} body ran")

    final = await run_worker(
        "r-ok",
        session_factory=async_session_factory,
        max_run_usd=50.0,
        step_body=quick_step,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_OK

    async with async_session_factory() as session:
        run = await session.get(Run, "r-ok")
        steps = (
            await session.scalars(
                select(RunStep).where(RunStep.run_id == "r-ok").order_by(RunStep.step_num)
            )
        ).all()
        log_messages = [
            r.message
            for r in (
                await session.scalars(
                    select(RunLog).where(RunLog.run_id == "r-ok").order_by(RunLog.id)
                )
            ).all()
        ]
    assert run.status == TERMINAL_OK
    assert run.finished_at is not None
    assert len(steps) == len(PIPELINE_STEPS)
    assert all(s.status == "done" for s in steps)
    # Sanity: at least one log line landed for each step + the lifecycle messages.
    assert any("Worker started" in m for m in log_messages)
    assert any("step 1 body ran" in m for m in log_messages)
    assert any("step 6 body ran" in m for m in log_messages)
    assert any("Worker exiting with status=done" in m for m in log_messages)


# ---- cancellation between steps -----------------------------------------

@pytest.mark.asyncio
async def test_cancel_requested_between_steps(async_session_factory) -> None:
    """If the API flips runs.status to 'cancel_requested', the next step
    boundary should observe it, log the cancel, and exit cleanly."""
    await _seed_run(async_session_factory, "r-cancel")

    cancelled_after = 2  # request cancel just after step 2 finishes

    async def step_then_request_cancel(step_num: int, ctx: WorkerContext) -> None:
        await ctx.logger.log("info", f"step {step_num} body")
        if step_num == cancelled_after:
            # Simulate the API telling the worker to bail.
            from sqlalchemy import update as sqla_update
            async with async_session_factory() as session:
                await session.execute(
                    sqla_update(Run)
                    .where(Run.id == "r-cancel")
                    .values(status="cancel_requested")
                )
                await session.commit()

    final = await run_worker(
        "r-cancel",
        session_factory=async_session_factory,
        step_body=step_then_request_cancel,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_CANCELLED
    async with async_session_factory() as session:
        run = await session.get(Run, "r-cancel")
        steps = (
            await session.scalars(
                select(RunStep).where(RunStep.run_id == "r-cancel").order_by(RunStep.step_num)
            )
        ).all()
    assert run.status == TERMINAL_CANCELLED
    # Steps 1 and 2 should have completed; step 3 should not have started.
    by_step = {s.step_num: s.status for s in steps}
    assert by_step.get(1) == "done"
    assert by_step.get(2) == "done"
    assert 3 not in by_step  # never even created


# ---- cost ceiling abort --------------------------------------------------

@pytest.mark.asyncio
async def test_cost_ceiling_abort(async_session_factory) -> None:
    """A step body that raises CostCeilingExceeded triggers TERMINAL_COST_ABORTED."""
    await _seed_run(async_session_factory, "r-cost")

    async def explode_on_step_3(step_num: int, ctx: WorkerContext) -> None:
        if step_num == 3:
            raise CostCeilingExceeded("Projected $51 exceeds ceiling $50")

    final = await run_worker(
        "r-cost",
        session_factory=async_session_factory,
        step_body=explode_on_step_3,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_COST_ABORTED
    async with async_session_factory() as session:
        run = await session.get(Run, "r-cost")
    assert run.status == TERMINAL_COST_ABORTED
    assert "Projected $51" in (run.error_text or "")


# ---- crashing step ------------------------------------------------------

@pytest.mark.asyncio
async def test_step_exception_marks_run_error(async_session_factory) -> None:
    # NOTE: step 4 is a lifecycle no-op (confirmation step for 3+4 unit) when
    # step 3 is in requested_steps, so the step_body is not called for step 4.
    # Use step 5 here so the crash actually reaches the step_body.
    await _seed_run(async_session_factory, "r-err")

    async def crash_on_step_5(step_num: int, ctx: WorkerContext) -> None:
        if step_num == 5:
            raise RuntimeError("kaboom")

    final = await run_worker(
        "r-err",
        session_factory=async_session_factory,
        step_body=crash_on_step_5,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_ERROR
    async with async_session_factory() as session:
        run = await session.get(Run, "r-err")
    assert run.status == TERMINAL_ERROR
    assert "RuntimeError" in (run.error_text or "")
    assert "kaboom" in (run.error_text or "")


# ---- resume mode --------------------------------------------------------

@pytest.mark.asyncio
async def test_resume_skips_already_done_steps(async_session_factory) -> None:
    """If RESUME=true and steps 1+2 are already 'done', they should be
    skipped — only the unfinished tail runs."""
    run_id = "r-resume"
    await _seed_run(async_session_factory, run_id)
    # Pre-populate completed steps 1 and 2.
    async with async_session_factory() as session:
        for step_num in (1, 2):
            session.add(
                RunStep(
                    run_id=run_id,
                    step_num=step_num,
                    status="done",
                    started_at=datetime.now(timezone.utc),
                    finished_at=datetime.now(timezone.utc),
                )
            )
        await session.commit()

    executed: list[int] = []

    async def record_step(step_num: int, ctx: WorkerContext) -> None:
        executed.append(step_num)

    final = await run_worker(
        run_id,
        session_factory=async_session_factory,
        resume=True,
        step_body=record_step,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_OK
    # Steps 1 and 2 were already done. Step 3, 5 and 6 run via step_body; step 4
    # is the assessment-confirmation no-op (KNOW-2334 — step 3+4 are a unit),
    # marked done inline WITHOUT calling step_body, so it is absent from `executed`.
    assert executed == [3, 5, 6]
    async with async_session_factory() as session:
        step4 = await session.get(RunStep, (run_id, 4))
        assert step4 is not None and step4.status == "done"


# ---- step body type signature -------------------------------------------

def test_step_body_signature_is_callable() -> None:
    """Sanity check the type alias resolves to an awaitable-returning callable."""
    async def _example(step_num: int, ctx: WorkerContext) -> None:
        return None

    body: Callable[[int, WorkerContext], Awaitable[None]] = _example
    assert body is _example
