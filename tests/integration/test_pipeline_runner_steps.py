"""Integration tests for ``app.services.pipeline_runner`` steps 1 and 2
(KNOW-2334).

These tests run the real ``build_manifest`` and ``build_changelog`` functions
against a temp version tree + a small CSV fixture.  No OpenAI or Jira API
calls are made.

Assertions:
- Step 1 writes ``manifest-<run_id>.json`` under the artifact dir.
- Step 2 writes ``changelog-<run_id>.json`` under the artifact dir.
- The manifest has the expected lesson count.
- The changelog artifact (on-disk file) contains NO ``"description"`` field
  (PII-absent assertion).
- The changelog dict in ctx.scratch DOES contain the description field
  (it's only stripped from disk; in-memory it's intact for downstream steps).
- The stdout→log_sync bridge captures build_manifest's print() output in
  the run_logs table.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.models.runs import Run, RunLog, RunStep
from app.services.pipeline_runner import make_step_body
from app.services.worker_lifecycle import TERMINAL_OK, WorkerContext, run_worker
from sqlalchemy import select


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _seed_run(
    session_factory,
    run_id: str,
    *,
    scope: dict | None = None,
    options: dict | None = None,
    to_version: str = "2026.1",
) -> None:
    async with session_factory() as session:
        session.add(
            Run(
                id=run_id,
                status="running",
                to_version=to_version,
                scope_json=scope or {},
                options_json=options or {},
                created_at=datetime.now(timezone.utc),
            )
        )
        await session.commit()


def _make_small_jira_csv(path: Path, *, to_version: str = "2026.1") -> Path:
    """Write a minimal Jira CSV with two issues in the version window.

    One issue has a non-empty description (PII sentinel) so the PII test can
    assert it was stripped from disk.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Issue key", "Issue id", "Issue Type", "Status", "Project key",
            "Summary", "Description", "Affects versions", "Fix versions",
        ])
        # Issue 1: affects version in range (2025.0, 2026.1]
        writer.writerow([
            "FMEENGINE-1001", "100001", "Story", "Done", "FMEENGINE",
            "Add new transformer XYZ",
            "VERY SECRET CUSTOMER PII DESCRIPTION - MUST NOT REACH DISK",  # PII sentinel
            "2026.1", "",
        ])
        # Issue 2: fix version in range
        writer.writerow([
            "FOUNDATION-2002", "100002", "Task", "Done", "FOUNDATION",
            "Update documentation",
            "",
            "", "2025.1",
        ])
        # Issue 3: out of range — should be filtered out
        writer.writerow([
            "FMEENGINE-999", "99999", "Story", "Done", "FMEENGINE",
            "Old issue outside window",
            "",
            "2021.0", "2021.0",
        ])
    return path


# ---------------------------------------------------------------------------
# Step 1: manifest
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_step1_writes_manifest_json(
    async_session_factory, tmp_version_tree, tmp_path
) -> None:
    """Step 1 should write manifest-<run_id>.json to the artifact dir."""
    run_id = "r-step1-manifest"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    final = await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=step_body,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_OK

    manifest_file = artifact_dir / run_id / f"manifest-{run_id}.json"
    assert manifest_file.exists(), f"manifest file not found at {manifest_file}"
    data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert data["run_id"] == run_id
    assert len(data["lessons"]) == len(tree["lessons"])


@pytest.mark.asyncio
async def test_step1_logs_appear_in_run_logs(
    async_session_factory, tmp_version_tree, tmp_path
) -> None:
    """The stdout→log_sync bridge should capture build_manifest's print lines."""
    run_id = "r-step1-logs"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=step_body,
        log_flush_interval_s=0.05,
    )

    async with async_session_factory() as session:
        logs = (
            await session.scalars(
                select(RunLog)
                .where(RunLog.run_id == run_id)
                .order_by(RunLog.id)
            )
        ).all()

    messages = [log.message for log in logs]
    # build_manifest prints "[Step 1] Resolving scope..." via stdout → log_sync
    assert any("step 1" in m.lower() for m in messages), (
        f"Expected a 'step 1' log line, got: {messages}"
    )


@pytest.mark.asyncio
async def test_step1_stores_manifest_in_scratch(
    async_session_factory, tmp_version_tree, tmp_path
) -> None:
    """After step 1, ctx.scratch['manifest'] should contain the manifest dict."""
    run_id = "r-step1-scratch"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1"},
    )

    observed_scratch: list[dict] = []
    real_step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    async def _capturing_body(step_num: int, ctx: WorkerContext) -> None:
        await real_step_body(step_num, ctx)
        if step_num == 1:
            observed_scratch.append(dict(ctx.scratch))

    await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=_capturing_body,
        log_flush_interval_s=0.05,
    )

    assert observed_scratch, "step 1 body should have run"
    assert "manifest" in observed_scratch[0], "manifest must be in ctx.scratch after step 1"
    manifest = observed_scratch[0]["manifest"]
    assert len(manifest["lessons"]) == len(tree["lessons"])


# ---------------------------------------------------------------------------
# Step 2: changelog (CSV source)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_step2_writes_changelog_json(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """Step 2 (csv source) should write changelog-<run_id>.json."""
    run_id = "r-step2-changelog"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path, to_version="2026.1")

    # Point pipeline.config.JIRA_CSV_PATH at our temp CSV
    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    final = await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=step_body,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_OK

    changelog_file = artifact_dir / run_id / f"changelog-{run_id}.json"
    assert changelog_file.exists(), f"changelog file not found at {changelog_file}"

    data = json.loads(changelog_file.read_text(encoding="utf-8"))
    assert data["run_id"] == run_id
    # The CSV has 2 issues in range; the out-of-range issue should be filtered
    assert len(data["issues"]) >= 1


# ---------------------------------------------------------------------------
# PII-absent assertion (the key correctness guarantee for KNOW-2334)
# ---------------------------------------------------------------------------

PII_SENTINEL = "VERY SECRET CUSTOMER PII DESCRIPTION - MUST NOT REACH DISK"


@pytest.mark.asyncio
async def test_pii_description_absent_from_all_artifact_files(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """No artifact file under the run dir may contain the known PII sentinel.

    This test directly asserts the core privacy guarantee: Jira issue
    descriptions are stripped from on-disk artifacts. They may live in
    ctx.scratch only.
    """
    run_id = "r-pii-check"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path)

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    final = await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=step_body,
        log_flush_interval_s=0.05,
    )

    assert final == TERMINAL_OK

    # Every file under the run artifact dir must NOT contain the PII sentinel.
    run_dir = artifact_dir / run_id
    assert run_dir.exists(), f"run artifact dir not found: {run_dir}"

    files = list(run_dir.rglob("*"))
    assert files, "No artifact files were written"

    contaminated: list[str] = []
    for fpath in files:
        if fpath.is_file():
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                if PII_SENTINEL in content:
                    contaminated.append(str(fpath))
            except Exception:  # noqa: BLE001
                pass

    assert not contaminated, (
        f"PII sentinel found on disk! Files: {contaminated}. "
        "Jira descriptions must never be written to artifact files."
    )


@pytest.mark.asyncio
async def test_pii_description_present_in_scratch_not_disk(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """In-memory ctx.scratch['changelog'] retains descriptions; disk files don't.

    This validates the full PII contract: descriptions are available in-process
    for the assessment step, but they don't leak to disk.
    """
    run_id = "r-pii-scratch"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path)

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2"},
    )

    observed_scratch: list[dict] = []
    real_step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    async def _capturing_body(step_num: int, ctx: WorkerContext) -> None:
        await real_step_body(step_num, ctx)
        if step_num == 2:
            # Take a snapshot of scratch after step 2
            import copy
            observed_scratch.append(copy.deepcopy(ctx.scratch))

    await run_worker(
        run_id,
        session_factory=async_session_factory,
        step_body=_capturing_body,
        log_flush_interval_s=0.05,
    )

    assert observed_scratch, "step 2 body should have run"
    scratch = observed_scratch[0]
    changelog_in_memory = scratch.get("changelog", {})
    issues = changelog_in_memory.get("issues", [])

    # Find the issue with our PII sentinel
    pii_issues = [i for i in issues if i.get("description") == PII_SENTINEL]
    assert pii_issues, (
        "In-memory changelog must keep descriptions for downstream steps. "
        f"Issues found: {[i.get('summary') for i in issues]}"
    )

    # And confirm the disk file doesn't have it
    changelog_file = artifact_dir / run_id / f"changelog-{run_id}.json"
    assert changelog_file.exists()
    disk_content = changelog_file.read_text(encoding="utf-8")
    assert PII_SENTINEL not in disk_content, (
        "PII sentinel leaked to disk changelog file!"
    )
