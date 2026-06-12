"""Regenerate the HTML report for an existing run (KNOW-2348).

Ports the legacy "Regenerate Report" run-action (``serve.py`` POST
``/api/run-action`` → ``pipeline.py --report-only <run>``) into the FastAPI web
app. It re-runs ``pipeline.report.build_report`` over a completed run's existing
artifacts — **no OpenAI cost** — writing the report to the served per-run
location ``<artifacts_root>/<run_id>/report-<run_id>.html``.

This mirrors the ``_regen_report`` helper in
``app/services/pipeline_runner.py`` (which the worker runs at the end of step 6)
but as a standalone, awaitable function the API endpoint can call directly,
without spawning a worker or shelling out to ``pipeline.py``.

The legacy sync ``build_report`` is run in ``asyncio.to_thread`` so it doesn't
block the event loop — the same pattern the pipeline runner uses.

KNOW-2347 compatibility: ``build_report`` emits image URLs that resolve via the
``/lesson-content`` route + ``leImgRelTail`` (relative paths), so a freshly
generated report stays compatible with the ``/artifacts`` mount. We do not
rewrite any paths here — regenerating with the current ``build_report`` is
exactly what picks up the KNOW-2347 fix on an older run.
"""
from __future__ import annotations

import asyncio
import contextlib
import io
import logging
from pathlib import Path
from typing import Callable, Optional

from app.config import get_settings

_logger = logging.getLogger(__name__)

# (level, message) -> None. Thread-safe (e.g. ``RunLogger.log_sync``) so the
# in-thread ``build_report`` call can emit progress without blocking the loop.
LogCallback = Callable[[str, str], None]


class RecommendationsNotFound(Exception):
    """Raised when a run has no ``update-recommendations-<run_id>.json`` artifact.

    Without the step-5 recommendations artifact there is nothing to render, so
    the endpoint turns this into a 409 (the run exists but isn't ready for a
    report regeneration).
    """


async def regenerate_report(
    run_id: str,
    *,
    artifacts_root: str | Path | None = None,
    on_log: Optional[LogCallback] = None,
) -> Path:
    """Regenerate ``report-<run_id>.html`` from the run's existing artifacts.

    Args:
        run_id: The run whose report to regenerate.
        artifacts_root: Override for ``Settings.artifacts_root`` (tests pass a
            tmp dir). Defaults to the configured artifacts root.
        on_log: Optional ``(level, message)`` callback used to surface progress
            through the caller's existing per-run log stream (the regenerate
            endpoint passes ``RunLogger.log_sync``). Called with a "starting"
            line and a "report written" line so the user sees the regeneration
            run in the same Logs UI they already use. Must be thread-safe — it
            is invoked from within ``asyncio.to_thread``.

    Returns:
        Path to the written report HTML.

    Raises:
        RecommendationsNotFound: if the run's recommendations artifact is
            missing (nothing to render).
    """
    from pipeline.report import build_report
    from pipeline.utils import edit_plans_path, recommendations_path

    def _emit(level: str, message: str) -> None:
        if on_log is not None:
            on_log(level, message)

    root = Path(artifacts_root or get_settings().artifacts_root)
    output_dir = root / run_id

    recs_path = recommendations_path(run_id, output_dir)
    if not recs_path.exists():
        raise RecommendationsNotFound(
            f"No recommendations artifact for run {run_id!r} "
            f"(expected {recs_path.name}); run steps 1-5 first."
        )

    # Include the Lesson Edits tab only if step 6 already produced edit plans.
    ep = edit_plans_path(run_id, output_dir)
    edit_plans_arg = ep if ep.exists() else None

    _emit("info", f"Regenerating report for run {run_id} from existing artifacts…")

    def _sync() -> Path:
        # Swallow build_report's stdout so it doesn't leak into the server log.
        with contextlib.redirect_stdout(io.StringIO()):
            return build_report(
                run_id,
                output_dir,
                recs_path=recs_path,
                edit_plans_path=edit_plans_arg,
            )

    report_path = await asyncio.to_thread(_sync)
    _emit("info", f"Report written: {report_path.name}")
    _logger.info("Regenerated report for run %s → %s", run_id, report_path.name)
    return report_path
