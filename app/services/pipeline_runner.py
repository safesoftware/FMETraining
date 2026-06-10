"""Real pipeline step-body dispatcher for the worker (KNOW-2334).

Replaces ``_stub_step_body`` with a dispatcher that calls the legacy
``pipeline/*`` functions for real, wrapped in ``asyncio.to_thread`` so the
sync legacy code doesn't block the event loop.

Design notes (see plan section 2B):
- ``make_step_body()`` returns a ``StepBody`` that the caller injects into
  ``run_worker(..., step_body=make_step_body(...))``.
- Each legacy fn is called with an explicit ``output_dir`` so we bypass the
  ``pipeline/config.ARTIFACTS_DIR`` global.
- stdout is redirected to ``ctx.logger.log_sync`` via a line-splitting sink.
- Cross-step in-memory state (manifest dict, full changelog with descriptions)
  lives in ``ctx.scratch``; it is NEVER written to disk.
- Step 3 runs LLM assessment via ``pipeline/assessment.py:run_assessment``,
  wired to ``ctx.cost_meter`` for ceiling enforcement and token accounting.
- Step 5 generates the HTML report via ``pipeline/report.py:build_report``.
- Step 6 generates edit suggestions via
  ``pipeline/edit_suggestions.py:run_edit_suggestions``, also wired to
  ``ctx.cost_meter`` for ceiling enforcement.
- PII guarantee: the slim changelog written by ``pipeline/changelog.py``
  already strips ``description`` fields. The full in-memory changelog (with
  descriptions) stays in ``ctx.scratch["changelog"]`` only. The descriptions
  dict built for assessment/edit-suggestions also lives only in
  ``ctx.scratch`` and is NEVER written to disk.
"""
from __future__ import annotations

import asyncio
import contextlib
import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.worker_lifecycle import StepBody, WorkerContext

from app.config import get_settings

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# stdout → RunLogger bridge
# ---------------------------------------------------------------------------

class _LogSink(io.TextIOBase):
    """A file-like object that forwards complete lines to ``ctx.logger.log_sync``.

    Used as the target for ``contextlib.redirect_stdout`` inside
    ``asyncio.to_thread`` so that ``print()`` calls in the legacy pipeline
    functions appear in the run log rather than being swallowed.
    """

    def __init__(self, logger_ref: "RunLogger", level: str = "info") -> None:  # noqa: F821
        super().__init__()
        self._logger_ref = logger_ref
        self._level = level
        self._buf = ""

    def write(self, s: str) -> int:
        self._buf += s
        # Flush complete lines immediately.
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            stripped = line.rstrip("\r")
            if stripped:
                self._logger_ref.log_sync(self._level, stripped)
        return len(s)

    def flush(self) -> None:
        # Flush any remaining partial line on explicit flush.
        if self._buf.strip():
            self._logger_ref.log_sync(self._level, self._buf.rstrip("\r\n"))
            self._buf = ""


# ---------------------------------------------------------------------------
# Step dispatcher factory
# ---------------------------------------------------------------------------

def make_step_body(
    artifacts_root: str | None = None,
    lesson_content_root: str | None = None,
) -> "StepBody":
    """Return a StepBody that dispatches to the real legacy pipeline fns.

    Args:
        artifacts_root: Override for ``Settings.artifacts_root``. Useful for
            tests (pass a ``tmp_path``).
        lesson_content_root: Override for ``Settings.lesson_content_root``.
    """
    settings = get_settings()
    _artifacts_root = Path(artifacts_root or settings.artifacts_root)
    _content_root = Path(lesson_content_root or settings.lesson_content_root).resolve()

    async def _step_body(step_num: int, ctx: "WorkerContext") -> None:
        # Per-run artifact directory: <artifacts_root>/<run_id>/
        run_artifact_dir = _artifacts_root / ctx.run_id
        run_artifact_dir.mkdir(parents=True, exist_ok=True)

        if step_num == 1:
            await _run_step_1(ctx, run_artifact_dir, _content_root)
        elif step_num == 2:
            await _run_step_2(ctx, run_artifact_dir)
        elif step_num == 3:
            await _run_step_3(ctx, run_artifact_dir)
        elif step_num == 5:
            await _run_step_5(ctx, run_artifact_dir)
        elif step_num == 6:
            await _run_step_6(ctx, run_artifact_dir)

    return _step_body


# ---------------------------------------------------------------------------
# Step 1 — Manifest
# ---------------------------------------------------------------------------

async def _run_step_1(
    ctx: "WorkerContext",
    output_dir: Path,
    repo_root: Path,
) -> None:
    """Run ``pipeline/manifest.py:build_manifest`` in a thread."""
    from pipeline.manifest import build_manifest

    await ctx.logger.log("info", "[step 1] building manifest...")

    def _sync() -> dict:
        sink = _LogSink(ctx.logger)
        with contextlib.redirect_stdout(sink):
            result = build_manifest(
                run_id=ctx.run_id,
                job=ctx.job,
                repo_root=repo_root,
                output_dir=output_dir,
                dry_run=False,
            )
        sink.flush()
        return result

    manifest = await asyncio.to_thread(_sync)

    # Store the full manifest in scratch for step 2 to consume.
    ctx.scratch["manifest"] = manifest
    lesson_count = len(manifest.get("lessons", []))
    await ctx.logger.log(
        "info",
        f"[step 1] manifest done: {lesson_count} lesson(s), "
        f"artifact manifest-{ctx.run_id}.json",
    )


# ---------------------------------------------------------------------------
# Step 2 — Changelog
# ---------------------------------------------------------------------------

async def _run_step_2(
    ctx: "WorkerContext",
    output_dir: Path,
) -> None:
    """Run ``pipeline/changelog.py:build_changelog`` in a thread."""
    from pipeline.changelog import build_changelog

    manifest = ctx.scratch.get("manifest")
    if manifest is None:
        raise RuntimeError(
            "Step 2 requires manifest in ctx.scratch (step 1 must run first)"
        )

    jira_source = ctx.options.get("jira_source", "csv")
    await ctx.logger.log(
        "info", f"[step 2] building changelog (jira_source={jira_source!r})..."
    )

    def _sync() -> dict:
        sink = _LogSink(ctx.logger)
        with contextlib.redirect_stdout(sink):
            # build_changelog returns the FULL changelog (with descriptions
            # in memory); it writes only the slim (description-stripped)
            # version to disk. That invariant is enforced in changelog.py.
            result = build_changelog(
                run_id=ctx.run_id,
                manifest=manifest,
                output_dir=output_dir,
                dry_run=False,
                jira_source=jira_source,
                refresh_jira=False,
            )
        sink.flush()
        return result

    # The full changelog (with descriptions) goes into scratch, NEVER to disk.
    changelog = await asyncio.to_thread(_sync)
    ctx.scratch["changelog"] = changelog

    issue_count = len(changelog.get("issues", []))
    await ctx.logger.log(
        "info",
        f"[step 2] changelog done: {issue_count} issue(s), "
        f"artifact changelog-{ctx.run_id}.json",
    )


# ---------------------------------------------------------------------------
# Step 3 — LLM Assessment
# ---------------------------------------------------------------------------

async def _run_step_3(
    ctx: "WorkerContext",
    output_dir: Path,
) -> None:
    """Run ``pipeline/assessment.py:run_assessment`` in a thread.

    Reads ``manifest`` and ``changelog`` from ``ctx.scratch`` (set by steps 1
    and 2).  Builds the ephemeral ``descriptions`` dict in-process and passes
    it (along with ``ctx.cost_meter``) into ``run_assessment`` so that:

    - Jira descriptions never touch disk (PII guarantee).
    - Token usage is recorded against the run's ``RunCostMeter``.
    - ``CostCeilingExceeded`` propagates out of ``to_thread`` to
      ``run_worker``'s handler → ``status='aborted_cost_ceiling'``.

    The resulting recommendations dict is stored in ``ctx.scratch["recommendations"]``.
    """
    from pipeline.assessment import run_assessment

    manifest = ctx.scratch.get("manifest")
    changelog = ctx.scratch.get("changelog")

    if manifest is None:
        raise RuntimeError(
            "Step 3 requires manifest in ctx.scratch (step 1 must run first)"
        )
    if changelog is None:
        raise RuntimeError(
            "Step 3 requires changelog in ctx.scratch (step 2 must run first)"
        )

    # Build the ephemeral descriptions dict: issue_key → description string.
    # These stay in memory only and are NEVER written to disk.
    descriptions: dict[str, str] = {
        i["issue_key"]: (i.get("description") or "")
        for i in changelog.get("issues", [])
        if i.get("issue_key")
    }

    issue_count = len(changelog.get("issues", []))
    lesson_count = len(manifest.get("lessons", []))
    dry_run = ctx.options.get("dry_run", False)
    cost_meter = ctx.cost_meter

    await ctx.logger.log(
        "info",
        f"[step 3] running LLM assessment "
        f"({lesson_count} lesson(s) × {issue_count} issue(s), "
        f"dry_run={dry_run})...",
    )

    def _sync() -> dict:
        sink = _LogSink(ctx.logger)
        with contextlib.redirect_stdout(sink):
            result = run_assessment(
                run_id=ctx.run_id,
                manifest=manifest,
                changelog=changelog,
                output_dir=output_dir,
                descriptions=descriptions,
                dry_run=dry_run,
                cost_meter=cost_meter,
            )
        sink.flush()
        return result

    recommendations = await asyncio.to_thread(_sync)

    ctx.scratch["recommendations"] = recommendations

    completed = recommendations.get("completed_pairs", 0)
    total = recommendations.get("total_pairs", 0)
    model = recommendations.get("model", "?")
    await ctx.logger.log(
        "info",
        f"[step 3] assessment done: {completed}/{total} pair(s) assessed, "
        f"model={model}, artifact update-recommendations-{ctx.run_id}.json",
    )


# ---------------------------------------------------------------------------
# Step 5 — Report
# ---------------------------------------------------------------------------

async def _run_step_5(
    ctx: "WorkerContext",
    output_dir: Path,
) -> None:
    """Run ``pipeline/report.py:build_report`` in a thread.

    Reads the recommendations from ``ctx.scratch["recommendations"]`` (set by
    step 3) and the edit-plans path from disk if present (set by step 6 when
    it ran before this, or absent on first pass). Writes
    ``report-<run_id>.html`` to the artifact directory.

    ``build_report`` internally calls ``get_run_job`` which reads
    ``runs.json``.  Since the worker pipeline does not use ``runs.json``, we
    write a minimal stub so ``get_run_job`` can resolve ``to_version`` for the
    report's save-draft JS.
    """
    import json as _json

    from pipeline.report import build_report
    from pipeline.utils import edit_plans_path as _edit_plans_path, recommendations_path

    recommendations = ctx.scratch.get("recommendations")
    recs_path: Path | None = None

    if recommendations is None:
        # Fall back to reading the recs artifact from disk (resume path).
        recs_path = recommendations_path(ctx.run_id, output_dir)
        if not recs_path.exists():
            raise RuntimeError(
                "Step 5 requires recommendations in ctx.scratch or on disk "
                "(step 3 must run first)"
            )
        await ctx.logger.log(
            "info",
            "[step 5] recommendations not in scratch; reading from disk (resume mode)",
        )
    else:
        recs_path = recommendations_path(ctx.run_id, output_dir)

    # Determine if an edit-plans file exists (step 6 may have already run or
    # be running after step 5 — the file presence is what matters here).
    edit_plans_file = _edit_plans_path(ctx.run_id, output_dir)
    edit_plans_arg = edit_plans_file if edit_plans_file.exists() else None

    # Write a minimal runs.json stub so build_report can resolve to_version.
    # This only writes to the run's own artifact dir — no PII touches disk.
    _runs_json = output_dir / "runs.json"
    if not _runs_json.exists():
        to_version = ctx.to_version or ""
        _stub_runs = {
            "runs": [{
                "run_id": ctx.run_id,
                "job": {"to_version": to_version, "scope": ctx.scope},
                "steps_completed": [],
            }]
        }
        _runs_json.write_text(
            _json.dumps(_stub_runs, indent=2), encoding="utf-8"
        )

    await ctx.logger.log("info", "[step 5] generating HTML report...")

    def _sync() -> Path:
        sink = _LogSink(ctx.logger)
        with contextlib.redirect_stdout(sink):
            result = build_report(
                run_id=ctx.run_id,
                output_dir=output_dir,
                recs_path=recs_path,
                edit_plans_path=edit_plans_arg,
            )
        sink.flush()
        return result

    report_file = await asyncio.to_thread(_sync)

    await ctx.logger.log(
        "info",
        f"[step 5] report done: {report_file.name}",
    )


# ---------------------------------------------------------------------------
# Step 6 — Edit Suggestions
# ---------------------------------------------------------------------------

async def _run_step_6(
    ctx: "WorkerContext",
    output_dir: Path,
) -> None:
    """Run ``pipeline/edit_suggestions.py:run_edit_suggestions`` in a thread.

    Reads recommendations + descriptions from ``ctx.scratch`` (set by step 3).
    Passes ``ctx.cost_meter`` so token usage is tracked and
    ``CostCeilingExceeded`` propagates to ``run_worker``'s existing handler
    (→ ``aborted_cost_ceiling``).

    After edit-plans are generated, re-runs ``build_report`` so the HTML
    report's "Lesson Edits" tab is enabled (mirrors the legacy pipeline.py
    behavior where step 6 regenerates the report).

    PII guarantee: ``descriptions`` lives only in ``ctx.scratch`` and is NEVER
    written to disk by either ``run_edit_suggestions`` or the report.
    """
    import json as _json

    from pipeline.edit_suggestions import run_edit_suggestions
    from pipeline.report import build_report
    from pipeline.utils import edit_plans_path as _edit_plans_path, recommendations_path

    recommendations = ctx.scratch.get("recommendations")
    if recommendations is None:
        # Resume: read recs from disk.
        recs_path = recommendations_path(ctx.run_id, output_dir)
        if not recs_path.exists():
            raise RuntimeError(
                "Step 6 requires recommendations in ctx.scratch or on disk "
                "(step 3 must run first)"
            )
        with open(recs_path, encoding="utf-8") as _f:
            recommendations = _json.load(_f)
        await ctx.logger.log(
            "info",
            "[step 6] recommendations not in scratch; read from disk (resume mode)",
        )

    # Descriptions live in ctx.scratch — NEVER on disk.
    # If step 3 populated them they're already there; otherwise we can
    # reconstruct from the in-memory changelog (also in scratch).
    descriptions: dict[str, str] = ctx.scratch.get("descriptions", {})
    if not descriptions:
        changelog = ctx.scratch.get("changelog", {})
        descriptions = {
            i["issue_key"]: (i.get("description") or "")
            for i in changelog.get("issues", [])
            if i.get("issue_key")
        }

    to_version = ctx.to_version or ""
    cost_meter = ctx.cost_meter
    dry_run = ctx.options.get("dry_run", False)

    lesson_count = len({
        a["lesson_id"]
        for a in recommendations.get("assessments", [])
        if a.get("update_likelihood") in ("medium", "high")
    })
    await ctx.logger.log(
        "info",
        f"[step 6] generating edit suggestions "
        f"({lesson_count} lesson(s) with medium/high likelihood, "
        f"dry_run={dry_run})...",
    )

    def _sync() -> dict:
        sink = _LogSink(ctx.logger)
        with contextlib.redirect_stdout(sink):
            result = run_edit_suggestions(
                run_id=ctx.run_id,
                recommendations=recommendations,
                output_dir=output_dir,
                dry_run=dry_run,
                to_version=to_version,
                descriptions=descriptions,
                cost_meter=cost_meter,
            )
        sink.flush()
        return result

    edit_plans = await asyncio.to_thread(_sync)

    # Store edit-plans in scratch for any downstream use.
    ctx.scratch["edit_plans"] = edit_plans
    completed_lessons = edit_plans.get("completed_lessons", 0)
    await ctx.logger.log(
        "info",
        f"[step 6] edit suggestions done: {completed_lessons} lesson(s), "
        f"artifact edit-plans-{ctx.run_id}.json",
    )

    # Regenerate the report now that the edit-plans artifact exists, so the
    # "Lesson Edits" tab is enabled in the HTML report.
    await ctx.logger.log("info", "[step 6] regenerating report with edit-plans tab...")

    edit_plans_file = _edit_plans_path(ctx.run_id, output_dir)
    recs_path = recommendations_path(ctx.run_id, output_dir)

    def _regen_report() -> Path:
        sink = _LogSink(ctx.logger)
        with contextlib.redirect_stdout(sink):
            result = build_report(
                run_id=ctx.run_id,
                output_dir=output_dir,
                recs_path=recs_path,
                edit_plans_path=edit_plans_file,
            )
        sink.flush()
        return result

    report_file = await asyncio.to_thread(_regen_report)
    await ctx.logger.log(
        "info",
        f"[step 6] report regenerated: {report_file.name}",
    )
