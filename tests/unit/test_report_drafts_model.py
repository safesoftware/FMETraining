"""Schema tests for ``report_lesson_drafts``. KNOW-2276."""

from __future__ import annotations

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from app.models import Run, ReportLessonDraft


pytestmark = pytest.mark.asyncio


async def _seed_run(session: AsyncSession, run_id: str = "20260505T120000-aaaa") -> Run:
    run = Run(id=run_id, status="done", to_version="2026.1")
    session.add(run)
    await session.flush()
    return run


async def test_can_insert_draft(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        await _seed_run(session)
        draft = ReportLessonDraft(
            run_id="20260505T120000-aaaa",
            lesson_dir="lp/course 2026.1/lesson",
            decisions_json={"ch-1": "accepted", "ch-2": "rejected"},
            body_html="<p>edited</p>",
        )
        session.add(draft)
        await session.commit()
        assert draft.id is not None
        assert draft.created_at is not None
        assert draft.updated_at is not None


async def test_decisions_json_defaults_to_empty(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        await _seed_run(session)
        draft = ReportLessonDraft(
            run_id="20260505T120000-aaaa",
            lesson_dir="lp/course 2026.1/lesson",
        )
        session.add(draft)
        await session.commit()
        assert draft.decisions_json == {}


async def test_unique_run_id_lesson_dir(
    async_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    async with async_session_factory() as session:
        await _seed_run(session)
        session.add(
            ReportLessonDraft(
                run_id="20260505T120000-aaaa",
                lesson_dir="lp/course 2026.1/lesson",
            )
        )
        await session.commit()

        session.add(
            ReportLessonDraft(
                run_id="20260505T120000-aaaa",
                lesson_dir="lp/course 2026.1/lesson",
            )
        )
        with pytest.raises(IntegrityError):
            await session.commit()


async def test_fk_to_runs_is_declared() -> None:
    """The FK to ``runs.id`` must be declared so Alembic generates
    the constraint and Postgres enforces it in production. SQLite
    in tests doesn't enforce FKs without a PRAGMA, so we inspect the
    declared column metadata instead.
    """
    fk_target_tables: set[str] = set()
    for col in ReportLessonDraft.__table__.columns:
        for fk in col.foreign_keys:
            fk_target_tables.add(fk.column.table.name)
    assert {"runs", "users"} <= fk_target_tables
