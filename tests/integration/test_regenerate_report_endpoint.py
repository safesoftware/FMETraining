"""Integration tests for ``POST /api/runs/{run_id}/regenerate-report`` (KNOW-2348).

The endpoint re-runs ``build_report`` over a completed run's existing artifacts
(no OpenAI cost) and writes ``report-<run_id>.html`` into the served per-run
location ``<artifacts_root>/<run_id>/``. It is authenticated (401 when signed
out), 404s for an unknown run, and 409s when the run lacks the step-5
recommendations artifact.

Uses the SQLite in-memory harness; ``ARTIFACTS_ROOT`` is pointed at a tmp dir so
the service writes there instead of ``/var/lib/fme-train/artifacts``.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from httpx import ASGITransport, AsyncClient
from starlette.middleware.sessions import SessionMiddleware

from app.auth import AuthMiddleware
from app.config import reset_settings
from app.db.session import get_session
from app.models.runs import Run
from app.routes import auth as auth_routes
from app.routes import index as index_routes
from app.routes import runs as runs_routes
from tests.conftest import auth_cookie_for, seed_active_user

SESSION_SECRET = "test-session-key-know-2348"

_STATIC_DIR = Path(__file__).resolve().parent.parent.parent / "app" / "static"


def _make_app(session_factory, artifacts_root: Path) -> FastAPI:
    import os

    os.environ["SESSION_SIGNING_KEY"] = SESSION_SECRET
    os.environ["TASK_DISPATCHER"] = "stub"
    os.environ["ARTIFACTS_ROOT"] = str(artifacts_root)
    reset_settings()

    app = FastAPI()
    app.add_middleware(AuthMiddleware, session_factory=session_factory)
    app.add_middleware(
        SessionMiddleware,
        secret_key=SESSION_SECRET,
        session_cookie="fme_session",
        same_site="lax",
        https_only=False,
    )
    if _STATIC_DIR.exists():
        app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")
    auth_routes.session_factory = session_factory  # type: ignore[assignment]

    async def _get_session_override():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_session] = _get_session_override
    app.include_router(auth_routes.router)
    app.include_router(index_routes.router)
    app.include_router(runs_routes.router)
    return app


async def _seed_run(session_factory, run_id: str, created_by: int) -> None:
    async with session_factory() as session:
        session.add(
            Run(
                id=run_id,
                created_by=created_by,
                to_version="2026.1",
                scope_json={"lessons": [], "courses": [], "learning_paths": []},
                options_json={"steps": "1,2,3,5"},
                status="done",
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()


def _write_recs(artifacts_root: Path, run_id: str) -> None:
    run_dir = artifacts_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / f"update-recommendations-{run_id}.json").write_text(
        json.dumps(
            {
                "run_id": run_id,
                "model": "gpt-test",
                "total_pairs": 0,
                "completed_pairs": 0,
                "generated_at": "2026-06-12T00:00:00Z",
                "assessments": [],
            }
        ),
        encoding="utf-8",
    )


@pytest.fixture
def artifacts_root(tmp_path: Path) -> Path:
    return tmp_path / "artifacts"


@pytest.fixture
async def app_with_db(async_session_factory, artifacts_root):
    return _make_app(async_session_factory, artifacts_root)


@pytest.fixture
async def client(app_with_db):
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        yield c


@pytest.fixture
async def authed_client(app_with_db, async_session_factory):
    user = await seed_active_user(async_session_factory)
    cookie = auth_cookie_for(user.id, secret=SESSION_SECRET, epoch=user.epoch)
    transport = ASGITransport(app=app_with_db)
    async with AsyncClient(transport=transport, base_url="http://testserver") as c:
        c.cookies.set("fme_session", cookie)
        yield c, user


@pytest.mark.asyncio
async def test_regenerate_report_requires_auth(client: AsyncClient) -> None:
    resp = await client.post("/api/runs/some-run/regenerate-report")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_regenerate_report_unknown_run_404(authed_client) -> None:
    client, _ = authed_client
    resp = await client.post("/api/runs/does-not-exist/regenerate-report")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_regenerate_report_missing_recs_409(
    authed_client, async_session_factory, artifacts_root
) -> None:
    client, user = authed_client
    run_id = "20260612T000000-norecs"
    await _seed_run(async_session_factory, run_id, user.id)
    # No recs artifact on disk.

    resp = await client.post(f"/api/runs/{run_id}/regenerate-report")
    assert resp.status_code == 409, resp.text


@pytest.mark.asyncio
async def test_regenerate_report_happy_path(
    authed_client, async_session_factory, artifacts_root
) -> None:
    client, user = authed_client
    run_id = "20260612T000000-ok"
    await _seed_run(async_session_factory, run_id, user.id)
    _write_recs(artifacts_root, run_id)

    resp = await client.post(f"/api/runs/{run_id}/regenerate-report")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["report_url"] == f"/report/{run_id}"

    report_file = artifacts_root / run_id / f"report-{run_id}.html"
    assert report_file.is_file()
    assert run_id in report_file.read_text(encoding="utf-8")


@pytest.mark.asyncio
async def test_launch_page_renders_regen_report_button(authed_client) -> None:
    """The signed-in launch page wires the run-history "Regen Report" action."""
    client, _ = authed_client
    resp = await client.get("/")
    assert resp.status_code == 200
    body = resp.text
    assert "Regen Report" in body
    assert "regenerate-report" in body
