"""Tail ``run_logs`` rows and yield them as Server-Sent Events.

Plan section 3:

    GET /api/runs/{id}/logs/stream  (SSE; tails run_logs WHERE id > last_seen)

The browser opens an ``EventSource`` against this stream; the worker
appends rows to ``run_logs`` (see :class:`app.services.run_logger.RunLogger`);
this module reads them out and re-emits as SSE events.

Why polling instead of LISTEN/NOTIFY: polling at 500 ms is cheap on a
single-instance deployment, the table is tiny, and it works equally
well against Postgres or the in-memory SQLite that tests use. We can
swap to LISTEN/NOTIFY in a follow-up if the team grows past 5 users.

Reconnect support: clients reconnecting after a dropped connection send
``Last-Event-ID`` in the request headers. Pass that as ``last_event_id``
to :func:`stream_logs` and we resume from the row after that id.
"""
from __future__ import annotations

import asyncio
import json
import logging
from typing import AsyncIterator, Iterable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models.runs import Run, RunLog

_logger = logging.getLogger(__name__)

# Run statuses that mean "no more rows will arrive". Once we observe one
# AND the queue is empty, the streamer closes.
_TERMINAL_STATUSES = frozenset(
    ("done", "cancelled", "error", "aborted_cost_ceiling")
)

# How often to query for new rows when the run is still active.
DEFAULT_POLL_INTERVAL_S = 0.5

# How often to send a heartbeat comment so intermediaries don't time out
# the connection (Nginx default proxy_read_timeout is 60s; App Runner /
# ALB are similar).
DEFAULT_HEARTBEAT_INTERVAL_S = 15.0

# Hard cap so a runaway connection doesn't hold a worker forever even
# if the run never reaches a terminal status (e.g. a forgotten browser
# tab against a crashed worker).
DEFAULT_MAX_DURATION_S = 6 * 60 * 60  # 6 hours — comfortably longer than any real run


# ---------------------------------------------------------------------------
# SSE encoding
# ---------------------------------------------------------------------------

def _sse_event(*, event: str, data: str, id: Optional[int] = None) -> bytes:
    """Encode one SSE event. Returns bytes ready to write to the wire.

    The newline conventions are part of the protocol: each field on its
    own line, blank line ends the event.
    """
    parts: list[str] = []
    if id is not None:
        parts.append(f"id: {id}")
    parts.append(f"event: {event}")
    # data: lines must not contain raw newlines — split if needed.
    for line in data.split("\n"):
        parts.append(f"data: {line}")
    parts.append("")  # terminator
    parts.append("")  # blank line between events
    return ("\n".join(parts)).encode("utf-8")


def _sse_comment(text: str) -> bytes:
    """Heartbeat comment. Lines starting with ':' are ignored by the
    EventSource parser but keep the connection alive."""
    return f": {text}\n\n".encode("utf-8")


# ---------------------------------------------------------------------------
# Streamer
# ---------------------------------------------------------------------------

async def stream_logs(
    *,
    session_factory: async_sessionmaker[AsyncSession],
    run_id: str,
    last_event_id: Optional[int] = None,
    poll_interval_s: float = DEFAULT_POLL_INTERVAL_S,
    heartbeat_interval_s: float = DEFAULT_HEARTBEAT_INTERVAL_S,
    max_duration_s: float = DEFAULT_MAX_DURATION_S,
) -> AsyncIterator[bytes]:
    """Yield SSE-encoded bytes for the given ``run_id``.

    Behaviour:
    - First yield: every ``run_logs`` row with id > ``last_event_id``.
      ``last_event_id`` defaults to 0 (yield everything).
    - Then a polling loop: every ``poll_interval_s`` seconds, query for
      new rows. Yield each as an ``event: log`` SSE event with the row's
      ``id`` as the SSE id (so the client's ``Last-Event-ID`` works).
    - Heartbeat: every ``heartbeat_interval_s`` seconds, yield a comment
      line so the connection stays alive through proxies.
    - Termination: when the run's ``status`` is terminal AND no new rows
      have arrived in the last poll, yield a final ``event: complete``
      SSE event and stop.
    - Hard cap: stop after ``max_duration_s`` regardless.

    Yields raw ``bytes`` because that's what FastAPI's ``StreamingResponse``
    wants. The encoding is UTF-8.
    """
    # Treat negative or out-of-band ids as "start from the beginning" — a
    # malformed Last-Event-ID (e.g. a negative integer from a buggy client)
    # would otherwise cause `WHERE id > -1`, replaying the entire log.
    cursor = last_event_id if (last_event_id is not None and last_event_id >= 0) else 0
    started_at = asyncio.get_event_loop().time()
    last_heartbeat_at = started_at

    # Tell the client we're alive even before any rows are ready.
    yield _sse_comment("connected")

    try:
        while True:
            # 1. Drain any rows newer than the cursor.
            new_rows = await _fetch_rows(
                session_factory, run_id, cursor, limit=_FETCH_BATCH
            )
            for row in new_rows:
                yield _sse_event(
                    id=row["id"],
                    event="log",
                    data=json.dumps({
                        "id": row["id"],
                        "ts": row["ts"],
                        "level": row["level"],
                        "message": row["message"],
                    }),
                )
                cursor = row["id"]

            # If we filled the batch, more rows may be waiting — drain
            # immediately without sleeping (and don't treat a full batch as
            # "caught up" for the terminal-status check below).
            if len(new_rows) >= _FETCH_BATCH:
                continue

            # 2. Check if we should stop. Terminal status AND no new rows
            #    means the run is done and we've delivered everything.
            if not new_rows:
                run_status = await _fetch_run_status(session_factory, run_id)
                if run_status in _TERMINAL_STATUSES:
                    yield _sse_event(
                        event="complete",
                        data=json.dumps({"run_id": run_id, "status": run_status}),
                    )
                    return
                if run_status is None:
                    # Run row doesn't exist — surface and stop.
                    yield _sse_event(
                        event="error",
                        data=json.dumps({"error": "run not found", "run_id": run_id}),
                    )
                    return

            # 3. Hard cap.
            now = asyncio.get_running_loop().time()
            if now - started_at > max_duration_s:
                yield _sse_event(
                    event="error",
                    data=json.dumps({
                        "error": "stream max-duration reached",
                        "run_id": run_id,
                    }),
                )
                return

            # 4. Heartbeat if we haven't sent one in a while.
            if now - last_heartbeat_at >= heartbeat_interval_s:
                yield _sse_comment("heartbeat")
                last_heartbeat_at = now

            # 5. Wait, then loop.
            await asyncio.sleep(poll_interval_s)
    except asyncio.CancelledError:
        # FastAPI's StreamingResponse throws this into the generator when
        # the client disconnects. Log it once so we have visibility into
        # how many streams die mid-flight, then re-raise so FastAPI knows
        # the generator is done and can release its resources.
        _logger.info(
            "SSE stream cancelled (client disconnect) for run %s at cursor %s",
            run_id, cursor,
        )
        raise
    finally:
        _logger.debug(
            "SSE stream exiting for run %s (final cursor=%s)", run_id, cursor
        )


# ---------------------------------------------------------------------------
# DB helpers — broken out so tests can stub them
# ---------------------------------------------------------------------------

# Cap rows pulled per poll so a reconnect against a long run (or a big
# backlog) can't load the entire run_logs history into memory at once. The
# stream loop drains successive full batches without sleeping.
_FETCH_BATCH = 500


async def _fetch_rows(
    session_factory: async_sessionmaker[AsyncSession],
    run_id: str,
    cursor_id: int,
    limit: int = _FETCH_BATCH,
) -> Iterable[dict]:
    async with session_factory() as session:
        result = await session.execute(
            select(RunLog)
            .where(RunLog.run_id == run_id, RunLog.id > cursor_id)
            .order_by(RunLog.id.asc())
            .limit(limit)
        )
        return [
            {
                "id": r.id,
                "ts": r.ts.isoformat() if r.ts else None,
                "level": r.level,
                "message": r.message,
            }
            for r in result.scalars().all()
        ]


async def _fetch_run_status(
    session_factory: async_sessionmaker[AsyncSession],
    run_id: str,
) -> Optional[str]:
    async with session_factory() as session:
        return await session.scalar(select(Run.status).where(Run.id == run_id))
