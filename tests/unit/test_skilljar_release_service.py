"""Unit tests for ``app.services.skilljar_release_service`` (WS-B2 / Wave 2).

The service is a thin wrapper around the pipeline primitives
(``pipeline.skilljar_release`` + ``pipeline.skilljar_push.load_mapping``). These
tests monkeypatch those primitives so the suite runs with **no Docker, no git
tree, no DB, and no network**:

* ``scan_saved_lessons`` is now a plain filesystem listing of the WRITABLE saved
  store and takes ``(to_version, saved_root)`` — we patch it to return a fixed
  set so the test doesn't touch the disk, and assert it is called with the
  service's ``saved_root`` (``settings.saved_versions_root``), NOT
  ``lesson_content_root``. No git/subprocess is involved.
* ``load_mapping`` is patched so ``release_status`` can compute ``mapped`` /
  ``direct`` against a fake mapping.
* The pipeline ``execute_release`` generator is patched with a fake that yields a
  few lines, so we can assert the background thread drains them into the
  ``ReleaseLog`` and flips status to ``done``.

The service uses **deferred imports** (it imports the pipeline names inside each
method), so we patch them at their definition modules
(``pipeline.skilljar_release.<name>`` / ``pipeline.skilljar_push.load_mapping``),
which is where ``from pipeline.X import Y`` resolves ``Y`` at call time.

Saved store vs content root
---------------------------
``_make_settings`` points ``saved_versions_root`` at ``tmp_path`` (the saved
store the service must use) and ``lesson_content_root`` at a SEPARATE,
deliberately-wrong sentinel path. Threading assertions check the pipeline
received ``saved_root == tmp_path`` — proving the service threads the saved
store and never the (read-only-under-s3mirror) content root.
"""
from __future__ import annotations

import time

import pytest

from app.config import Settings
from app.services import skilljar_release_service as svc_mod
from app.services.skilljar_release_service import (
    ReleaseLog,
    SkilljarReleaseService,
)

# Sentinel content root: distinct from the saved store so any test that
# accidentally threads ``lesson_content_root`` instead of ``saved_versions_root``
# fails its ``saved_root == tmp_path`` assertion.
_WRONG_CONTENT_ROOT = "/nonexistent/content-root-must-not-be-used"


def _make_settings(tmp_path) -> Settings:
    """Construct a Settings instance with a tmp SAVED store + dummy creds.

    ``saved_versions_root`` is ``tmp_path`` (the writable saved store the
    release service reads/pushes); ``lesson_content_root`` is a sentinel that
    must never be used for the saved path. ``_env_file=None`` prevents pydantic
    from reading a real ``.env`` so the test is hermetic regardless of the dev
    box's environment.
    """
    return Settings(
        _env_file=None,
        saved_versions_root=str(tmp_path),
        lesson_content_root=_WRONG_CONTENT_ROOT,
        skilljar_api_key="test-api-key",
        skilljar_domain="test.skilljar.com",
        aws_s3_bucket="test-bucket",
        aws_access_key_id="test-key-id",
        aws_secret_access_key="test-secret",
        aws_s3_region="us-west-2",
    )


def _make_service(tmp_path) -> SkilljarReleaseService:
    return SkilljarReleaseService(_make_settings(tmp_path))


# ---------------------------------------------------------------------------
# release_status
# ---------------------------------------------------------------------------

def test_release_status_sorts_and_computes_direct(tmp_path, monkeypatch) -> None:
    """release_status sorts saved/mapped/direct and derives direct correctly.

    direct = mapped dirs whose dir string IS a key in the mapping (draft/linked
    courses), per serve.py line 552 (``d in mapping``).
    """
    to_version = "2026.1"

    # Unsorted scan result; scan_saved_lessons returns a set in production.
    fake_saved = {
        "2026.1/fme-form-basic/Zeta",
        "2026.1/fme-form-basic/Alpha",
        "2026.1/fme-form-basic/Mu",  # not mapped at all
    }

    # Mapping: Alpha is a *direct* key (its dir IS a mapping key → draft/linked).
    # Zeta is mapped only as a *source* (is_lesson_mapped True, but not a key).
    fake_mapping = {
        "2026.1/fme-form-basic/Alpha": {"course_id": "c-alpha"},
        "2025.0/fme-form-basic/Zeta": {"course_id": "c-zeta"},
    }
    mapped_dirs = {
        "2026.1/fme-form-basic/Alpha",
        "2026.1/fme-form-basic/Zeta",
    }

    captured: dict = {}

    monkeypatch.setattr(
        "pipeline.skilljar_push.load_mapping",
        lambda path: fake_mapping,
    )

    def _fake_scan(tv, saved_root):
        # New Wave-2 signature: (to_version, saved_root) — a filesystem listing
        # of the writable saved store. Record args to assert no git/content-root.
        captured["scan"] = (tv, saved_root)
        return fake_saved

    monkeypatch.setattr(
        "pipeline.skilljar_release.scan_saved_lessons", _fake_scan
    )
    monkeypatch.setattr(
        "pipeline.skilljar_release.is_lesson_mapped",
        lambda d, mapping: d in mapped_dirs,
    )

    svc = _make_service(tmp_path)
    result = svc.release_status(to_version)

    # scan_saved_lessons got the saved store (tmp_path), NOT lesson_content_root.
    scan_tv, scan_root = captured["scan"]
    assert scan_tv == to_version
    assert str(scan_root) == str(tmp_path)
    assert str(scan_root) != _WRONG_CONTENT_ROOT

    assert result["saved"] == [
        "2026.1/fme-form-basic/Alpha",
        "2026.1/fme-form-basic/Mu",
        "2026.1/fme-form-basic/Zeta",
    ]
    assert result["mapped"] == [
        "2026.1/fme-form-basic/Alpha",
        "2026.1/fme-form-basic/Zeta",
    ]
    # Only Alpha is a direct mapping key.
    assert result["direct"] == ["2026.1/fme-form-basic/Alpha"]


# ---------------------------------------------------------------------------
# build_release_plan
# ---------------------------------------------------------------------------

def test_build_release_plan_delegates_to_pipeline(tmp_path, monkeypatch) -> None:
    """build_release_plan loads the mapping and forwards args to the pipeline."""
    fake_mapping = {"k": {"course_id": "c1"}}
    captured: dict = {}

    def _fake_build(scope_lesson_dirs, to_version, mapping, repo_root):
        captured["args"] = (scope_lesson_dirs, to_version, mapping, repo_root)
        return {"to_version": to_version, "courses": [], "warnings": []}

    monkeypatch.setattr(
        "pipeline.skilljar_push.load_mapping", lambda path: fake_mapping
    )
    monkeypatch.setattr(
        "pipeline.skilljar_release.build_release_plan", _fake_build
    )

    svc = _make_service(tmp_path)
    lessons = ["2026.1/lp/Course/L1", "2026.1/lp/Course/L2"]
    plan = svc.build_release_plan("2026.1", lessons)

    assert plan == {"to_version": "2026.1", "courses": [], "warnings": []}
    scope, tv, mapping, repo_root = captured["args"]
    assert scope == lessons
    assert tv == "2026.1"
    assert mapping is fake_mapping
    assert str(repo_root) == str(tmp_path)


# ---------------------------------------------------------------------------
# execute_release + get_release_log
# ---------------------------------------------------------------------------

def _poll_until_done(svc, action_key, timeout_s: float = 5.0) -> ReleaseLog:
    """Poll the run log until it leaves 'running' or we time out."""
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        rl = svc.get_release_log(action_key)
        assert rl is not None
        if rl.status != "running":
            return rl
        time.sleep(0.01)
    raise AssertionError(f"release run {action_key} did not finish in {timeout_s}s")


def test_execute_release_returns_key_and_drains_log(tmp_path, monkeypatch) -> None:
    """execute_release returns an action_key; the worker drains lines → done."""
    fake_mapping = {"k": {"course_id": "c1"}}
    captured: dict = {}

    monkeypatch.setattr(
        "pipeline.skilljar_push.load_mapping", lambda path: fake_mapping
    )
    monkeypatch.setattr(
        "pipeline.skilljar_release.build_release_plan",
        lambda scope, tv, mapping, repo_root: {
            "to_version": tv,
            "courses": [],
            "warnings": [],
        },
    )

    def _fake_exec(plan, api_key, domain, mapping, mapping_path, repo_root,
                   *, dry_run, s3_bucket, s3_key_id, s3_secret, s3_region):
        # Record the creds the service threaded from Settings so we assert
        # they came from app Settings, not pipeline.config globals.
        captured["creds"] = {
            "api_key": api_key,
            "domain": domain,
            "s3_bucket": s3_bucket,
            "s3_key_id": s3_key_id,
            "s3_secret": s3_secret,
            "s3_region": s3_region,
            "dry_run": dry_run,
        }
        yield "line 1"
        yield "line 2"

    monkeypatch.setattr("pipeline.skilljar_release.execute_release", _fake_exec)

    svc = _make_service(tmp_path)
    action_key = svc.execute_release("2026.1", ["2026.1/lp/Course/L1"])

    assert action_key.startswith("release:2026.1:")

    rl = _poll_until_done(svc, action_key)
    assert rl.status == "done"
    assert rl.log == ["line 1", "line 2"]
    assert rl.action_key == action_key

    # Creds were threaded from the app Settings (dummy values from _make_settings).
    assert captured["creds"] == {
        "api_key": "test-api-key",
        "domain": "test.skilljar.com",
        "s3_bucket": "test-bucket",
        "s3_key_id": "test-key-id",
        "s3_secret": "test-secret",
        "s3_region": "us-west-2",
        "dry_run": False,
    }


def test_execute_release_dry_run_threads_flag(tmp_path, monkeypatch) -> None:
    """dry_run=True is threaded through to the pipeline generator."""
    captured: dict = {}

    monkeypatch.setattr("pipeline.skilljar_push.load_mapping", lambda path: {})
    monkeypatch.setattr(
        "pipeline.skilljar_release.build_release_plan",
        lambda *a, **k: {"to_version": "2026.1", "courses": [], "warnings": []},
    )

    def _fake_exec(plan, api_key, domain, mapping, mapping_path, repo_root,
                   *, dry_run, s3_bucket, s3_key_id, s3_secret, s3_region):
        captured["dry_run"] = dry_run
        yield "[DRY RUN] would do stuff"

    monkeypatch.setattr("pipeline.skilljar_release.execute_release", _fake_exec)

    svc = _make_service(tmp_path)
    key = svc.execute_release("2026.1", [], dry_run=True)
    rl = _poll_until_done(svc, key)

    assert rl.status == "done"
    assert captured["dry_run"] is True


def test_execute_release_error_sets_error_status(tmp_path, monkeypatch) -> None:
    """A pipeline exception is captured into the log and flips status to error."""
    monkeypatch.setattr("pipeline.skilljar_push.load_mapping", lambda path: {})
    monkeypatch.setattr(
        "pipeline.skilljar_release.build_release_plan",
        lambda *a, **k: {"to_version": "2026.1", "courses": [], "warnings": []},
    )

    def _boom(*a, **k):
        yield "starting"
        raise RuntimeError("skilljar exploded")

    monkeypatch.setattr("pipeline.skilljar_release.execute_release", _boom)

    svc = _make_service(tmp_path)
    key = svc.execute_release("2026.1", [])
    rl = _poll_until_done(svc, key)

    assert rl.status == "error"
    assert rl.log[0] == "starting"
    assert any("skilljar exploded" in line for line in rl.log)
    assert any(line.startswith("[ERROR]") for line in rl.log)


def test_get_release_log_unknown_key_returns_none(tmp_path) -> None:
    """An unknown action_key yields None (WS-C maps that to 404)."""
    svc = _make_service(tmp_path)
    assert svc.get_release_log("nope") is None


# ---------------------------------------------------------------------------
# link_draft_course
# ---------------------------------------------------------------------------

def test_link_draft_course_delegates_and_returns(tmp_path, monkeypatch) -> None:
    """link_draft_course loads mapping, threads args, returns the pipeline dict."""
    fake_mapping = {"k": {"course_id": "c1"}}
    captured: dict = {}
    expected = {
        "matched": [{"local_dir": "L1", "skilljar_lesson_id": "s1", "title": "L1"}],
        "unmatched_local": [],
        "unmatched_skilljar": [],
    }

    def _fake_link(course_prefix, skilljar_course_id, api_key, mapping,
                   mapping_path, repo_root):
        captured["args"] = (
            course_prefix, skilljar_course_id, api_key, mapping, repo_root
        )
        return expected

    monkeypatch.setattr(
        "pipeline.skilljar_push.load_mapping", lambda path: fake_mapping
    )
    monkeypatch.setattr(
        "pipeline.skilljar_release.link_draft_course", _fake_link
    )

    svc = _make_service(tmp_path)
    result = svc.link_draft_course(
        "2026.1/fme-form-basic/Connect To Data 2026.1", "course-123"
    )

    assert result == expected
    prefix, course_id, api_key, mapping, repo_root = captured["args"]
    assert prefix == "2026.1/fme-form-basic/Connect To Data 2026.1"
    assert course_id == "course-123"
    assert api_key == "test-api-key"
    assert mapping is fake_mapping
    assert str(repo_root) == str(tmp_path)


def test_link_draft_course_propagates_runtime_error(tmp_path, monkeypatch) -> None:
    """A pipeline RuntimeError propagates (WS-C maps it to HTTP 400)."""
    monkeypatch.setattr("pipeline.skilljar_push.load_mapping", lambda path: {})

    def _boom(*a, **k):
        raise RuntimeError("no such draft course")

    monkeypatch.setattr("pipeline.skilljar_release.link_draft_course", _boom)

    svc = _make_service(tmp_path)
    with pytest.raises(RuntimeError, match="no such draft course"):
        svc.link_draft_course("2026.1/lp/Course", "course-123")


# ---------------------------------------------------------------------------
# module surface sanity
# ---------------------------------------------------------------------------

def test_release_log_defaults() -> None:
    """ReleaseLog defaults: status 'running', empty log."""
    rl = svc_mod.ReleaseLog(action_key="release:2026.1:1")
    assert rl.status == "running"
    assert rl.log == []
    assert rl.action_key == "release:2026.1:1"
