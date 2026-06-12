"""Unit tests for the report-regeneration service (KNOW-2348).

The service re-runs ``pipeline.report.build_report`` over a completed run's
existing artifacts (no OpenAI cost), writing the report to the served per-run
location ``<artifacts_root>/<run_id>/report-<run_id>.html``. It mirrors the
``_regen_report`` helper in ``app/services/pipeline_runner.py`` but as a
standalone, awaitable function the API endpoint can call.

These tests exercise the service directly (no FastAPI), so they run under the
SQLite-free unit suite.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.report_regen import (
    RecommendationsNotFound,
    regenerate_report,
)


def _write_recs(run_dir: Path, run_id: str) -> Path:
    """Write a minimal recommendations artifact that ``build_report`` accepts."""
    run_dir.mkdir(parents=True, exist_ok=True)
    recs_path = run_dir / f"update-recommendations-{run_id}.json"
    recs_path.write_text(
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
    return recs_path


@pytest.mark.asyncio
async def test_regenerate_report_writes_html(tmp_path: Path) -> None:
    """Happy path: writes report-<run_id>.html into <artifacts_root>/<run_id>/."""
    run_id = "20260612T000000-abcd"
    artifacts_root = tmp_path / "artifacts"
    run_dir = artifacts_root / run_id
    _write_recs(run_dir, run_id)

    out_path = await regenerate_report(run_id, artifacts_root=artifacts_root)

    assert out_path == run_dir / f"report-{run_id}.html"
    assert out_path.is_file()
    html = out_path.read_text(encoding="utf-8")
    assert run_id in html


@pytest.mark.asyncio
async def test_regenerate_report_missing_recs_raises(tmp_path: Path) -> None:
    """Guard: no recommendations artifact → RecommendationsNotFound."""
    run_id = "20260612T000000-none"
    artifacts_root = tmp_path / "artifacts"
    (artifacts_root / run_id).mkdir(parents=True)  # dir exists but no recs

    with pytest.raises(RecommendationsNotFound):
        await regenerate_report(run_id, artifacts_root=artifacts_root)


@pytest.mark.asyncio
async def test_regenerate_report_includes_edit_plans_when_present(
    tmp_path: Path,
) -> None:
    """When an edit-plans artifact exists, the report references it (Lesson
    Edits tab)."""
    run_id = "20260612T000000-edit"
    artifacts_root = tmp_path / "artifacts"
    run_dir = artifacts_root / run_id
    _write_recs(run_dir, run_id)
    (run_dir / f"edit-plans-{run_id}.json").write_text(
        json.dumps({"run_id": run_id, "completed_lessons": 0, "lessons": []}),
        encoding="utf-8",
    )

    out_path = await regenerate_report(run_id, artifacts_root=artifacts_root)
    html = out_path.read_text(encoding="utf-8")
    assert f"edit-plans-{run_id}.json" in html
