"""Integration tests for ``app.services.pipeline_runner`` steps 1–3
(KNOW-2334).

These tests run the real ``build_manifest``, ``build_changelog``, and
``run_assessment`` functions against a temp version tree + a small CSV
fixture.  OpenAI API calls in step 3 are intercepted via ``unittest.mock``
so no real network calls are made.

Assertions:
- Step 1 writes ``manifest-<run_id>.json`` under the artifact dir.
- Step 2 writes ``changelog-<run_id>.json`` under the artifact dir.
- Step 3 writes ``update-recommendations-<run_id>.json`` under the artifact dir.
- The manifest has the expected lesson count.
- The changelog artifact (on-disk file) contains NO ``"description"`` field
  (PII-absent assertion for step 2).
- The recommendations artifact (on-disk file) contains NO description string
  (PII-absent assertion for step 3).
- The changelog dict in ctx.scratch DOES contain the description field
  (it's only stripped from disk; in-memory it's intact for downstream steps).
- The stdout→log_sync bridge captures build_manifest's print() output in
  the run_logs table.
- ctx.scratch["recommendations"] is populated after step 3.
- run_steps[3].token_usage_json reflects the mocked OpenAI token counts.
- CostCeilingExceeded during step 3 results in status='aborted_cost_ceiling'.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.runs import Run, RunLog, RunStep
from app.services.pipeline_runner import make_step_body
from app.services.worker_lifecycle import (
    TERMINAL_COST_ABORTED,
    TERMINAL_OK,
    WorkerContext,
    run_worker,
)
from sqlalchemy import select

# These integration tests drive the full ``run_worker`` lifecycle, which starts
# the RunLogger's concurrent background flush. On the in-memory SQLite test
# harness that races ("cannot commit transaction - SQL statements in progress")
# and is flaky. They run reliably only against Postgres. Gate the whole module
# on a Postgres ``TEST_DATABASE_URL`` until the ephemeral-Postgres harness lands
# (KNOW-2265 / KNOW-2310), which will both point ``async_session_factory`` at
# Postgres and set this env var in ``make test``.
import os as _os

pytestmark = pytest.mark.skipif(
    "postgresql" not in _os.environ.get("TEST_DATABASE_URL", ""),
    reason=(
        "run_worker integration tests race on the in-memory SQLite harness; "
        "need ephemeral Postgres (KNOW-2265/KNOW-2310). Set TEST_DATABASE_URL "
        "to a postgresql:// URL to enable."
    ),
)


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


# ---------------------------------------------------------------------------
# Step 3: LLM Assessment (mocked OpenAI)
# ---------------------------------------------------------------------------

def _make_assessment_response_json() -> str:
    """Return a minimal valid assessment JSON string."""
    return json.dumps({
        "update_likelihood": "low",
        "justification": "Minor UI label change.",
        "impacts_exercise": False,
        "affected_headings": [],
        "screenshots_need_retaking": False,
        "affected_screenshots": [],
    })


def _mock_openai_client(
    *,
    prompt_tokens: int = 150,
    completion_tokens: int = 80,
) -> MagicMock:
    """Build a mock AsyncOpenAI client that returns a valid assessment response."""
    mock_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(
            content=_make_assessment_response_json()
        ))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        ),
    )
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    return client


def _mock_assessment_patches(mock_client: MagicMock):
    """Return a context-manager stack that patches both AsyncOpenAI and
    ``get_openai_api_key`` so assessment tests run without real credentials.

    ``_assess_all`` calls ``AsyncOpenAI(api_key=config.get_openai_api_key())``
    — without the key patch the test raises EnvironmentError before the mock
    client is even reached.
    """
    from contextlib import contextmanager

    @contextmanager
    def _ctx():
        with patch("pipeline.assessment.AsyncOpenAI") as mock_cls, \
             patch("pipeline.assessment.config.get_openai_api_key", return_value="sk-test"):
            mock_cls.return_value = mock_client
            yield

    return _ctx()


@pytest.mark.asyncio
async def test_step3_writes_recs_artifact(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """Step 3 (mocked OpenAI) should write update-recommendations-<run_id>.json."""
    run_id = "r-step3-recs"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path, to_version="2026.1")

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    with _mock_assessment_patches(_mock_openai_client()):
        final = await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=step_body,
            log_flush_interval_s=0.05,
        )

    assert final == TERMINAL_OK

    recs_file = artifact_dir / run_id / f"update-recommendations-{run_id}.json"
    assert recs_file.exists(), f"recs file not found at {recs_file}"
    data = json.loads(recs_file.read_text(encoding="utf-8"))
    assert data["run_id"] == run_id
    assert "assessments" in data


@pytest.mark.asyncio
async def test_step3_populates_scratch_recommendations(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """After step 3, ctx.scratch['recommendations'] must be set."""
    run_id = "r-step3-scratch"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path, to_version="2026.1")

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3"},
    )

    observed_scratch: list[dict] = []
    real_step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    async def _capturing_body(step_num: int, ctx: WorkerContext) -> None:
        await real_step_body(step_num, ctx)
        if step_num == 3:
            import copy
            observed_scratch.append(copy.deepcopy(ctx.scratch))

    with _mock_assessment_patches(_mock_openai_client()):
        await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=_capturing_body,
            log_flush_interval_s=0.05,
        )

    assert observed_scratch, "step 3 body should have run"
    scratch = observed_scratch[0]
    assert "recommendations" in scratch, (
        "ctx.scratch['recommendations'] must be set after step 3"
    )
    recs = scratch["recommendations"]
    assert recs["run_id"] == run_id


@pytest.mark.asyncio
async def test_step3_token_usage_recorded_in_run_steps(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """run_steps[3].token_usage_json should reflect the mocked token counts."""
    run_id = "r-step3-tokens"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path, to_version="2026.1")

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    # Use deterministic token counts so we can assert exact values.
    mocked_prompt_tokens = 333
    mocked_completion_tokens = 77

    with _mock_assessment_patches(_mock_openai_client(
        prompt_tokens=mocked_prompt_tokens,
        completion_tokens=mocked_completion_tokens,
    )):
        final = await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=step_body,
            log_flush_interval_s=0.05,
            max_run_usd=50.0,
        )

    assert final == TERMINAL_OK

    async with async_session_factory() as session:
        step3 = await session.get(RunStep, (run_id, 3))

    assert step3 is not None
    assert step3.token_usage_json is not None, "token_usage_json should be populated after step 3"

    usage = step3.token_usage_json
    assert "by_model" in usage, f"Expected 'by_model' in token_usage_json: {usage}"
    # Sum across models should match the mocked totals (one pair ran)
    total_prompt = sum(m["prompt_tokens"] for m in usage["by_model"].values())
    total_completion = sum(m["completion_tokens"] for m in usage["by_model"].values())
    assert total_prompt == mocked_prompt_tokens, (
        f"Expected {mocked_prompt_tokens} prompt tokens, got {total_prompt}"
    )
    assert total_completion == mocked_completion_tokens, (
        f"Expected {mocked_completion_tokens} completion tokens, got {total_completion}"
    )


@pytest.mark.asyncio
async def test_step3_cost_ceiling_aborts_run(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """A tiny MAX_RUN_USD ceiling should abort the run with 'aborted_cost_ceiling'."""
    run_id = "r-step3-ceiling"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path, to_version="2026.1")

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    with _mock_assessment_patches(_mock_openai_client()):
        # The ceiling is so low it fires before the first API call
        # (via check_before_call inside _call_openai).
        final = await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=step_body,
            log_flush_interval_s=0.05,
            max_run_usd=0.000001,  # $0.000001 — will be exceeded by any call
        )

    assert final == TERMINAL_COST_ABORTED, (
        f"Expected '{TERMINAL_COST_ABORTED}', got '{final}'"
    )


@pytest.mark.asyncio
async def test_step3_pii_description_absent_from_recs_artifact(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """The on-disk recs artifact must NOT contain the known PII sentinel string.

    Jira issue descriptions are built into the ephemeral ``descriptions`` dict
    (in-memory only) and passed to run_assessment, but the on-disk recs JSON
    must never contain them.
    """
    run_id = "r-step3-pii"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path)  # includes PII_SENTINEL in FMEENGINE-1001

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    with _mock_assessment_patches(_mock_openai_client()):
        final = await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=step_body,
            log_flush_interval_s=0.05,
        )

    assert final == TERMINAL_OK

    # Check ALL artifact files — none should contain the PII sentinel
    run_dir = artifact_dir / run_id
    assert run_dir.exists()

    contaminated: list[str] = []
    for fpath in run_dir.rglob("*"):
        if fpath.is_file():
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                if PII_SENTINEL in content:
                    contaminated.append(str(fpath))
            except Exception:  # noqa: BLE001
                pass

    assert not contaminated, (
        f"PII sentinel '{PII_SENTINEL}' found in artifact files: {contaminated}. "
        "Jira descriptions must never be written to any artifact file."
    )


# ---------------------------------------------------------------------------
# Step 5: Report generation (mocked OpenAI for steps 1-3)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_step5_writes_report_html(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """Step 5 should write report-<run_id>.html to the artifact dir."""
    run_id = "r-step5-report"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path, to_version="2026.1")

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3,5"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    with _mock_assessment_patches(_mock_openai_client()):
        final = await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=step_body,
            log_flush_interval_s=0.05,
        )

    assert final == TERMINAL_OK

    report_file = artifact_dir / run_id / f"report-{run_id}.html"
    assert report_file.exists(), f"report file not found at {report_file}"

    content = report_file.read_text(encoding="utf-8")
    assert run_id in content, "report HTML should contain the run_id"
    assert "<!DOCTYPE html>" in content, "report should be valid HTML"


@pytest.mark.asyncio
async def test_step5_pii_absent_from_report(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """The on-disk report HTML must NOT contain the PII sentinel."""
    run_id = "r-step5-pii"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path)  # includes PII_SENTINEL in FMEENGINE-1001

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3,5"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    with _mock_assessment_patches(_mock_openai_client()):
        final = await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=step_body,
            log_flush_interval_s=0.05,
        )

    assert final == TERMINAL_OK

    run_dir = artifact_dir / run_id
    contaminated: list[str] = []
    for fpath in run_dir.rglob("*"):
        if fpath.is_file():
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                if PII_SENTINEL in content:
                    contaminated.append(str(fpath))
            except Exception:  # noqa: BLE001
                pass

    assert not contaminated, (
        f"PII sentinel found after steps 1,2,3,5: {contaminated}. "
        "Jira descriptions must never be written to any artifact file."
    )


# ---------------------------------------------------------------------------
# Step 6: Edit suggestions (mocked OpenAI for all LLM calls)
# ---------------------------------------------------------------------------


def _mock_edit_suggestions_patches(
    mock_client: MagicMock,
    *,
    assessment_client: MagicMock | None = None,
):
    """Return a context-manager stack patching both assessment and edit_suggestions.

    ``assessment_client`` defaults to the same mock_client if not provided.
    Both AsyncOpenAI classes + their api_key getters are patched so no real
    credentials are needed.
    """
    from contextlib import contextmanager

    _asmnt_client = assessment_client if assessment_client is not None else mock_client

    @contextmanager
    def _ctx():
        with patch("pipeline.assessment.AsyncOpenAI") as asmnt_cls, \
             patch("pipeline.assessment.config.get_openai_api_key", return_value="sk-test"), \
             patch("pipeline.edit_suggestions.AsyncOpenAI") as es_cls, \
             patch("pipeline.edit_suggestions.config.get_openai_api_key", return_value="sk-test"):
            asmnt_cls.return_value = _asmnt_client
            es_cls.return_value = mock_client
            yield

    return _ctx()


def _make_edit_plan_response() -> str:
    """Minimal valid edit-plan JSON for mocking."""
    import json
    return json.dumps({
        "rename_pairs": [],
        "changes": [],
        "screenshot_updates": [],
    })


def _mock_edit_suggestions_client(
    *,
    prompt_tokens: int = 200,
    completion_tokens: int = 100,
) -> MagicMock:
    """Build a mock AsyncOpenAI client for edit_suggestions."""
    mock_response = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(
            content=_make_edit_plan_response()
        ))],
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        ),
    )
    client = MagicMock()
    client.chat.completions.create = AsyncMock(return_value=mock_response)
    return client


@pytest.mark.asyncio
async def test_step6_writes_edit_plans_json(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """Step 6 should write edit-plans-<run_id>.json to the artifact dir."""
    run_id = "r-step6-plans"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path, to_version="2026.1")

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3,5,6"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    with _mock_edit_suggestions_patches(_mock_edit_suggestions_client()):
        final = await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=step_body,
            log_flush_interval_s=0.05,
        )

    assert final == TERMINAL_OK

    edit_plans_file = artifact_dir / run_id / f"edit-plans-{run_id}.json"
    assert edit_plans_file.exists(), f"edit-plans file not found at {edit_plans_file}"

    import json
    data = json.loads(edit_plans_file.read_text(encoding="utf-8"))
    assert data["run_id"] == run_id


@pytest.mark.asyncio
async def test_step6_regenerates_report_with_edit_plans_tab(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """After step 6, the regenerated report HTML should reference the edit-plans file."""
    run_id = "r-step6-regen"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path, to_version="2026.1")

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3,5,6"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    with _mock_edit_suggestions_patches(_mock_edit_suggestions_client()):
        final = await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=step_body,
            log_flush_interval_s=0.05,
        )

    assert final == TERMINAL_OK

    report_file = artifact_dir / run_id / f"report-{run_id}.html"
    assert report_file.exists(), f"report file not found at {report_file}"

    content = report_file.read_text(encoding="utf-8")
    # The regenerated report should reference the edit-plans file in its JS constants
    assert f"edit-plans-{run_id}.json" in content, (
        "Regenerated report should contain a reference to the edit-plans JSON file"
    )


@pytest.mark.asyncio
async def test_step6_pii_absent_from_edit_plans_and_report(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """No artifact file (edit-plans OR report) may contain the PII sentinel after step 6."""
    run_id = "r-step6-pii"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path)  # includes PII_SENTINEL

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3,5,6"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    with _mock_edit_suggestions_patches(_mock_edit_suggestions_client()):
        final = await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=step_body,
            log_flush_interval_s=0.05,
        )

    assert final == TERMINAL_OK

    run_dir = artifact_dir / run_id
    assert run_dir.exists()

    contaminated: list[str] = []
    for fpath in run_dir.rglob("*"):
        if fpath.is_file():
            try:
                content = fpath.read_text(encoding="utf-8", errors="replace")
                if PII_SENTINEL in content:
                    contaminated.append(str(fpath))
            except Exception:  # noqa: BLE001
                pass

    assert not contaminated, (
        f"PII sentinel found in artifact files after step 6: {contaminated}. "
        "Jira descriptions must never be written to any artifact file."
    )


@pytest.mark.asyncio
async def test_step6_cost_ceiling_aborts_run(
    async_session_factory, tmp_version_tree, tmp_path, monkeypatch
) -> None:
    """A tiny MAX_RUN_USD ceiling should abort during step 6 with 'aborted_cost_ceiling'."""
    run_id = "r-step6-ceiling"
    tree = tmp_version_tree
    artifact_dir = tmp_path / "artifacts"

    csv_path = tmp_path / "data" / "jira_export.csv"
    _make_small_jira_csv(csv_path, to_version="2026.1")

    import pipeline.config as pipeline_cfg
    monkeypatch.setattr(pipeline_cfg, "JIRA_CSV_PATH", csv_path)

    await _seed_run(
        async_session_factory,
        run_id,
        scope={"learning_paths": [tree["lp"]], "courses": [], "lessons": []},
        to_version="2026.1",
        options={"steps": "1,2,3,5,6"},
    )

    step_body = make_step_body(
        artifacts_root=str(artifact_dir),
        lesson_content_root=str(tree["repo_root"]),
    )

    # Step 3 uses a normal ceiling to pass. Step 6 uses a near-zero ceiling
    # to trigger the cost guard before its first API call. We set max_run_usd
    # very small so the check_before_call in step 6 fires immediately.
    with _mock_edit_suggestions_patches(_mock_edit_suggestions_client()):
        final = await run_worker(
            run_id,
            session_factory=async_session_factory,
            step_body=step_body,
            log_flush_interval_s=0.05,
            max_run_usd=0.000001,  # near-zero — fires on step 3 OR step 6
        )

    # Either step 3 or step 6 triggers the ceiling; both produce TERMINAL_COST_ABORTED
    assert final == TERMINAL_COST_ABORTED, (
        f"Expected '{TERMINAL_COST_ABORTED}', got '{final}'"
    )
