"""Background run scheduler.

Plan section 3:
- Polls ``runs`` table for ``status='queued'`` rows.
- Enforces the team-wide concurrency cap (default 2 — see ``Settings.run_concurrency``).
- Atomically transitions ``queued → running`` and asks the configured
  :class:`TaskDispatcher` to spawn a worker.
- On dispatch failure, marks the run ``error`` so it doesn't sit forever.

The scheduler runs as a single asyncio task in the API process (started
in :func:`app.main.lifespan`). One instance per process is fine for the
2-5 user team this app targets — no leader-election, no Redis lock.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.runs import Run
from app.services.task_dispatcher import TaskDispatcher

_logger = logging.getLogger(__name__)


# Run statuses that count against the running-concurrency cap.
# Queued runs are unbounded — only actually-running runs consume a slot.
_RUNNING_STATUSES = ("running",)


class RunScheduler:
    """Single-instance scheduler driving worker dispatch.

    Usage::

        scheduler = RunScheduler(
            session_factory=session_factory,
            dispatcher=dispatcher,
            concurrency=2,
            poll_interval_s=2.0,
        )
        await scheduler.start()
        ...
        await scheduler.stop()

    Or via the contextmanager-style :meth:`run_in_background`.
    """

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        dispatcher: TaskDispatcher,
        concurrency: int = 2,
        poll_interval_s: float = 2.0,
    ) -> None:
        if concurrency < 1:
            raise ValueError("concurrency must be ≥ 1")
        self._session_factory = session_factory
        self._dispatcher = dispatcher
        self._concurrency = concurrency
        self._poll_interval = poll_interval_s
        self._task: Optional[asyncio.Task] = None
        self._stopped = asyncio.Event()
        # Test/diagnostic counters.
        self.tick_count = 0
        self.dispatch_count = 0

    # ---- lifecycle -------------------------------------------------------

    async def start(self) -> None:
        if self._task is not None:
            return
        self._stopped.clear()
        self._task = asyncio.create_task(self._loop(), name="run-scheduler")
        _logger.info(
            "RunScheduler started (concurrency=%d, poll=%.1fs, dispatcher=%s)",
            self._concurrency,
            self._poll_interval,
            type(self._dispatcher).__name__,
        )

    async def stop(self) -> None:
        self._stopped.set()
        if self._task is not None:
            try:
                await self._task
            except Exception:  # noqa: BLE001
                _logger.exception("RunScheduler loop crashed during shutdown")
            self._task = None
        _logger.info("RunScheduler stopped")

    # ---- core loop -------------------------------------------------------

    async def _loop(self) -> None:
        while not self._stopped.is_set():
            try:
                await self.tick()
            except Exception:  # noqa: BLE001
                _logger.exception("RunScheduler tick raised; continuing")
            try:
                await asyncio.wait_for(self._stopped.wait(), timeout=self._poll_interval)
            except asyncio.TimeoutError:
                continue

    async def tick(self) -> None:
        """One scheduler iteration. Public so tests can call it directly
        instead of waiting for the timer."""
        self.tick_count += 1

        slots = await self._available_slots()
        if slots <= 0:
            return

        for _ in range(slots):
            run_id = await self._claim_oldest_queued()
            if run_id is None:
                return  # nothing more to dispatch this tick
            await self._dispatch_claimed(run_id)

    # ---- atomic state transitions ---------------------------------------

    async def _available_slots(self) -> int:
        async with self._session_factory() as session:
            result = await session.execute(
                select(func.count())
                .select_from(Run)
                .where(Run.status.in_(_RUNNING_STATUSES))
            )
            running = result.scalar_one()
        return max(0, self._concurrency - running)

    async def _claim_oldest_queued(self) -> Optional[str]:
        """Transition the oldest queued run to 'running' and return its id.

        v1 runs a single scheduler instance per process and one process per
        environment, so we don't try to defend against concurrent claims of
        the same row. If we ever need to scale out the scheduler, swap this
        for a Postgres ``SELECT … FOR UPDATE SKIP LOCKED`` pattern.
        """
        async with self._session_factory() as session:
            result = await session.execute(
                select(Run)
                .where(Run.status == "queued")
                .order_by(Run.created_at.asc())
                .limit(1)
            )
            run = result.scalar_one_or_none()
            if run is None:
                return None
            run.status = "running"
            run.started_at = datetime.now(timezone.utc)
            await session.commit()
            return run.id

    async def _dispatch_claimed(self, run_id: str) -> None:
        try:
            task_arn = await self._dispatcher.dispatch(run_id)
        except Exception as exc:  # noqa: BLE001
            _logger.exception("Dispatcher failed for run %s; marking error", run_id)
            await self._mark_error(run_id, f"Dispatch failed: {exc}")
            return

        # Persist the task handle so cancellation / observability can find it.
        async with self._session_factory() as session:
            await session.execute(
                update(Run).where(Run.id == run_id).values(fargate_task_arn=task_arn)
            )
            await session.commit()
        self.dispatch_count += 1
        _logger.info("Dispatched run %s as task %s", run_id, task_arn)

    async def _mark_error(self, run_id: str, error_text: str) -> None:
        async with self._session_factory() as session:
            await session.execute(
                update(Run)
                .where(Run.id == run_id)
                .values(
                    status="error",
                    error_text=error_text,
                    finished_at=datetime.now(timezone.utc),
                )
            )
            await session.commit()
