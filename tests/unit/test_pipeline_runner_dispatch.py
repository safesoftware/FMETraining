"""Unit tests for ``app.services.pipeline_runner`` (KNOW-2334).

Covers:
- ``_parse_requested_steps``: step-subset parsing from ``options["steps"]``
- Step-skip handling in the lifecycle: steps not in requested_steps →
  RunStep.status == 'skipped'
- Steps 3+4 unit: step 3 runs the body; step 4 is a no-op confirmation
- The stdout→log_sync bridge (_LogSink)
- WorkerContext.requested_steps default and custom values

All tests use the SQLite in-memory fixture and custom step bodies so no
real pipeline code (and no OpenAI/Jira calls) are involved.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select

from app.models.runs import Run, RunStep
from app.services.pipeline_runner import _LogSink, make_step_body
from app.services.worker_lifecycle import (
    PIPELINE_STEPS,
    TERMINAL_OK,
    WorkerContext,
    _parse_requested_steps,
    run_worker,
)


# ---------------------------------------------------------------------------
# _parse_requested_steps
# ---------------------------------------------------------------------------


class TestParseRequestedSteps:
    def test_empty_options_returns_all_steps(self) -> None:
        result = _parse_requested_steps({})
        assert result == frozenset(PIPELINE_STEPS)

    def test_none_steps_returns_all(self) -> None:
        result = _parse_requested_steps({"steps": None})
        assert result == frozenset(PIPELINE_STEPS)

    def test_comma_separated(self) -> None:
        result = _parse_requested_steps({"steps": "1,2"})
        assert result == frozenset({1, 2})

    def test_range_syntax(self) -> None:
        result = _parse_requested_steps({"steps": "1-3"})
        assert result == frozenset({1, 2, 3})

    def test_mixed_comma_and_range(self) -> None:
        result = _parse_requested_steps({"steps": "1,2,5-6"})
        assert result == frozenset({1, 2, 5, 6})

    def test_out_of_range_steps_excluded(self) -> None:
        # Step 99 is not in PIPELINE_STEPS
        result = _parse_requested_steps({"steps": "1,2,99"})
        assert 99 not in result
        assert 1 in result

    def test_garbage_steps_falls_back_to_all(self) -> None:
        # All tokens invalid → falls back to all steps
        result = _parse_requested_steps({"steps": "abc,xyz"})
        assert result == frozenset(PIPELINE_STEPS)

    def test_single_step(self) -> None:
        result = _parse_requested_steps({"steps": "1"})
        assert result == frozenset({1})


# ---------------------------------------------------------------------------
# _LogSink — stdout → log_sync bridge
# ---------------------------------------------------------------------------


class TestLogSink:
    def test_complete_lines_are_forwarded(self) -> None:
        captured: list[tuple[str, str]] = []

        class _FakeLogger:
            def log_sync(self, level: str, message: str) -> None:
                captured.append((level, message))

        sink = _LogSink(_FakeLogger(), level="info")
        sink.write("hello\nworld\n")

        assert ("info", "hello") in captured
        assert ("info", "world") in captured

    def test_partial_line_held_until_flush(self) -> None:
        captured: list[str] = []

        class _FakeLogger:
            def log_sync(self, level: str, message: str) -> None:
                captured.append(message)

        sink = _LogSink(_FakeLogger())
        sink.write("partial line without newline")
        assert captured == []  # not flushed yet
        sink.flush()
        assert "partial line without newline" in captured

    def test_empty_lines_are_skipped(self) -> None:
        captured: list[str] = []

        class _FakeLogger:
            def log_sync(self, level: str, message: str) -> None:
                captured.append(message)

        sink = _LogSink(_FakeLogger())
        sink.write("\n\n\n")
        assert captured == []  # blank lines suppressed

    def test_write_returns_length(self) -> None:
        class _FakeLogger:
            def log_sync(self, level: str, message: str) -> None:
                pass

        sink = _LogSink(_FakeLogger())
        assert sink.write("hello\n") == 6


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_run(
    session_factory,
    run_id: str,
    *,
    scope: dict | None = None,
    options: dict | None = None,
    to_version: str = "2026.1",
    status: str = "running",
) -> None:
    async with session_factory() as session:
        session.add(
            Run(
                id=run_id,
                status=status,
                to_version=to_version,
                scope_json=scope or {},
                options_json=options or {},
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()


# ---------------------------------------------------------------------------
# Step-skip handling via run_worker
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_step_skip_marks_skipped_in_db(async_session_factory) -> None:
    """Steps not in requested_steps should be marked 'skipped' in run_steps."""
    run_id = "r-skip-test"
    await _seed_run(
        async_session_factory,
        run_id,
        options={"steps": "1,2"},  # only steps 1 and 2
    )

    ran: list[int] = []

    async def _body(step_num: int, ctx: WorkerContext) -> None:
        ran.append(step_num)

    final = await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=_body,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_OK
    assert ran == [1, 2]  # only requested steps ran

    async with async_session_factory() as session:
        steps = (
            await session.scalars(
                select(RunStep)
                .where(RunStep.run_id == run_id)
                .order_by(RunStep.step_num)
            )
        ).all()

    by_step = {s.step_num: s.status for s in steps}
    assert by_step[1] == "done"
    assert by_step[2] == "done"
    # Steps 3–6 not requested → skipped
    for s in (3, 4, 5, 6):
        assert by_step.get(s) == "skipped", f"step {s} should be skipped, got {by_step.get(s)!r}"


@pytest.mark.asyncio
async def test_step_4_is_noop_when_step_3_requested(async_session_factory) -> None:
    """When steps 3+4 are both requested, step 3 runs via step_body and step 4
    is a confirmation no-op (step_body is NOT called for step 4)."""
    run_id = "r-3-4-unit"
    await _seed_run(
        async_session_factory,
        run_id,
        options={"steps": "3,4"},
    )

    ran: list[int] = []

    async def _body(step_num: int, ctx: WorkerContext) -> None:
        ran.append(step_num)

    final = await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=_body,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_OK
    # step_body called only for step 3; step 4 is handled internally
    assert ran == [3]

    async with async_session_factory() as session:
        steps = (
            await session.scalars(
                select(RunStep)
                .where(RunStep.run_id == run_id)
                .order_by(RunStep.step_num)
            )
        ).all()

    by_step = {s.step_num: s.status for s in steps}
    # Both steps 1, 2, 5, 6 skipped; 3 done (ran body); 4 done (no-op)
    for s in (1, 2, 5, 6):
        assert by_step.get(s) == "skipped"
    assert by_step[3] == "done"
    assert by_step[4] == "done"


@pytest.mark.asyncio
async def test_worker_context_requested_steps_attached(async_session_factory) -> None:
    """WorkerContext.requested_steps should reflect options["steps"]."""
    run_id = "r-ctx-steps"
    await _seed_run(
        async_session_factory,
        run_id,
        options={"steps": "1,2"},
    )

    observed_ctx: list[WorkerContext] = []

    async def _capture(step_num: int, ctx: WorkerContext) -> None:
        observed_ctx.append(ctx)

    await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=_capture,
        log_flush_interval_s=0.05,
    )

    assert len(observed_ctx) == 2  # only steps 1 and 2 ran
    ctx = observed_ctx[0]
    assert ctx.requested_steps == frozenset({1, 2})
    assert ctx.to_version == "2026.1"
    assert isinstance(ctx.scratch, dict)


@pytest.mark.asyncio
async def test_worker_context_scratch_shared_across_steps(async_session_factory) -> None:
    """ctx.scratch should be the same dict object across all step body calls."""
    run_id = "r-scratch"
    await _seed_run(
        async_session_factory,
        run_id,
        options={"steps": "1,2"},
    )

    seen_ids: list[int] = []

    async def _body(step_num: int, ctx: WorkerContext) -> None:
        if step_num == 1:
            ctx.scratch["token"] = "shared"
        if step_num == 2:
            seen_ids.append(1 if ctx.scratch.get("token") == "shared" else 0)

    await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=_body,
        log_flush_interval_s=0.05,
    )

    assert seen_ids == [1], "ctx.scratch written in step 1 must be visible in step 2"


# ---------------------------------------------------------------------------
# make_step_body smoke: steps 3–6 return without error
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_make_step_body_steps_3_to_6_are_no_ops(
    async_session_factory, tmp_path
) -> None:
    """Steps 3–6 log 'not yet integrated' and return — they must not crash."""
    run_id = "r-nyi"
    await _seed_run(
        async_session_factory,
        run_id,
        options={"steps": "3,4,5,6"},
    )

    # Use make_step_body with tmp_path as artifacts_root so the dir exists.
    step_body = make_step_body(
        artifacts_root=str(tmp_path / "artifacts"),
        lesson_content_root=str(tmp_path),
    )

    # Override step 4 handling: step 4 is a no-op already in lifecycle.
    # The body should only be called for step 3, 5, 6.
    called: list[int] = []
    original_body = step_body

    async def _tracking_body(step_num: int, ctx: WorkerContext) -> None:
        called.append(step_num)
        await original_body(step_num, ctx)

    final = await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=_tracking_body,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_OK
    # step_body called for 3, 5, 6 (4 is no-op in lifecycle)
    assert set(called) == {3, 5, 6}
