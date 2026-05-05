"""Integration tests for the SSE log-streaming endpoint.

Drives the streamer against an in-memory SQLite DB instead of unit-
mocking the queries, so the SQL is real and the encoder/parsing is
tested end-to-end.

We don't use FastAPI's ``TestClient`` here because StreamingResponse
under TestClient buffers the whole response — which would block on a
streamer that only ends when the run reaches a terminal status. Instead
we drive the async generator (`stream_logs`) directly, which is what
``StreamingResponse`` does under the hood.
"""

from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import AsyncIterator

import pytest

from app.models.runs import Run, RunLog
from app.services.log_streamer import _sse_event, stream_logs


# ---- helpers --------------------------------------------------------------

async def _seed_run(session_factory, run_id: str = "r-sse", status: str = "running") -> None:
    async with session_factory() as session:
        session.add(
            Run(
                id=run_id,
                status=status,
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()


async def _append_log(
    session_factory, run_id: str, level: str, message: str
) -> RunLog:
    async with session_factory() as session:
        row = RunLog(
            run_id=run_id,
            ts=datetime.now(timezone.utc),
            level=level,
            message=message,
        )
        session.add(row)
        await session.commit()
        return row


async def _set_status(session_factory, run_id: str, status: str) -> None:
    from sqlalchemy import update
    async with session_factory() as session:
        await session.execute(
            update(Run).where(Run.id == run_id).values(status=status)
        )
        await session.commit()


def _parse_sse_events(payload: bytes) -> list[dict]:
    """Decode an SSE wire format payload into a list of event dicts.

    Each dict has keys: ``id`` (optional), ``event``, ``data`` (already
    decoded JSON if the data field looked like JSON, else string).
    Comment lines are dropped.
    """
    text = payload.decode("utf-8")
    events: list[dict] = []
    current: dict = {}
    data_lines: list[str] = []
    for line in text.split("\n"):
        if line.startswith(":"):
            continue  # heartbeat / comment
        if line == "":
            if current or data_lines:
                if data_lines:
                    raw = "\n".join(data_lines)
                    try:
                        current["data"] = json.loads(raw)
                    except json.JSONDecodeError:
                        current["data"] = raw
                events.append(current)
                current = {}
                data_lines = []
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        value = value[1:] if value.startswith(" ") else value
        if key == "id":
            current["id"] = int(value)
        elif key == "event":
            current["event"] = value
        elif key == "data":
            data_lines.append(value)
    return events


async def _drain(stream: AsyncIterator[bytes]) -> bytes:
    """Read every chunk from an async generator into a single bytes blob."""
    chunks: list[bytes] = []
    async for chunk in stream:
        chunks.append(chunk)
    return b"".join(chunks)


# ---- happy path: pre-existing rows + terminal status close ---------------

@pytest.mark.asyncio
async def test_streams_pre_existing_rows_then_closes(async_session_factory) -> None:
    """If the run is already in a terminal status with rows in run_logs,
    the stream should yield each row as an event then a `complete` event."""
    await _seed_run(async_session_factory, "r1", status="running")
    await _append_log(async_session_factory, "r1", "info", "first")
    await _append_log(async_session_factory, "r1", "info", "second")
    await _set_status(async_session_factory, "r1", "done")

    payload = await _drain(stream_logs(
        session_factory=async_session_factory,
        run_id="r1",
        poll_interval_s=0.01,
    ))
    events = _parse_sse_events(payload)

    log_events = [e for e in events if e.get("event") == "log"]
    complete = [e for e in events if e.get("event") == "complete"]
    assert [e["data"]["message"] for e in log_events] == ["first", "second"]
    # Each log event has the row id as its SSE id (so Last-Event-ID works).
    assert all("id" in e for e in log_events)
    assert log_events[0]["id"] < log_events[1]["id"]
    assert len(complete) == 1
    assert complete[0]["data"]["status"] == "done"


# ---- reconnect: Last-Event-ID resumes after that row --------------------

@pytest.mark.asyncio
async def test_last_event_id_skips_already_seen_rows(async_session_factory) -> None:
    """Client reconnects with Last-Event-ID set to the highest id it saw.
    The stream should NOT replay rows up to and including that id."""
    await _seed_run(async_session_factory, "r2", status="running")
    row1 = await _append_log(async_session_factory, "r2", "info", "first")
    row2 = await _append_log(async_session_factory, "r2", "info", "second")
    row3 = await _append_log(async_session_factory, "r2", "info", "third")
    await _set_status(async_session_factory, "r2", "done")

    payload = await _drain(stream_logs(
        session_factory=async_session_factory,
        run_id="r2",
        last_event_id=row2.id,
        poll_interval_s=0.01,
    ))
    events = _parse_sse_events(payload)
    messages = [e["data"]["message"] for e in events if e.get("event") == "log"]
    # Should only see what came AFTER row2.
    assert messages == ["third"]


# ---- streaming: rows arriving during the connection are delivered --------

@pytest.mark.asyncio
async def test_rows_arriving_after_connect_are_streamed(async_session_factory) -> None:
    """Open the stream, append rows mid-flight, ensure they show up
    before the terminal close event."""
    await _seed_run(async_session_factory, "r3", status="running")
    # No rows yet.

    stream = stream_logs(
        session_factory=async_session_factory,
        run_id="r3",
        poll_interval_s=0.05,
    )

    collected: list[bytes] = []
    appender_done = asyncio.Event()

    async def appender() -> None:
        await asyncio.sleep(0.05)
        await _append_log(async_session_factory, "r3", "info", "live-1")
        await asyncio.sleep(0.05)
        await _append_log(async_session_factory, "r3", "info", "live-2")
        await asyncio.sleep(0.05)
        await _set_status(async_session_factory, "r3", "done")
        appender_done.set()

    appender_task = asyncio.create_task(appender())
    try:
        async for chunk in stream:
            collected.append(chunk)
    finally:
        await appender_task

    events = _parse_sse_events(b"".join(collected))
    log_events = [e for e in events if e.get("event") == "log"]
    assert [e["data"]["message"] for e in log_events] == ["live-1", "live-2"]
    assert any(e.get("event") == "complete" for e in events)


# ---- run not found ------------------------------------------------------

@pytest.mark.asyncio
async def test_unknown_run_id_emits_error_and_closes(async_session_factory) -> None:
    payload = await _drain(stream_logs(
        session_factory=async_session_factory,
        run_id="does-not-exist",
        poll_interval_s=0.01,
    ))
    events = _parse_sse_events(payload)
    assert any(e.get("event") == "error" for e in events)
    assert all(e.get("event") != "complete" for e in events)


# ---- encoder unit-level test --------------------------------------------

def test_sse_event_encodes_id_event_and_data() -> None:
    out = _sse_event(id=42, event="log", data='{"hello": "world"}')
    text = out.decode("utf-8")
    assert "id: 42" in text
    assert "event: log" in text
    assert 'data: {"hello": "world"}' in text
    # Two trailing newlines = end of event + blank-line separator.
    assert text.endswith("\n\n")


def test_sse_event_handles_multi_line_data() -> None:
    """``data:`` lines must be repeated for each newline in the payload."""
    out = _sse_event(event="log", data="line one\nline two")
    text = out.decode("utf-8")
    assert "data: line one" in text
    assert "data: line two" in text
