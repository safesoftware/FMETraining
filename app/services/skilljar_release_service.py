"""Skilljar release service — WS-B2 implementation (barrier B1 contract).

This module implements the public interface frozen at the foundation barrier so
the new release router (``app/routes/skilljar_release.py``, owned by WS-C) can
import a stable surface. **Do not change the public signatures** without
re-coordinating WS-B/WS-C/WS-D — they are the contract.

Background / source of truth
----------------------------
* ``serve.py`` legacy HTTP handlers ``_handle_release_status`` /
  ``_handle_release_plan`` / ``_handle_release_execute`` /
  ``_handle_link_draft_course`` (serve.py lines 540-655) define the behaviour
  and the JSON shapes the UI expects. This service ports them verbatim.
* ``pipeline/skilljar_release.py`` exposes the proven v1 primitives this service
  wraps **verbatim**: ``scan_saved_lessons``, ``is_lesson_mapped``,
  ``build_release_plan``, ``execute_release``, ``link_draft_course``.
* ``pipeline/skilljar_push.load_mapping`` loads the mapping dict.

Credentials / paths
-------------------
Resolved from the app ``Settings`` (NOT ``pipeline.config`` module globals,
which read raw ``os.environ`` and have a *different* S3 region default):
    - api_key   ← settings.skilljar_api_key
    - domain    ← settings.skilljar_domain
    - s3_bucket ← settings.aws_s3_bucket
    - s3_key_id ← settings.aws_access_key_id
    - s3_secret ← settings.aws_secret_access_key
    - s3_region ← settings.aws_s3_region   (default "us-west-2" in app Settings)
    - repo_root / content root ← settings.lesson_content_root

Box-QA risks (path decisions — flagged, not resolved here)
----------------------------------------------------------
* **R3 — read-only mapping path.** ``mapping_path`` reuses
  ``pipeline.config.SKILLJAR_MAPPING_PATH`` (``<repo>/data/skilljar-mapping.json``).
  On the EC2 box the repo is checked out under the **read-only** ``/app`` mount,
  so ``execute_release`` Step 5 (which rewrites the mapping file) and
  ``link_draft_course`` (which writes matched entries) will fail to persist
  there. We do NOT relocate the mapping now — flag for box QA. The default S3
  region also differs from ``pipeline.config`` (``us-west-2`` here vs
  ``us-east-1`` in the pipeline default); we thread the app Settings value so the
  app and the pipeline agree.
* **repo_root is a git work tree assumption.** ``scan_saved_lessons`` runs
  ``git status --porcelain`` in ``repo_root = Path(settings.lesson_content_root)``.
  It therefore only sees NEW/MODIFIED *uncommitted* ``index.html`` dirs and
  silently returns an empty set if ``repo_root`` is not a git work tree (the
  subprocess error is swallowed). On the box, ``LESSON_CONTENT_ROOT`` must point
  at an actual git checkout with the to_version edits still uncommitted for
  release status/plan to see anything — flag for box QA.

Concurrency
-----------
``pipeline.skilljar_release.execute_release`` is a *synchronous generator* of log
lines. ``execute_release`` here spawns a daemon thread that drains it into an
in-process ``ReleaseLog`` registry and returns an ``action_key`` immediately;
``get_release_log(action_key)`` returns the buffered lines + status so WS-C/WS-D
can poll/stream them. All methods are synchronous and do blocking I/O (except
``get_release_log``, which is a cheap dict+lock lookup) — WS-C's async handlers
must call them via ``run_in_threadpool`` / ``asyncio.to_thread``.

The registry is an **instance** dict guarded by an instance ``threading.Lock``,
so a single shared service instance persists runs across the execute → poll
request boundary (the recommended pattern is a module-level singleton built from
``get_settings()``).
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal, Optional

from app.config import Settings


@dataclass
class ReleaseLog:
    """In-process buffer for one background release run.

    Mirrors the legacy ``_active_runs[key]`` entry shape (serve.py line 51:
    ``{"process", "log", "status"}``), minus ``process`` since release runs are
    threads, not subprocesses.

    Attributes:
        status: ``"running"`` | ``"done"`` | ``"error"``. Matches the legacy
            status vocabulary so WS-D's poller can reuse its existing logic.
        log: ordered log lines yielded by ``execute_release``.
        action_key: the key this log is registered under.
    """

    action_key: str
    status: Literal["running", "done", "error"] = "running"
    log: list[str] = field(default_factory=list)


class SkilljarReleaseService:
    """Service wrapper around ``pipeline.skilljar_release`` for the FastAPI app.

    Construct once per request (cheap) or share a singleton — the only mutable
    state is the in-process release-log registry, which must be shared across
    requests so a poll after an execute finds the run. The recommended pattern is
    a module-level singleton built from ``get_settings()`` (see
    ``app/routes/skilljar.py`` for the throttle-state precedent), so the
    ``_runs`` registry survives across the execute → poll request boundary.
    """

    def __init__(self, settings: Settings) -> None:
        """Store settings; resolve credentials/paths lazily per operation.

        Args:
            settings: app ``Settings`` (typically ``get_settings()``). The
                service reads skilljar_api_key / skilljar_domain / aws_* /
                lesson_content_root off this and never touches
                ``pipeline.config`` module globals.
        """
        self._settings = settings
        self._repo_root = Path(settings.lesson_content_root)
        # Instance registry so a shared service persists runs across
        # execute → poll. Guarded by an instance lock (mirrors serve.py's
        # module-level _active_runs / _runs_lock pattern, but per-instance).
        self._runs: dict[str, ReleaseLog] = {}
        self._runs_lock = threading.Lock()

    # -- internal helpers --------------------------------------------------

    def _load_mapping(self) -> dict:
        """Load the Skilljar mapping dict from the canonical mapping path.

        Reuses ``pipeline.config.SKILLJAR_MAPPING_PATH`` (see Risk R3 in the
        module docstring re: the read-only ``/app`` mount on the box).
        """
        from pipeline.config import SKILLJAR_MAPPING_PATH
        from pipeline.skilljar_push import load_mapping

        return load_mapping(SKILLJAR_MAPPING_PATH)

    # -- status ------------------------------------------------------------

    def release_status(self, to_version: str) -> dict[str, list[str]]:
        """Saved + mapped lesson dirs for ``to_version``.

        Wraps ``scan_saved_lessons`` + ``is_lesson_mapped`` (pipeline) exactly as
        serve.py ``_handle_release_status`` (lines 540-553).

        Args:
            to_version: e.g. ``"2026.1"``. Caller validates the ``\\d{4}\\.\\d+``
                shape and returns 400 before reaching here.

        Returns:
            ``{"saved": [...], "mapped": [...], "direct": [...]}`` — each a
            sorted list of lesson-dir strings. ``direct`` = mapped dirs whose
            mapping key IS the to_version path (draft/linked courses).
        """
        from pipeline.skilljar_release import is_lesson_mapped, scan_saved_lessons

        mapping = self._load_mapping()
        saved = scan_saved_lessons(to_version, self._repo_root)
        mapped = [d for d in saved if is_lesson_mapped(d, mapping)]
        # "direct" = lesson_dirs whose mapping key IS the to_version path
        # (draft/linked courses).
        direct = [d for d in mapped if d in mapping]
        return {
            "saved": sorted(saved),
            "mapped": sorted(mapped),
            "direct": sorted(direct),
        }

    # -- plan --------------------------------------------------------------

    def build_release_plan(self, to_version: str, lessons: list[str]) -> dict[str, Any]:
        """Pre-flight release plan for the selected lessons.

        Thin wrapper over ``pipeline.skilljar_release.build_release_plan`` (loads
        mapping, threads repo_root). Mirrors serve.py ``_handle_release_plan``
        (lines 557-568).

        Args:
            to_version: target version, e.g. ``"2026.1"``.
            lessons: lesson-dir strings to release (may be empty).

        Returns:
            The plan dict from the pipeline — ``{"to_version", "courses": [...],
            "warnings": [...]}``.
        """
        from pipeline.skilljar_release import build_release_plan

        mapping = self._load_mapping()
        return build_release_plan(list(lessons), to_version, mapping, self._repo_root)

    # -- execute -----------------------------------------------------------

    def execute_release(
        self,
        to_version: str,
        lessons: list[str],
        *,
        dry_run: bool = False,
    ) -> str:
        """Start a release in a background thread; return its ``action_key``.

        Rebuilds the plan from ``lessons`` (like serve.py line 599), registers a
        new ``ReleaseLog`` under a fresh action_key, spawns a daemon thread that
        drains ``pipeline.skilljar_release.execute_release(...)`` into the log
        buffer, and returns immediately. Mirrors serve.py
        ``_handle_release_execute`` (lines 572-625).

        The caller (WS-C) is responsible for the ``SKILLJAR_API_KEY``-missing 503
        guard before invoking this (serve.py lines 592-594).

        Args:
            to_version: target version, e.g. ``"2026.1"``.
            lessons: lesson-dir strings to release.
            dry_run: when True, the underlying generator logs intended actions
                without mutating Skilljar or the mapping file.

        Returns:
            ``action_key`` string, shaped ``"release:{to_version}:{epoch_ms}"``
            (serve.py line 601). Poll it via ``get_release_log``.
        """
        from pipeline.config import SKILLJAR_MAPPING_PATH
        from pipeline.skilljar_release import (
            build_release_plan,
            execute_release as pipeline_execute_release,
        )

        settings = self._settings
        mapping = self._load_mapping()
        plan = build_release_plan(list(lessons), to_version, mapping, self._repo_root)

        action_key = f"release:{to_version}:{int(time.time() * 1000)}"
        log = ReleaseLog(action_key=action_key)
        with self._runs_lock:
            self._runs[action_key] = log

        def _run_release() -> None:
            try:
                for line in pipeline_execute_release(
                    plan,
                    settings.skilljar_api_key,
                    settings.skilljar_domain,
                    mapping,
                    SKILLJAR_MAPPING_PATH,
                    self._repo_root,
                    dry_run=dry_run,
                    s3_bucket=settings.aws_s3_bucket,
                    s3_key_id=settings.aws_access_key_id,
                    s3_secret=settings.aws_secret_access_key,
                    s3_region=settings.aws_s3_region,
                ):
                    with self._runs_lock:
                        log.log.append(line)
                with self._runs_lock:
                    log.status = "done"
            except Exception as exc:  # noqa: BLE001 — mirror serve.py: surface any failure into the log
                with self._runs_lock:
                    log.log.append(f"[ERROR] {exc}")
                    log.status = "error"

        threading.Thread(target=_run_release, daemon=True).start()
        return action_key

    # -- link draft course -------------------------------------------------

    def link_draft_course(
        self,
        course_prefix: str,
        skilljar_course_id: str,
    ) -> dict[str, Any]:
        """Link a local draft course folder to an existing Skilljar course.

        Wraps ``pipeline.skilljar_release.link_draft_course`` (loads mapping,
        threads api_key + mapping_path + repo_root). Mirrors serve.py
        ``_handle_link_draft_course`` (lines 629-655). The pipeline raises
        ``RuntimeError`` on failure; we let it propagate so WS-C can map it to
        HTTP 400.

        Args:
            course_prefix: e.g. ``"2026.1/fme-form-basic/Connect To Data 2026.1"``.
            skilljar_course_id: the Skilljar course to match lessons against.

        Returns:
            ``{"matched": [{"local_dir", "skilljar_lesson_id", "title"}],
            "unmatched_local": [folder, ...], "unmatched_skilljar": [title, ...]}``.
        """
        from pipeline.config import SKILLJAR_MAPPING_PATH
        from pipeline.skilljar_release import link_draft_course

        mapping = self._load_mapping()
        return link_draft_course(
            course_prefix,
            skilljar_course_id,
            self._settings.skilljar_api_key,
            mapping,
            SKILLJAR_MAPPING_PATH,
            self._repo_root,
        )

    # -- run log -----------------------------------------------------------

    def get_release_log(self, action_key: str) -> Optional[ReleaseLog]:
        """Return the in-process ``ReleaseLog`` for ``action_key``, or None.

        Cheap (dict lookup under a lock); safe to call directly from an async
        handler without a threadpool. Returns ``None`` when the key is unknown
        (WS-C maps that to HTTP 404, mirroring serve.py ``_api_run_log`` line
        239-241).

        Args:
            action_key: the key returned by ``execute_release``.

        Returns:
            ``ReleaseLog`` (status + buffered lines) or ``None`` if not found.
        """
        with self._runs_lock:
            return self._runs.get(action_key)
