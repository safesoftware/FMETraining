"""Service-layer tests for ``app.services.report_drafts``. KNOW-2276."""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models import Run
from app.services import report_drafts as svc


pytestmark = pytest.mark.asyncio


async def _seed_run(
    session: AsyncSession,
    run_id: str = "20260505T120000-aaaa",
    *,
    to_version: str = "2026.1",
) -> Run:
    run = Run(id=run_id, status="done", to_version=to_version)
    session.add(run)
    await session.flush()
    return run


async def test_upsert_sanitizes_body_html_on_write(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Stage-6 security fix: a stored XSS payload in body_html must be
    stripped before it is persisted, so it can never reach another user's
    browser via the report's innerHTML re-render."""
    async with async_session_factory() as session:
        await _seed_run(session)
        row = await svc.upsert_draft(
            session,
            run_id="20260505T120000-aaaa",
            lesson_dir="lp/course/lesson",
            decisions={},
            body_html='<p>ok</p><img src="x" onerror="alert(document.cookie)">'
            "<script>steal()</script>",
        )
        await session.commit()
        assert "onerror" not in (row.body_html or "")
        assert "<script" not in (row.body_html or "")
        assert "steal()" not in (row.body_html or "")
        assert "<p>ok</p>" in (row.body_html or "")  # legitimate content kept


async def test_upsert_inserts_then_updates(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        await _seed_run(session)

        first = await svc.upsert_draft(
            session,
            run_id="20260505T120000-aaaa",
            lesson_dir="lp/course/lesson",
            decisions={"a": "accepted"},
            body_html="<p>v1</p>",
        )
        await session.commit()
        assert first.id is not None
        first_updated_at = first.updated_at

        # Make sure utc_now() advances measurably
        await asyncio.sleep(0.01)

        second = await svc.upsert_draft(
            session,
            run_id="20260505T120000-aaaa",
            lesson_dir="lp/course/lesson",
            decisions={"a": "rejected", "b": "accepted"},
            body_html="<p>v2</p>",
        )
        await session.commit()

        assert second.id == first.id
        assert second.decisions_json == {"a": "rejected", "b": "accepted"}
        assert second.body_html == "<p>v2</p>"
        assert second.updated_at > first_updated_at


async def test_upsert_409_on_stale_token(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        await _seed_run(session)
        row = await svc.upsert_draft(
            session,
            run_id="20260505T120000-aaaa",
            lesson_dir="lp/course/lesson",
            decisions={},
            body_html=None,
        )
        await session.commit()

        bogus_token = datetime.now(timezone.utc) - timedelta(hours=1)
        with pytest.raises(svc.StaleDraftError) as exc:
            await svc.upsert_draft(
                session,
                run_id="20260505T120000-aaaa",
                lesson_dir="lp/course/lesson",
                decisions={"x": "accepted"},
                body_html=None,
                expected_updated_at=bogus_token,
            )
        # The exception carries the live row so the caller can echo it.
        assert exc.value.current.id == row.id


async def test_reset_deletes_row(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        await _seed_run(session)
        await svc.upsert_draft(
            session,
            run_id="20260505T120000-aaaa",
            lesson_dir="lp/course/lesson",
            decisions={"a": "accepted"},
            body_html="<p>x</p>",
        )
        await session.commit()

        deleted = await svc.reset_draft(
            session, "20260505T120000-aaaa", "lp/course/lesson"
        )
        await session.commit()
        assert deleted is True

        # Second reset is a no-op
        deleted_again = await svc.reset_draft(
            session, "20260505T120000-aaaa", "lp/course/lesson"
        )
        assert deleted_again is False

        gone = await svc.get_draft(
            session, "20260505T120000-aaaa", "lp/course/lesson"
        )
        assert gone is None


async def test_mark_saved_creates_then_updates(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        await _seed_run(session)

        # mark_saved on a fresh row creates it
        first = await svc.mark_saved(
            session,
            run_id="20260505T120000-aaaa",
            lesson_dir="lp/course/lesson",
            saved_to_version_path="2026.1/lp/course 2026.1/lesson/index.html",
        )
        await session.commit()
        assert first.saved_to_version_at is not None
        first_path = first.saved_to_version_path

        # Subsequent call updates the timestamp + path
        await asyncio.sleep(0.01)
        second = await svc.mark_saved(
            session,
            run_id="20260505T120000-aaaa",
            lesson_dir="lp/course/lesson",
            saved_to_version_path="2026.1/lp/course 2026.1/lesson/index.html",
        )
        await session.commit()
        assert second.id == first.id
        assert second.saved_to_version_at is not None
        assert second.saved_to_version_at >= first.saved_to_version_at
        assert second.saved_to_version_path == first_path


async def test_get_drafts_for_run_returns_only_that_run(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        await _seed_run(session, "run-a")
        await _seed_run(session, "run-b")
        await svc.upsert_draft(
            session, run_id="run-a", lesson_dir="x/y/z", decisions={}, body_html=None
        )
        await svc.upsert_draft(
            session, run_id="run-a", lesson_dir="x/y/zz", decisions={}, body_html=None
        )
        await svc.upsert_draft(
            session, run_id="run-b", lesson_dir="x/y/z", decisions={}, body_html=None
        )
        await session.commit()

        rows = await svc.get_drafts_for_run(session, "run-a")
        assert {r.lesson_dir for r in rows} == {"x/y/z", "x/y/zz"}


async def test_list_runs_with_drafts_summarises(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        await _seed_run(session, "run-a", to_version="2026.1")
        await _seed_run(session, "run-b", to_version="2026.1")

        # run-a: one in_progress, one saved
        await svc.upsert_draft(
            session,
            run_id="run-a",
            lesson_dir="lp/course/lesson-1",
            decisions={"ch": "accepted"},
            body_html=None,
        )
        await svc.mark_saved(
            session,
            run_id="run-a",
            lesson_dir="lp/course/lesson-2",
            saved_to_version_path="2026.1/x/y/z/index.html",
        )

        # run-b: one pure-pending row (rare, but exercised)
        await svc.upsert_draft(
            session,
            run_id="run-b",
            lesson_dir="lp/course/lesson-3",
            decisions={},
            body_html=None,
        )
        await session.commit()

        summary = await svc.list_runs_with_drafts(session)
        statuses_by_run: dict[str, set[str]] = {}
        for run in summary:
            statuses_by_run[run.run_id] = {
                lesson.status for lesson in run.lessons
            }
        assert statuses_by_run["run-a"] == {"in_progress", "saved"}
        assert statuses_by_run["run-b"] == {"pending"}


async def test_list_runs_with_drafts_bounds_runs_at_sql_layer(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """KNOW-2287: the limit must bound the number of *runs* returned, and
    the bound is pushed into SQL (a ``LIMIT`` is emitted) rather than the
    whole table being pulled into Python and sliced afterwards.

    Seed 5 runs, each with several lessons, ask for limit=2, and assert:
    (a) exactly the 2 most-recent runs come back, fully populated, and
    (b) the SQL the DB ran carried a ``LIMIT`` clause.

    Ordering is by ``Run.created_at`` descending, so the two newest runs
    (run-4, run-3) are returned.
    """
    from sqlalchemy import event

    statements: list[str] = []

    async with async_session_factory() as session:
        # Seed 5 runs with strictly increasing created_at so ordering is
        # deterministic regardless of insert timing granularity.
        base = datetime(2026, 5, 5, 12, 0, 0, tzinfo=timezone.utc)
        for i in range(5):
            run = Run(id=f"run-{i}", status="done", to_version="2026.1")
            run.created_at = base + timedelta(minutes=i)
            session.add(run)
            await session.flush()
            for j in range(3):
                await svc.upsert_draft(
                    session,
                    run_id=f"run-{i}",
                    lesson_dir=f"lp/course/lesson-{j}",
                    decisions={"ch": "accepted"},
                    body_html=None,
                )
        await session.commit()

        # Capture the SQL the service issues. The sync engine under the
        # async one is where the cursor-level event fires.
        sync_engine = session.bind.sync_engine

        def _before_cursor_execute(
            conn, cursor, statement, parameters, context, executemany
        ):
            statements.append(statement)

        event.listen(sync_engine, "before_cursor_execute", _before_cursor_execute)
        try:
            summary = await svc.list_runs_with_drafts(session, limit=2)
        finally:
            event.remove(sync_engine, "before_cursor_execute", _before_cursor_execute)

        # (a) Exactly two runs, the two newest, each with all 3 lessons.
        assert [r.run_id for r in summary] == ["run-4", "run-3"]
        for run in summary:
            assert len(run.lessons) == 3

        # (b) The bound was pushed into SQL: the draft/run select carried a
        # LIMIT, so we never loaded all 5 runs' rows just to slice in Python.
        draft_selects = [
            s for s in statements if "report_lesson_drafts" in s and "SELECT" in s
        ]
        assert draft_selects, "expected a select against report_lesson_drafts"
        assert any(
            "LIMIT" in s.upper() for s in draft_selects
        ), f"expected a LIMIT in the drafts query, got: {draft_selects}"


async def test_status_flips_to_saved_edited_after_post_save_edit(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """KNOW-2289 decision (Option C): once a lesson is saved to a version
    folder, a *later* edit must surface as ``saved_edited`` — the badge
    keeps the "this was saved" signal but flags that the live draft now
    differs from what was pushed (unpersisted changes). A fresh save with
    no subsequent edit stays ``saved``.
    """
    async with async_session_factory() as session:
        await _seed_run(session, "run-a")

        # Save first: status is "saved".
        await svc.mark_saved(
            session,
            run_id="run-a",
            lesson_dir="lp/course/lesson",
            saved_to_version_path="2026.1/lp/course/lesson/index.html",
        )
        await session.commit()
        summary = await svc.list_runs_with_drafts(session, limit=10)
        statuses = {ls.lesson_dir: ls.status for ls in summary[0].lessons}
        assert statuses["lp/course/lesson"] == "saved"

        # Edit after the save: utc_now() must advance past saved_to_version_at.
        await asyncio.sleep(0.01)
        await svc.upsert_draft(
            session,
            run_id="run-a",
            lesson_dir="lp/course/lesson",
            decisions={"ch-1": "accepted"},
            body_html="<p>post-save edit</p>",
        )
        await session.commit()

        summary = await svc.list_runs_with_drafts(session, limit=10)
        statuses = {ls.lesson_dir: ls.status for ls in summary[0].lessons}
        assert statuses["lp/course/lesson"] == "saved_edited"
