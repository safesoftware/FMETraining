"""Tests for RunLogger.

The flush loop is a finicky piece — it has its own asyncio task and an
event-driven shutdown path that's easy to break in a refactor. The
shutdown test here locks in the contract that lines queued right at
``stop()`` time still land in the database.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.models.runs import Run, RunLog
from app.services.run_logger import RunLogger


async def _seed_run(session_factory, run_id: str = "r-log") -> None:
    async with session_factory() as session:
        session.add(
            Run(
                id=run_id,
                status="running",
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()


# ---- happy path ----------------------------------------------------------

@pytest.mark.asyncio
async def test_log_lines_land_in_run_logs(async_session_factory) -> None:
    await _seed_run(async_session_factory)

    async with RunLogger.attached(
        async_session_factory, "r-log", flush_interval_s=0.05
    ) as rl:
        await rl.log("info", "first")
        await rl.log("info", "second")
        # Wait one flush cycle.
        await asyncio.sleep(0.1)

    async with async_session_factory() as session:
        rows = (
            await session.scalars(
                select(RunLog).where(RunLog.run_id == "r-log").order_by(RunLog.id)
            )
        ).all()
    messages = [r.message for r in rows]
    assert messages == ["first", "second"]


# ---- shutdown drain ------------------------------------------------------

@pytest.mark.asyncio
async def test_lines_queued_just_before_stop_are_not_lost(async_session_factory) -> None:
    """Reviewer flag: the flush loop's shutdown timing was correct but
    fragile. This test locks it in: lines queued during a flush window are
    persisted before stop() returns."""
    await _seed_run(async_session_factory, "r-shutdown")

    rl = RunLogger(
        async_session_factory,
        "r-shutdown",
        flush_interval_s=0.5,  # long interval, so we know shutdown drains, not the timer
    )
    await rl.start()

    # Queue lines back-to-back.
    for i in range(5):
        await rl.log("info", f"line-{i}")

    # stop() should drain everything before returning, not wait for the timer.
    await rl.stop()

    async with async_session_factory() as session:
        rows = (
            await session.scalars(
                select(RunLog).where(RunLog.run_id == "r-shutdown").order_by(RunLog.id)
            )
        ).all()
    assert [r.message for r in rows] == [f"line-{i}" for i in range(5)]


# ---- log_sync from a worker thread ---------------------------------------

@pytest.mark.asyncio
async def test_log_sync_from_thread(async_session_factory) -> None:
    """The legacy pipeline is sync — its calls into RunLogger come from a
    thread via ``asyncio.to_thread``. ``log_sync`` must successfully
    schedule onto the owning event loop."""
    await _seed_run(async_session_factory, "r-sync")

    async with RunLogger.attached(
        async_session_factory, "r-sync", flush_interval_s=0.05
    ) as rl:
        def from_thread() -> None:
            rl.log_sync("info", "from-thread")

        await asyncio.to_thread(from_thread)
        await asyncio.sleep(0.15)  # let the schedule round-trip + flush

    async with async_session_factory() as session:
        rows = (
            await session.scalars(
                select(RunLog).where(RunLog.run_id == "r-sync")
            )
        ).all()
    assert any("from-thread" in r.message for r in rows)


def test_log_sync_before_start_raises(async_session_factory) -> None:
    """``log_sync`` needs the owning loop reference, which only exists
    after ``start()``. Calling it earlier should fail loudly, not silently."""
    rl = RunLogger(async_session_factory, "r-x")
    with pytest.raises(RuntimeError, match="start"):
        rl.log_sync("info", "no loop yet")
