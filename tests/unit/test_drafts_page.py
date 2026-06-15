"""Drafts page render test. KNOW-2277."""

from __future__ import annotations

from typing import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_session
from app.main import create_app
from app.models import Base, Run
from app.services import report_drafts as svc


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def app_and_factory() -> AsyncIterator[
    tuple[TestClient, async_sessionmaker[AsyncSession]]
]:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)

    async def _override_get_session() -> AsyncIterator[AsyncSession]:
        session = factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    app = create_app()
    app.dependency_overrides[get_session] = _override_get_session
    try:
        with TestClient(app) as client:
            yield client, factory
    finally:
        await engine.dispose()


async def test_drafts_page_empty_state(
    app_and_factory: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = app_and_factory
    res = client.get("/drafts")
    assert res.status_code == 200
    assert "No drafts yet" in res.text


async def test_drafts_page_lists_seeded_run(
    app_and_factory: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = app_and_factory
    async with factory() as session:
        session.add(Run(id="run-z", status="done", to_version="2026.1"))
        await session.commit()
        await svc.upsert_draft(
            session,
            run_id="run-z",
            lesson_dir="lp-x/course/lesson-q",
            decisions={"ch": "accepted"},
            body_html=None,
        )
        await svc.mark_saved(
            session,
            run_id="run-z",
            lesson_dir="lp-x/course/lesson-r",
            saved_to_version_path="2026.1/lp-x/course 2026.1/lesson-r/index.html",
        )
        await session.commit()

    res = client.get("/drafts")
    assert res.status_code == 200
    body = res.text
    assert "run-z" in body
    assert "lp-x/course/lesson-q" in body
    assert "lp-x/course/lesson-r" in body
    # Status badges
    assert "in progress" in body
    assert "saved" in body
    # Open link uses /report/{id} (carries the tab through to the per-run
    # artifact path, KNOW-2355) and deep-links to the lesson via
    # &lesson=<lesson_dir> (KNOW-2356). Jinja HTML-escapes the & to &amp; in the
    # rendered href (the browser decodes it on navigation), so assert the parts.
    # The old flat /artifacts/report-{id}.html link 404'd.
    assert "/report/run-z?tab=lesson-edits" in body
    assert "lesson=lp-x%2Fcourse%2Flesson-q" in body
    assert "/artifacts/report-run-z.html" not in body


async def test_nav_includes_drafts_link(
    app_and_factory: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = app_and_factory
    res = client.get("/")
    assert res.status_code == 200
    assert 'href="/drafts"' in res.text
