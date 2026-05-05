"""Unit tests for RunScheduler.

The scheduler enforces the team-wide concurrency cap, atomically claims
queued runs, and dispatches via a ``TaskDispatcher``. Tests use a real
async SQLite + a ``StubTaskDispatcher`` so the queueing / claim logic
gets exercised without needing Postgres or a live worker.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select

from app.models.runs import Run
from app.services.run_scheduler import RunScheduler
from app.services.task_dispatcher import StubTaskDispatcher


def _seed_run(
    *, id: str, status: str = "queued", created_at: datetime | None = None
) -> Run:
    return Run(
        id=id,
        status=status,
        created_at=created_at or datetime.now(timezone.utc),
    )


async def _insert(session_factory, *runs: Run) -> None:
    async with session_factory() as session:
        session.add_all(runs)
        await session.commit()


# ---- happy path: dispatches up to the concurrency cap --------------------

@pytest.mark.asyncio
async def test_tick_dispatches_queued_runs_up_to_cap(async_session_factory) -> None:
    base = datetime.now(timezone.utc)
    await _insert(
        async_session_factory,
        _seed_run(id="r1", created_at=base),
        _seed_run(id="r2", created_at=base + timedelta(seconds=1)),
        _seed_run(id="r3", created_at=base + timedelta(seconds=2)),
    )
    dispatcher = StubTaskDispatcher()
    scheduler = RunScheduler(
        session_factory=async_session_factory,
        dispatcher=dispatcher,
        concurrency=2,
    )

    await scheduler.tick()

    # Cap is 2 → only the two oldest get dispatched, third stays queued.
    assert dispatcher.dispatched == ["r1", "r2"]
    async with async_session_factory() as session:
        statuses = {
            r.id: r.status
            for r in (await session.scalars(select(Run))).all()
        }
    assert statuses == {"r1": "running", "r2": "running", "r3": "queued"}


# ---- claim atomicity: a run already 'running' counts against cap ----------

@pytest.mark.asyncio
async def test_running_runs_count_against_cap(async_session_factory) -> None:
    """If 1 run is already 'running' and cap is 2, only 1 new dispatch fires."""
    base = datetime.now(timezone.utc)
    await _insert(
        async_session_factory,
        _seed_run(id="r-running", status="running", created_at=base),
        _seed_run(id="r-q1", created_at=base + timedelta(seconds=1)),
        _seed_run(id="r-q2", created_at=base + timedelta(seconds=2)),
    )
    dispatcher = StubTaskDispatcher()
    scheduler = RunScheduler(
        session_factory=async_session_factory,
        dispatcher=dispatcher,
        concurrency=2,
    )
    await scheduler.tick()

    assert dispatcher.dispatched == ["r-q1"]


# ---- terminal statuses don't count ---------------------------------------

@pytest.mark.asyncio
async def test_done_and_error_runs_dont_block_dispatch(async_session_factory) -> None:
    base = datetime.now(timezone.utc)
    await _insert(
        async_session_factory,
        _seed_run(id="r-done", status="done", created_at=base),
        _seed_run(id="r-err", status="error", created_at=base),
        _seed_run(id="r-cancelled", status="cancelled", created_at=base),
        _seed_run(id="r-q1", created_at=base + timedelta(seconds=10)),
    )
    dispatcher = StubTaskDispatcher()
    scheduler = RunScheduler(
        session_factory=async_session_factory,
        dispatcher=dispatcher,
        concurrency=2,
    )
    await scheduler.tick()
    assert dispatcher.dispatched == ["r-q1"]


# ---- ordering: oldest first ----------------------------------------------

@pytest.mark.asyncio
async def test_oldest_queued_run_dispatches_first(async_session_factory) -> None:
    base = datetime.now(timezone.utc)
    await _insert(
        async_session_factory,
        _seed_run(id="newer", created_at=base + timedelta(seconds=10)),
        _seed_run(id="older", created_at=base),
        _seed_run(id="middle", created_at=base + timedelta(seconds=5)),
    )
    dispatcher = StubTaskDispatcher()
    scheduler = RunScheduler(
        session_factory=async_session_factory,
        dispatcher=dispatcher,
        concurrency=1,
    )
    await scheduler.tick()
    assert dispatcher.dispatched == ["older"]


# ---- dispatcher failure -> error status ----------------------------------

class _FailingDispatcher(StubTaskDispatcher):
    async def dispatch(self, run_id: str) -> str:
        raise RuntimeError("ECS rejected the task")


@pytest.mark.asyncio
async def test_dispatcher_failure_marks_run_error(async_session_factory) -> None:
    await _insert(async_session_factory, _seed_run(id="r-fail"))
    scheduler = RunScheduler(
        session_factory=async_session_factory,
        dispatcher=_FailingDispatcher(),
        concurrency=2,
    )
    await scheduler.tick()
    async with async_session_factory() as session:
        run = await session.get(Run, "r-fail")
    assert run.status == "error"
    assert "ECS rejected the task" in (run.error_text or "")
    assert run.finished_at is not None


# ---- task ARN persistence ------------------------------------------------

@pytest.mark.asyncio
async def test_task_arn_is_persisted(async_session_factory) -> None:
    await _insert(async_session_factory, _seed_run(id="r-arn"))
    dispatcher = StubTaskDispatcher()
    scheduler = RunScheduler(
        session_factory=async_session_factory,
        dispatcher=dispatcher,
        concurrency=1,
    )
    await scheduler.tick()
    async with async_session_factory() as session:
        run = await session.get(Run, "r-arn")
    assert run.fargate_task_arn == "stub:r-arn"
    assert run.status == "running"


# ---- nothing to do -> noop ----------------------------------------------

@pytest.mark.asyncio
async def test_tick_with_no_queued_runs_is_noop(async_session_factory) -> None:
    dispatcher = StubTaskDispatcher()
    scheduler = RunScheduler(
        session_factory=async_session_factory,
        dispatcher=dispatcher,
        concurrency=2,
    )
    await scheduler.tick()
    assert dispatcher.dispatched == []
    assert scheduler.tick_count == 1
    assert scheduler.dispatch_count == 0


# ---- start/stop lifecycle ------------------------------------------------

@pytest.mark.asyncio
async def test_start_then_stop_is_clean(async_session_factory) -> None:
    """The background loop should start, run a few ticks, and stop without raising."""
    dispatcher = StubTaskDispatcher()
    scheduler = RunScheduler(
        session_factory=async_session_factory,
        dispatcher=dispatcher,
        concurrency=2,
        poll_interval_s=0.05,
    )
    await scheduler.start()
    # Let the loop tick at least once.
    import asyncio
    await asyncio.sleep(0.15)
    await scheduler.stop()
    assert scheduler.tick_count >= 1
