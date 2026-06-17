"""Integration tests for the Skilljar release router.

Drives the five release endpoints
(``release-status`` / ``release-plan`` / ``release-execute`` /
``link-draft-course`` / ``release-log``) through FastAPI's ``TestClient``,
asserting the FROZEN response shapes from
``docs/plans/release-sprint-api-contract.md`` plus the 400 (bad version),
503 (no API key), and 404 (unknown action_key) error paths.

The real ``SkilljarReleaseService`` (pipeline / Skilljar / S3 I/O) is never
constructed: the route's lazy ``_get_service`` singleton getter is monkeypatched
to return a ``_FakeReleaseService`` that returns canned data. This is the swap
seam the integrator relies on — patch ``skilljar_release_route._get_service``.
"""
from __future__ import annotations

from typing import Optional

import pytest
from fastapi.testclient import TestClient

from app.config import reset_settings
from app.db.session import get_session
from app.routes import skilljar_release as skilljar_release_route
from app.services.skilljar_release_service import ReleaseLog


def _override_get_session_factory(async_session_factory):
    """Build a ``get_session`` override that yields from the test engine."""

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


# ---- fake service --------------------------------------------------------


class _FakeReleaseService:
    """Stand-in for ``SkilljarReleaseService`` with canned, deterministic
    return values. No network / disk / pipeline calls happen.

    ``link_draft_course`` raises ``RuntimeError`` when asked to match the
    sentinel ``skilljar_course_id == "BOOM"`` so the 400 path is exercised.
    """

    def __init__(self) -> None:
        # One pre-seeded run so the release-log happy path has something to find.
        self._runs: dict[str, ReleaseLog] = {
            "release:2026.1:1718000000000": ReleaseLog(
                action_key="release:2026.1:1718000000000",
                status="running",
                log=["=== Course: Connect To Data 2026.1 (id=abc123) ===", "Step 1/5: ..."],
            )
        }

    def release_status(self, to_version: str) -> dict[str, list[str]]:
        return {
            "saved": [f"{to_version}/fme-form-basic/Connect To Data {to_version}/Read and Display Data"],
            "mapped": [f"{to_version}/fme-form-basic/Connect To Data {to_version}/Read and Display Data"],
            "direct": [],
        }

    def build_release_plan(self, to_version: str, lessons: list[str]) -> dict:
        return {
            "to_version": to_version,
            "courses": [
                {
                    "action": "release",
                    "source_course_id": "abc123",
                    "source_course_title": "Connect To Data 2025.0",
                    "archive_title": "Connect To Data 2025.0",
                    "new_title": f"Connect To Data {to_version}",
                    "new_labels": [to_version],
                    "lp": "fme-form-basic",
                    "course_canonical": "Connect To Data",
                    "course_folder": f"Connect To Data {to_version}",
                    "is_draft": False,
                    "lessons": [
                        {
                            "skilljar_lesson_id": "les_456",
                            "skilljar_course_id": "abc123",
                            "lesson_dir": dir_,
                            "lesson_name": "Read and Display Data",
                            "local_path": "/abs/path/index.html",
                            "has_local_file": True,
                            "mapped": True,
                            "is_draft": False,
                        }
                        for dir_ in lessons
                    ],
                }
            ],
            "warnings": [],
        }

    def execute_release(
        self, to_version: str, lessons: list[str], *, dry_run: bool = False
    ) -> str:
        return f"release:{to_version}:1718000000000"

    def link_draft_course(
        self, course_prefix: str, skilljar_course_id: str
    ) -> dict:
        if skilljar_course_id == "BOOM":
            raise RuntimeError("Skilljar course not found: BOOM")
        return {
            "matched": [
                {
                    "local_dir": f"{course_prefix}/Read and Display Data",
                    "skilljar_lesson_id": "les_789",
                    "title": "Read and Display Data",
                }
            ],
            "unmatched_local": ["Some Folder Without A Match"],
            "unmatched_skilljar": ["A Skilljar Lesson Title With No Local Folder"],
        }

    def get_release_log(self, action_key: str) -> Optional[ReleaseLog]:
        return self._runs.get(action_key)


# ---- fixture (mirrors test_skilljar_route.py) ----------------------------


@pytest.fixture
def configured_app(async_session_factory, seeded_user, authenticate, monkeypatch):
    """Build the FastAPI app with a fake release service + test DB wired in."""
    skilljar_release_route.reset_service_for_tests()

    fake = _FakeReleaseService()
    monkeypatch.setattr(skilljar_release_route, "_get_service", lambda: fake)

    # Point the auth middleware's user lookup at the test DB so the seeded
    # user authenticates past the /api/* gate (KNOW-2259).
    monkeypatch.setattr(
        "app.main._get_or_create_session_factory",
        lambda: async_session_factory,
    )
    # Pretend we have an API key configured (mutating endpoints check this).
    monkeypatch.setenv("SKILLJAR_API_KEY", "test-key-not-used")
    reset_settings()
    try:
        from app.main import create_app  # late import — pulls fresh settings
        app = create_app()
        # release-execute / release-log / release-history use the DB (WS-E);
        # wire get_session at the test engine so those writes hit the test DB.
        app.dependency_overrides[get_session] = _override_get_session_factory(
            async_session_factory
        )
        with TestClient(app) as client:
            authenticate(client, seeded_user.id)
            yield client
    finally:
        reset_settings()
        skilljar_release_route.reset_service_for_tests()


# ---- release-status ------------------------------------------------------


def test_release_status_returns_saved_mapped_direct(configured_app) -> None:
    response = configured_app.get("/api/release-status?to_version=2026.1")
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"saved", "mapped", "direct"}
    assert isinstance(body["saved"], list)
    assert isinstance(body["mapped"], list)
    assert isinstance(body["direct"], list)
    assert body["saved"][0].startswith("2026.1/")


def test_release_status_bad_version_returns_400(configured_app) -> None:
    response = configured_app.get("/api/release-status?to_version=garbage")
    assert response.status_code == 400, response.text
    assert "detail" in response.json()


# ---- release-plan --------------------------------------------------------


def test_release_plan_returns_plan_dict(configured_app) -> None:
    dir1 = "2026.1/fme-form-basic/Connect To Data 2026.1/Read and Display Data"
    response = configured_app.get(
        "/api/release-plan", params={"to_version": "2026.1", "lessons": [dir1]}
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["to_version"] == "2026.1"
    assert isinstance(body["courses"], list)
    assert isinstance(body["warnings"], list)
    course = body["courses"][0]
    assert course["action"] == "release"
    assert course["new_labels"] == ["2026.1"]
    assert course["lessons"][0]["lesson_dir"] == dir1


def test_release_plan_empty_lessons(configured_app) -> None:
    response = configured_app.get("/api/release-plan?to_version=2026.1")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["to_version"] == "2026.1"
    assert body["courses"][0]["lessons"] == []


def test_release_plan_bad_version_returns_400(configured_app) -> None:
    response = configured_app.get("/api/release-plan?to_version=2026")
    assert response.status_code == 400, response.text


# ---- release-execute -----------------------------------------------------


def test_release_execute_returns_action_key(configured_app) -> None:
    response = configured_app.post(
        "/api/release-execute",
        json={"to_version": "2026.1", "lessons": ["a/b/c"], "dry_run": False},
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert list(body) == ["action_key"]
    assert body["action_key"] == "release:2026.1:1718000000000"


def test_release_execute_bad_version_returns_400(configured_app) -> None:
    response = configured_app.post(
        "/api/release-execute",
        json={"to_version": "nope", "lessons": [], "dry_run": False},
    )
    assert response.status_code == 400, response.text


# ---- link-draft-course ---------------------------------------------------


def test_link_draft_course_returns_match_dict(configured_app) -> None:
    response = configured_app.post(
        "/api/link-draft-course",
        json={
            "course_prefix": "2026.1/fme-form-basic/Connect To Data 2026.1",
            "skilljar_course_id": "abc123",
        },
    )
    assert response.status_code == 200, response.text
    body = response.json()
    assert set(body) == {"matched", "unmatched_local", "unmatched_skilljar"}
    assert body["matched"][0]["skilljar_lesson_id"] == "les_789"
    assert isinstance(body["unmatched_local"], list)
    assert isinstance(body["unmatched_skilljar"], list)


def test_link_draft_course_runtime_error_returns_400(configured_app) -> None:
    response = configured_app.post(
        "/api/link-draft-course",
        json={
            "course_prefix": "2026.1/fme-form-basic/Connect To Data 2026.1",
            "skilljar_course_id": "BOOM",
        },
    )
    assert response.status_code == 400, response.text
    assert "BOOM" in response.json()["detail"]


# ---- release-log ---------------------------------------------------------


def test_release_log_returns_status_and_log(configured_app) -> None:
    key = "release:2026.1:1718000000000"
    response = configured_app.get("/api/release-log", params={"action_key": key})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["action_key"] == key
    assert body["status"] == "running"
    assert isinstance(body["log"], list)
    assert body["log"][0].startswith("=== Course:")


def test_release_log_unknown_key_returns_404(configured_app) -> None:
    response = configured_app.get(
        "/api/release-log", params={"action_key": "release:does:not:exist"}
    )
    assert response.status_code == 404, response.text
    assert "detail" in response.json()


# ---- missing API key (mirrors test_skilljar_route.py) --------------------


def test_missing_api_key_returns_503(
    async_session_factory, seeded_user, authenticate, monkeypatch
) -> None:
    """Mutating endpoints fail loudly with 503 when SKILLJAR_API_KEY is unset,
    rather than constructing a real service / crashing inside the pipeline."""
    skilljar_release_route.reset_service_for_tests()

    fake = _FakeReleaseService()
    monkeypatch.setattr(skilljar_release_route, "_get_service", lambda: fake)
    monkeypatch.setattr(
        "app.main._get_or_create_session_factory",
        lambda: async_session_factory,
    )

    # Force the no-key path. pydantic-settings reads .env at construction, so
    # delenv alone isn't enough if a real .env has the key — patch
    # ``get_settings`` in the route module to return a stub with no key.
    monkeypatch.delenv("SKILLJAR_API_KEY", raising=False)

    class _NoKeySettings:
        skilljar_api_key = None
        environment = "test"
        app_version = "test"
        log_level = "INFO"
        run_concurrency = 2
        scheduler_poll_interval_s = 2.0
        task_dispatcher = "stub"
        database_url = None

    monkeypatch.setattr(
        skilljar_release_route, "get_settings", lambda: _NoKeySettings()
    )

    reset_settings()
    try:
        from app.main import create_app
        app = create_app()
        app.dependency_overrides[get_session] = _override_get_session_factory(
            async_session_factory
        )
        with TestClient(app) as client:
            authenticate(client, seeded_user.id)
            execute = client.post(
                "/api/release-execute",
                json={"to_version": "2026.1", "lessons": [], "dry_run": False},
            )
            link = client.post(
                "/api/link-draft-course",
                json={
                    "course_prefix": "2026.1/fme-form-basic/Connect To Data 2026.1",
                    "skilljar_course_id": "abc123",
                },
            )
        assert execute.status_code == 503, execute.text
        assert "SKILLJAR_API_KEY" in execute.json()["detail"]
        assert link.status_code == 503, link.text
        assert "SKILLJAR_API_KEY" in link.json()["detail"]
    finally:
        reset_settings()
        skilljar_release_route.reset_service_for_tests()
