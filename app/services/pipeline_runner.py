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
- Steps 3–6 log "not yet integrated" and return immediately in this slice;
  real integration is the next increment.
- PII guarantee: the slim changelog written by ``pipeline/changelog.py``
  already strips ``description`` fields. The full in-memory changelog (with
  descriptions) stays in ``ctx.scratch["changelog"]`` only.
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
        else:
            # Steps 3–6: not yet integrated in this slice.
            await ctx.logger.log(
                "info",
                f"[step {step_num}] not yet integrated (KNOW-2334 slice 2); "
                "logging and returning",
            )

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
