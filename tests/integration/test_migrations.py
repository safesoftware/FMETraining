"""Integration tests for the KNOW-2271 migration scripts.

Each test exercises one seeder against an in-memory SQLite and a
``tmp_path`` working directory, verifying both first-run and
idempotent-rerun behaviour.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest
from sqlalchemy import select

from app.models.cache import JiraCache
from app.models.jobs import Job
from app.models.runs import Run, RunStep
from app.models.skilljar import LessonDraft
from scripts.migrate import seed_drafts, seed_jira_cache, seed_jobs, seed_runs


# ---- seed_runs -----------------------------------------------------------


def _write_runs_json(tmp_path: Path) -> Path:
    """Two runs that look exactly like ``artifacts/runs.json`` entries."""
    payload = {
        "runs": [
            {
                "run_id": "20260304T225238-fe4b",
                "started_at": "2026-03-04T22:52:38.317691+00:00",
                "job": {
                    "to_version": "2026.1",
                    "scope": {"lessons": ["a/b/c"]},
                },
                "steps_completed": [1, 2],
                "artifacts": {
                    "manifest": "manifest-fe4b.json",
                    "report": "report-fe4b.html",
                },
            },
            {
                "run_id": "20260317T155430-28a8",
                "started_at": "2026-03-17T15:54:30+00:00",
                "job": {
                    "to_version": "2026.1",
                    "scope": {"courses": [{"learning_path": "lp", "course": "c"}]},
                },
                "steps_completed": [1, 2, 3],
                "artifacts": {},
            },
        ]
    }
    out = tmp_path / "runs.json"
    out.write_text(json.dumps(payload), encoding="utf-8")
    return out


@pytest.mark.asyncio
async def test_seed_runs_inserts_and_is_idempotent(async_session_factory, tmp_path):
    source = _write_runs_json(tmp_path)

    result = await seed_runs.migrate(source, async_session_factory)
    assert result == {"runs_inserted": 2, "runs_skipped": 0, "steps_inserted": 5}

    async with async_session_factory() as session:
        runs = (await session.scalars(select(Run))).all()
        steps = (await session.scalars(select(RunStep))).all()

    assert {r.id for r in runs} == {
        "20260304T225238-fe4b",
        "20260317T155430-28a8",
    }
    assert all(r.status == "done" for r in runs)
    fe4b = next(r for r in runs if r.id == "20260304T225238-fe4b")
    assert fe4b.to_version == "2026.1"
    assert fe4b.scope_json == {"lessons": ["a/b/c"]}
    assert fe4b.options_json == {"artifacts": {
        "manifest": "manifest-fe4b.json",
        "report": "report-fe4b.html",
    }}
    assert fe4b.started_at is not None
    assert fe4b.finished_at is not None
    assert len(steps) == 5

    # Re-run -> nothing inserted, both runs counted as skipped.
    again = await seed_runs.migrate(source, async_session_factory)
    assert again == {"runs_inserted": 0, "runs_skipped": 2, "steps_inserted": 0}


@pytest.mark.asyncio
async def test_seed_runs_dry_run_writes_nothing(async_session_factory, tmp_path):
    source = _write_runs_json(tmp_path)
    result = await seed_runs.migrate(source, async_session_factory, dry_run=True)
    assert result["runs_inserted"] == 2
    # Dry-run should still report the would-be steps so an operator can
    # eyeball the count before flipping it live.
    assert result["steps_inserted"] == 5
    async with async_session_factory() as session:
        assert (await session.scalars(select(Run))).all() == []
        assert (await session.scalars(select(RunStep))).all() == []


# ---- seed_jobs -----------------------------------------------------------


def _write_job_json(tmp_path: Path) -> Path:
    out = tmp_path / "update-job.json"
    out.write_text(
        json.dumps(
            {
                "to_version": "2026.1",
                "scope": {
                    "lessons": [],
                    "courses": [{"learning_path": "lp", "course": "c"}],
                    "learning_paths": [],
                },
            }
        ),
        encoding="utf-8",
    )
    return out


@pytest.mark.asyncio
async def test_seed_jobs_inserts_and_is_idempotent(async_session_factory, tmp_path):
    source = _write_job_json(tmp_path)

    first = await seed_jobs.migrate(source, async_session_factory)
    assert first == {"jobs_inserted": 1, "jobs_skipped": 0}

    async with async_session_factory() as session:
        jobs = (await session.scalars(select(Job))).all()
    assert len(jobs) == 1
    assert jobs[0].owner is None
    assert jobs[0].to_version == "2026.1"
    assert jobs[0].scope_json["courses"] == [
        {"learning_path": "lp", "course": "c"}
    ]

    second = await seed_jobs.migrate(source, async_session_factory)
    assert second == {"jobs_inserted": 0, "jobs_skipped": 1}


# ---- seed_jira_cache -----------------------------------------------------


def _write_jira_cache_json(tmp_path: Path) -> Path:
    out = tmp_path / "jira_api_cache.json"
    out.write_text(
        json.dumps(
            {
                "fetched_at": "2026-03-04T22:41:00+00:00",
                "filter_id": "12345",
                "total": 7,
                "issues": [{"key": f"KNOW-{i}"} for i in range(7)],
            }
        ),
        encoding="utf-8",
    )
    return out


@pytest.mark.asyncio
async def test_seed_jira_cache_inserts_then_updates(async_session_factory, tmp_path):
    source = _write_jira_cache_json(tmp_path)
    scratch = tmp_path / "scratch"

    first = await seed_jira_cache.migrate(
        source, async_session_factory, scratch_root=scratch
    )
    assert first["rows_inserted"] == 1
    assert first["rows_updated"] == 0
    payload_path = Path(first["payload_path"])
    assert payload_path.is_file()
    on_disk = json.loads(payload_path.read_text(encoding="utf-8"))
    assert on_disk["filter_id"] == "12345"
    assert len(on_disk["issues"]) == 7

    async with async_session_factory() as session:
        rows = (await session.scalars(select(JiraCache))).all()
    assert len(rows) == 1
    assert rows[0].filter_id == "12345"
    assert rows[0].issue_count == 7
    assert rows[0].payload_s3_key == str(payload_path)

    # Bump the source's fetched_at and re-run -> UPDATE, not INSERT.
    source.write_text(
        json.dumps(
            {
                "fetched_at": "2026-04-01T00:00:00+00:00",
                "filter_id": "12345",
                "total": 9,
                "issues": [{"key": f"KNOW-{i}"} for i in range(9)],
            }
        ),
        encoding="utf-8",
    )
    second = await seed_jira_cache.migrate(
        source, async_session_factory, scratch_root=scratch
    )
    assert second["rows_inserted"] == 0
    assert second["rows_updated"] == 1

    async with async_session_factory() as session:
        rows = (await session.scalars(select(JiraCache))).all()
    assert len(rows) == 1
    assert rows[0].issue_count == 9
    # SQLite strips tz info; compare naive equivalents.
    fetched = rows[0].fetched_at
    if fetched.tzinfo is not None:
        fetched = fetched.astimezone(timezone.utc).replace(tzinfo=None)
    assert fetched == datetime(2026, 4, 1, 0, 0)


# ---- seed_drafts ---------------------------------------------------------


def _write_legacy_draft_tree(tmp_path: Path) -> Path:
    """Build a fake ``./2026.1/<lp>/<course>/<lesson>/index.html`` layout."""
    root = tmp_path / "2026.1"
    drafts = [
        ("fme-form-basic", "Connect To Data 2026.1", "Read and Display Data"),
        ("fme-form-basic", "Connect To Data 2026.1", "Connect to a Database"),
        ("integrate-spatial-data", "Work with Geometry 2026.1", "Set Geometry Type"),
    ]
    for lp, course, lesson in drafts:
        d = root / lp / course / lesson
        d.mkdir(parents=True)
        (d / "index.html").write_text(
            f"<h1>{lesson}</h1>", encoding="utf-8"
        )
    return root


@pytest.mark.asyncio
async def test_seed_drafts_inserts_files_and_rows(async_session_factory, tmp_path):
    source = _write_legacy_draft_tree(tmp_path)
    drafts_root = tmp_path / "drafts"

    result = await seed_drafts.migrate(
        source, async_session_factory, drafts_root=drafts_root
    )
    assert result == {"drafts_inserted": 3, "drafts_skipped": 0}

    # Files landed in the new layout.
    landed = sorted(p for p in drafts_root.rglob("index.html"))
    assert len(landed) == 3
    expected = drafts_root / "2026.1" / "fme-form-basic" / "Connect To Data 2026.1" / "Read and Display Data" / "index.html"
    assert expected.is_file()

    async with async_session_factory() as session:
        rows = (await session.scalars(select(LessonDraft))).all()
    assert len(rows) == 3
    paths = {r.path for r in rows}
    assert "fme-form-basic/Connect To Data 2026.1/Read and Display Data" in paths
    assert all(r.to_version == "2026.1" for r in rows)
    assert all(r.status == "draft" for r in rows)
    assert all(r.source_skilljar_lesson_id is None for r in rows)
    assert all(r.created_by is None for r in rows)


@pytest.mark.asyncio
async def test_seed_drafts_idempotent(async_session_factory, tmp_path):
    source = _write_legacy_draft_tree(tmp_path)
    drafts_root = tmp_path / "drafts"

    await seed_drafts.migrate(
        source, async_session_factory, drafts_root=drafts_root
    )
    again = await seed_drafts.migrate(
        source, async_session_factory, drafts_root=drafts_root
    )
    assert again == {"drafts_inserted": 0, "drafts_skipped": 3}


@pytest.mark.asyncio
async def test_seed_drafts_skips_unexpected_layout(
    async_session_factory, tmp_path, caplog
):
    # Two-segment path that doesn't match <lp>/<course>/<lesson>.
    bad = tmp_path / "2026.1" / "lp" / "course" / "index.html"
    bad.parent.mkdir(parents=True)
    bad.write_text("<h1>x</h1>", encoding="utf-8")

    drafts_root = tmp_path / "drafts"
    with caplog.at_level("WARNING"):
        result = await seed_drafts.migrate(
            tmp_path / "2026.1",
            async_session_factory,
            drafts_root=drafts_root,
        )
    assert result == {"drafts_inserted": 0, "drafts_skipped": 0}
    assert any("expected <lp>/<course>/<lesson>" in r.message for r in caplog.records)


@pytest.mark.asyncio
async def test_seed_drafts_dry_run_writes_nothing(async_session_factory, tmp_path):
    source = _write_legacy_draft_tree(tmp_path)
    drafts_root = tmp_path / "drafts"

    result = await seed_drafts.migrate(
        source, async_session_factory, drafts_root=drafts_root, dry_run=True
    )
    assert result["drafts_inserted"] == 3
    assert not drafts_root.exists()
    async with async_session_factory() as session:
        assert (await session.scalars(select(LessonDraft))).all() == []
