"""HTTP-level tests for the report-drafts router. KNOW-2276.

Drives the FastAPI app through ``TestClient`` with the shared async
session factory swapped in for the production engine, so each test
gets an isolated SQLite instance.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import AsyncIterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.db.session import get_session
from app.main import create_app
from app.models import Base, Run


pytestmark = pytest.mark.asyncio


@pytest.fixture
async def app_client() -> AsyncIterator[tuple[TestClient, async_sessionmaker[AsyncSession]]]:
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:", future=True
    )
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

    # Seed a run that subsequent tests can attach drafts to.
    async with factory() as session:
        session.add(Run(id="run-1", status="done", to_version="2026.1"))
        await session.commit()

    try:
        with TestClient(app) as client:
            yield client, factory
    finally:
        await engine.dispose()


async def test_get_returns_empty_when_no_drafts(
    app_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = app_client
    res = client.get("/api/runs/run-1/report-drafts")
    assert res.status_code == 200
    assert res.json() == {"lessons": {}}


async def test_put_then_get_round_trips(
    app_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = app_client
    payload = {
        "lesson_dir": "lp/course 2026.1/lesson-a",
        "decisions": {"ch-1": "accepted", "ch-2": "rejected"},
        "body_html": "<p>edited</p>",
    }
    put = client.put("/api/runs/run-1/report-drafts", json=payload)
    assert put.status_code == 200, put.text
    assert "updated_at" in put.json()

    got = client.get("/api/runs/run-1/report-drafts")
    assert got.status_code == 200
    body = got.json()
    assert "lp/course 2026.1/lesson-a" in body["lessons"]
    lesson = body["lessons"]["lp/course 2026.1/lesson-a"]
    assert lesson["decisions"] == {"ch-1": "accepted", "ch-2": "rejected"}
    assert lesson["body_html"] == "<p>edited</p>"


async def test_put_409_on_stale_expected_updated_at(
    app_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = app_client

    first = client.put(
        "/api/runs/run-1/report-drafts",
        json={
            "lesson_dir": "lp/course/lesson",
            "decisions": {},
            "body_html": None,
        },
    )
    assert first.status_code == 200

    bogus = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
    stale = client.put(
        "/api/runs/run-1/report-drafts",
        json={
            "lesson_dir": "lp/course/lesson",
            "decisions": {"x": "accepted"},
            "body_html": None,
            "expected_updated_at": bogus,
        },
    )
    assert stale.status_code == 409
    detail = stale.json()["detail"]
    assert detail["detail"] == "stale draft"
    assert "current" in detail


async def test_reset_deletes(
    app_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = app_client
    client.put(
        "/api/runs/run-1/report-drafts",
        json={
            "lesson_dir": "lp/course/lesson",
            "decisions": {"x": "accepted"},
            "body_html": "<p>hi</p>",
        },
    )
    res = client.post(
        "/api/runs/run-1/report-drafts/reset",
        json={"lesson_dir": "lp/course/lesson"},
    )
    assert res.status_code == 200
    assert res.json() == {"ok": True, "deleted": True}

    got = client.get("/api/runs/run-1/report-drafts")
    assert got.json() == {"lessons": {}}


async def test_mark_saved_sets_timestamp(
    app_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, _ = app_client
    res = client.post(
        "/api/runs/run-1/report-drafts/mark-saved",
        json={
            "lesson_dir": "lp/course/lesson",
            "saved_to_version_path": "2026.1/lp/course 2026.1/lesson/index.html",
        },
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["saved_to_version_path"].endswith("index.html")
    assert body["saved_to_version_at"]

    got = client.get("/api/runs/run-1/report-drafts")
    lesson = got.json()["lessons"]["lp/course/lesson"]
    assert lesson["saved_to_version_at"] is not None


async def test_runs_with_drafts_aggregates(
    app_client: tuple[TestClient, async_sessionmaker[AsyncSession]],
) -> None:
    client, factory = app_client
    async with factory() as session:
        session.add(Run(id="run-2", status="done", to_version="2026.1"))
        await session.commit()

    client.put(
        "/api/runs/run-1/report-drafts",
        json={
            "lesson_dir": "lp/course/lesson-1",
            "decisions": {"ch": "accepted"},
            "body_html": None,
        },
    )
    client.post(
        "/api/runs/run-2/report-drafts/mark-saved",
        json={
            "lesson_dir": "lp/course/lesson-2",
            "saved_to_version_path": "2026.1/lp/course/lesson-2/index.html",
        },
    )

    res = client.get("/api/runs/with-drafts")
    assert res.status_code == 200
    body = res.json()
    by_run = {r["run_id"]: r for r in body["runs"]}
    assert {"run-1", "run-2"} <= set(by_run.keys())
    statuses_run1 = {l["status"] for l in by_run["run-1"]["lessons"]}
    statuses_run2 = {l["status"] for l in by_run["run-2"]["lessons"]}
    assert statuses_run1 == {"in_progress"}
    assert statuses_run2 == {"saved"}
