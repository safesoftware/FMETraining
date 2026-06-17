"""Integration tests for WS-E (release locks + history) on the release router.

Drives ``/api/release-execute`` / ``/api/release-log`` / ``/api/release-history``
through ``TestClient`` with a fake service whose in-process release log is
mutable, so we can exercise the full finalize-on-poll path over HTTP (no direct
async DB access in these sync tests). The DB writes (locks + history) hit the
per-test SQLite engine via the ``get_session`` override.
"""
from __future__ import annotations

from typing import Optional

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings
from app.db.session import get_session
from app.routes import skilljar_release as skilljar_release_route
from app.services.skilljar_release_service import ReleaseLog

_LESSON = "2026.1/fme-form-basic/Connect To Data 2026.1/Read and Display Data"
_COURSE = "Connect To Data 2026.1"


class _FakeService:
    """Minimal release service whose execute registers a mutable running log
    under the returned action_key (tests flip it to drive finalize-on-poll)."""

    def __init__(self) -> None:
        self._runs: dict[str, ReleaseLog] = {}

    def execute_release(
        self, to_version: str, lessons: list[str], *, dry_run: bool = False
    ) -> str:
        key = f"release:{to_version}:fake"
        self._runs[key] = ReleaseLog(action_key=key, status="running", log=["started"])
        return key

    def get_release_log(self, action_key: str) -> Optional[ReleaseLog]:
        return self._runs.get(action_key)

    # Unused by these tests, present for completeness.
    def release_status(self, to_version: str) -> dict:
        return {"saved": [], "mapped": [], "direct": []}

    def build_release_plan(self, to_version: str, lessons: list[str]) -> dict:
        return {"to_version": to_version, "courses": [], "warnings": []}


def _override_get_session_factory(async_session_factory):
    async def _override_get_session():
        session = async_session_factory()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    return _override_get_session


@pytest.fixture
def ctx(async_session_factory, seeded_user, authenticate, monkeypatch):
    """Yield ``(client, fake)`` with the app + a fake service + test DB wired."""
    skilljar_release_route.reset_service_for_tests()
    fake = _FakeService()
    monkeypatch.setattr(skilljar_release_route, "_get_service", lambda: fake)
    monkeypatch.setattr(
        "app.main._get_or_create_session_factory", lambda: async_session_factory
    )
    monkeypatch.setenv("SKILLJAR_API_KEY", "test-key-not-used")
    reset_settings()
    try:
        from app.main import create_app

        app = create_app()
        app.dependency_overrides[get_session] = _override_get_session_factory(
            async_session_factory
        )
        with TestClient(app) as client:
            authenticate(client, seeded_user.id)
            yield client, fake
    finally:
        reset_settings()
        skilljar_release_route.reset_service_for_tests()


def _execute(client, *, dry_run: bool, lessons=None):
    return client.post(
        "/api/release-execute",
        json={
            "to_version": "2026.1",
            "lessons": lessons if lessons is not None else [_LESSON],
            "dry_run": dry_run,
        },
    )


def test_live_execute_records_running_history(ctx) -> None:
    client, _ = ctx
    resp = _execute(client, dry_run=False)
    assert resp.status_code == 200, resp.text

    history = client.get("/api/release-history?to_version=2026.1").json()["history"]
    assert len(history) == 1
    row = history[0]
    assert row["course"] == _COURSE
    assert row["to_version"] == "2026.1"
    assert row["status"] == "running"
    assert row["started_at"] is not None and row["finished_at"] is None


def test_concurrent_execute_same_course_returns_409(ctx) -> None:
    client, _ = ctx
    assert _execute(client, dry_run=False).status_code == 200
    # Lock still held (no finalize yet) → second live execute conflicts.
    second = _execute(client, dry_run=False)
    assert second.status_code == 409, second.text
    assert _COURSE in second.json()["detail"]


def test_dry_run_skips_locks_and_history(ctx) -> None:
    client, _ = ctx
    assert _execute(client, dry_run=True).status_code == 200
    history = client.get("/api/release-history?to_version=2026.1").json()["history"]
    assert history == []
    # And a dry-run leaves no lock, so a live release can still run.
    assert _execute(client, dry_run=False).status_code == 200


def test_finalize_on_poll_closes_history_and_releases_lock(ctx) -> None:
    client, fake = ctx
    resp = _execute(client, dry_run=False)
    key = resp.json()["action_key"]

    # Simulate the background release finishing.
    fake._runs[key].status = "done"

    # The terminal poll finalizes: history → success, lock released.
    poll = client.get(f"/api/release-log?action_key={key}")
    assert poll.status_code == 200
    assert poll.json()["status"] == "done"

    history = client.get("/api/release-history?to_version=2026.1").json()["history"]
    assert history[0]["status"] == "success"
    assert history[0]["finished_at"] is not None

    # Lock was released → the same course can be released again (no 409).
    assert _execute(client, dry_run=False).status_code == 200


def test_history_reconciles_when_poll_missed(ctx) -> None:
    client, fake = ctx
    resp = _execute(client, dry_run=False)
    key = resp.json()["action_key"]
    fake._runs[key].status = "error"  # finished, but the client never polled

    # /api/release-history reconciles pending finalizations.
    history = client.get("/api/release-history?to_version=2026.1").json()["history"]
    assert history[0]["status"] == "failed"
    assert history[0]["finished_at"] is not None
