"""Batched, durable per-run log writer.

Plan section 3: the worker appends rows to ``run_logs`` and the API tails
the table to stream them to the browser via SSE. Rows survive App Runner
restarts (durability) and arrive at the browser within ~200 ms (latency).

The writer is intentionally async because:
- We want to batch inserts to keep RDS round-trips low.
- The worker's main loop is async; logging is a fire-and-forget call.

Sync callers (the legacy pipeline code we run inside ``asyncio.to_thread``)
get a thin sync wrapper, ``RunLogger.log_sync``, that schedules onto the
owning event loop via ``run_coroutine_threadsafe``.
"""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import AsyncIterator

from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.runs import RunLog

_logger = logging.getLogger(__name__)


@dataclass
class _Pending:
    run_id: str
    ts: datetime
    level: str
    message: str


class RunLogger:
    """Per-run log writer. Owns a small in-memory queue and a background
    flush task; the caller never blocks on DB I/O.

    Lifecycle::

        async with RunLogger.attached(session_factory, run_id) as rl:
            await rl.log("info", "Starting run")
            ...
            await rl.log("info", "Step 3 complete")
        # context exit drains the buffer with a final flush

    The flush interval is configurable; default 200 ms gives the SSE
    consumer near-real-time updates without hammering the DB.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        run_id: str,
        *,
        flush_interval_s: float = 0.2,
        max_batch: int = 200,
    ) -> None:
        self._session_factory = session_factory
        self._run_id = run_id
        self._flush_interval = flush_interval_s
        self._max_batch = max_batch
        self._queue: asyncio.Queue[_Pending] = asyncio.Queue()
        self._flush_task: asyncio.Task | None = None
        self._stopped = asyncio.Event()
        self._loop: asyncio.AbstractEventLoop | None = None

    # ---- lifecycle -------------------------------------------------------

    @classmethod
    @asynccontextmanager
    async def attached(
        cls,
        session_factory: async_sessionmaker[AsyncSession],
        run_id: str,
        *,
        flush_interval_s: float = 0.2,
    ) -> AsyncIterator["RunLogger"]:
        """Build a RunLogger, run its flush loop for the lifetime of the
        context, drain on exit. The caller never sees a flush task object."""
        rl = cls(session_factory, run_id, flush_interval_s=flush_interval_s)
        await rl.start()
        try:
            yield rl
        finally:
            await rl.stop()

    async def start(self) -> None:
        if self._flush_task is not None:
            return
        self._loop = asyncio.get_running_loop()
        self._flush_task = asyncio.create_task(self._flush_loop(), name=f"run-logger-{self._run_id}")

    async def stop(self) -> None:
        self._stopped.set()
        if self._flush_task is not None:
            try:
                await self._flush_task
            except Exception:  # noqa: BLE001 - we want shutdown to be best-effort
                _logger.exception("RunLogger flush loop crashed during shutdown")
            self._flush_task = None
        # One last drain in case the loop exited before catching latecomers.
        await self._drain_once()

    # ---- public log API --------------------------------------------------

    async def log(self, level: str, message: str) -> None:
        """Queue one log line. Returns immediately; the actual DB write happens
        in the next flush tick (≤ flush_interval_s)."""
        await self._queue.put(
            _Pending(
                run_id=self._run_id,
                ts=datetime.now(timezone.utc),
                level=level,
                message=message,
            )
        )

    def log_sync(self, level: str, message: str) -> None:
        """Sync equivalent for code running in ``asyncio.to_thread``. Schedules
        the enqueue onto the owning event loop. Safe to call from any thread."""
        if self._loop is None:
            raise RuntimeError("RunLogger.start() has not been called yet")
        asyncio.run_coroutine_threadsafe(self.log(level, message), self._loop)

    # ---- internals -------------------------------------------------------

    async def _flush_loop(self) -> None:
        while not self._stopped.is_set():
            try:
                await asyncio.wait_for(
                    self._stopped.wait(), timeout=self._flush_interval
                )
            except asyncio.TimeoutError:
                pass  # interval elapsed → time to flush
            await self._drain_once()

    async def _drain_once(self) -> None:
        if self._queue.empty():
            return
        batch: list[_Pending] = []
        # Pull up to max_batch in one go.
        while not self._queue.empty() and len(batch) < self._max_batch:
            batch.append(self._queue.get_nowait())
        if not batch:
            return
        try:
            await self._write_batch(batch)
        except Exception:  # noqa: BLE001
            # We don't want a transient DB blip to take down the worker.
            # Logs are best-effort; surface to local logger and move on.
            _logger.exception(
                "RunLogger failed to write batch of %d log line(s) for run %s",
                len(batch),
                self._run_id,
            )

    async def _write_batch(self, batch: Sequence[_Pending]) -> None:
        rows = [
            RunLog(run_id=p.run_id, ts=p.ts, level=p.level, message=p.message)
            for p in batch
        ]
        async with self._session_factory() as session:
            session.add_all(rows)
            await session.commit()
