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
