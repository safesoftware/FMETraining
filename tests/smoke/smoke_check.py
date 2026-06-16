#!/usr/bin/env python3
"""Hermetic in-container Docker smoke check (KNOW-2354).

Run by `make smoke` as the real runtime user (`appuser`) against the real
mounted layout — content root, writable cache root, artifacts dir, and drafts
root — to prove the path/permission surface that unit tests structurally
cannot (they pass tmp_path for every root, so they never exercise the
/app-vs-/content split or the non-root write reality).

It is HERMETIC: no live OpenAI, no live Jira, no network. It only resolves and
parses a committed synthetic 1-lesson fixture and writes a few bytes to each
writable root. The whole thing runs in well under a second.

What it guards (and why it would have caught the bugs that motivated it):

  * CONTENT READ — builds a manifest from a synthetic 1-lesson fixture under
    LESSON_CONTENT_ROOT. If content resolved against REPO_ROOT (=/app) instead
    of LESSON_CONTENT_ROOT (=/content), zero lessons would resolve and the
    >=1-lesson assertion fails. -> catches the KNOW-2353 class.
  * CACHE WRITE — writes a probe file under pipeline CACHE_ROOT (the same root
    JIRA_CACHE_PATH lives on). If CACHE_ROOT pointed at the root-owned /app,
    this raises PermissionError. -> catches the KNOW-2352 class.
  * ARTIFACTS WRITE — writes the manifest into the per-run artifacts dir.
  * DRAFTS WRITE — writes a lesson draft via the real LocalDiskDraftStorage at
    DRAFTS_ROOT. If DRAFTS_ROOT pointed at the unprovisioned, root-owned
    /var/lib/fme-train/drafts, this raises (the lesson-edit-save 503,
    audit finding #1).

ANY PermissionError / FileNotFoundError (or a draft-storage unavailable error,
which wraps OSError) is fatal and printed loudly. Exit 0 only if every surface
passed AND at least one lesson resolved.
"""

from __future__ import annotations

import asyncio
import json
import shutil
import sys
import traceback
from datetime import datetime, timezone
from pathlib import Path

# The committed synthetic fixture lives at this subtree under the content
# root. We treat that subtree as a miniature "content corpus" so the lesson
# path the manifest sees starts with the version folder, exactly as a real
# corpus does (<version>/<lp>/<course>/<lesson>/index.html).
SMOKE_FIXTURE_SUBDIR = "tests/fixtures/smoke"
# Path of the lesson RELATIVE TO the fixture subtree (i.e. starts with the
# version). Version 9999.0 is below SMOKE_TO_VERSION so scope resolution keeps
# it; the path shape mirrors production.
SMOKE_LESSON_REL = (
    "9999.0/fme-form-basic/Smoke Test Course 9999.0/Smoke Test Lesson/index.html"
)
# Path of the lesson RELATIVE TO the real content root — the value a real
# manifest stores and that edit_suggestions._resolve_lesson_html_path resolves
# against config.LESSON_CONTENT_ROOT (the exact KNOW-2353 surface).
SMOKE_LESSON_DIR_FROM_CONTENT_ROOT = (
    f"{SMOKE_FIXTURE_SUBDIR}/9999.0/fme-form-basic/"
    "Smoke Test Course 9999.0/Smoke Test Lesson"
)
SMOKE_TO_VERSION = "9999.1"


class SmokeFailure(Exception):
    """A smoke assertion or a fatal path/permission error."""


def _ok(msg: str) -> None:
    print(f"  [ok]   {msg}")


def _step(msg: str) -> None:
    print(f"[smoke] {msg}")


def _resolve_roots() -> dict[str, Path]:
    """Read the runtime roots the same way the app + pipeline do."""
    from app.config import get_settings
    from pipeline import config as pipeline_config

    settings = get_settings()
    roots = {
        "content_root": pipeline_config.LESSON_CONTENT_ROOT,
        "cache_root": pipeline_config.CACHE_ROOT,
        "jira_cache_path": pipeline_config.JIRA_CACHE_PATH,
        "artifacts_root": Path(settings.artifacts_root),
        "drafts_root": Path(settings.drafts_root),
    }
    _step("resolved runtime roots:")
    for k, v in roots.items():
        print(f"         {k:>15} = {v}")
    # Sanity: the Jira cache MUST live under the writable CACHE_ROOT, never
    # bare under /app (the KNOW-2352 trap).
    if roots["cache_root"] not in roots["jira_cache_path"].parents:
        raise SmokeFailure(
            f"JIRA_CACHE_PATH ({roots['jira_cache_path']}) is not under "
            f"CACHE_ROOT ({roots['cache_root']}) — the cache could land on a "
            f"non-writable root (KNOW-2352)."
        )
    return roots


def _check_content_read(content_root: Path, artifacts_root: Path) -> int:
    """Build a real manifest from the synthetic fixture. Returns lesson count.

    Exercises LESSON_CONTENT_ROOT resolution + HTML parse + artifacts write,
    plus the exact edit_suggestions resolver that KNOW-2353 fixed.
    """
    from pipeline.content_source import LessonContentNotFound, get_content_source
    from pipeline.manifest import build_manifest

    # Miniature content corpus: the fixture subtree under the REAL content
    # root. Deriving it from content_root (= config.LESSON_CONTENT_ROOT) is
    # what makes this exercise the seam — if LESSON_CONTENT_ROOT were wrong,
    # this subtree wouldn't exist and 0 lessons would resolve.
    smoke_corpus_root = content_root / SMOKE_FIXTURE_SUBDIR
    lesson_abs = smoke_corpus_root / SMOKE_LESSON_REL
    if not lesson_abs.is_file():
        # FileNotFoundError-class: the fixture isn't reachable under the
        # content root (e.g. content resolved against /app, not /content).
        raise SmokeFailure(
            f"synthetic fixture not found under content root: {lesson_abs}. "
            f"Is LESSON_CONTENT_ROOT pointing at the mounted content "
            f"(/content), and is tests/fixtures/smoke committed?"
        )
    _ok(f"fixture present under content root: {lesson_abs}")

    # KNOW-2353/KNOW-2360 surface: the content resolver MUST find the lesson
    # under config.LESSON_CONTENT_ROOT (the local backend; default CONTENT_SOURCE).
    # If a regression repointed it at REPO_ROOT (=/app), get_lesson_html raises.
    try:
        html = get_content_source().get_lesson_html(SMOKE_LESSON_DIR_FROM_CONTENT_ROOT)
    except LessonContentNotFound as exc:
        raise SmokeFailure(
            "content resolver did not resolve the fixture under "
            f"LESSON_CONTENT_ROOT ({exc}). This is the KNOW-2353 failure mode "
            "(content read against REPO_ROOT)."
        )
    if not html or not html.strip():
        raise SmokeFailure("content resolver returned empty HTML for the fixture lesson.")
    _ok("content resolver found lesson HTML via get_content_source()")

    run_id = "smoke-" + datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")
    run_artifact_dir = artifacts_root / run_id
    # Artifacts-write surface: mkdir under the artifacts root.
    run_artifact_dir.mkdir(parents=True, exist_ok=True)
    _ok(f"artifacts dir writable: {run_artifact_dir}")

    job = {
        "to_version": SMOKE_TO_VERSION,
        "scope": {"lessons": [SMOKE_LESSON_REL]},
    }
    # repo_root= is the smoke corpus root (derived from the real content root),
    # exactly as the worker threads the content root into step 1. dry_run=False
    # so we parse HTML AND write the manifest artifact.
    manifest = build_manifest(
        run_id=run_id,
        job=job,
        repo_root=smoke_corpus_root,
        output_dir=run_artifact_dir,
        dry_run=False,
    )
    lessons = manifest.get("lessons", [])
    manifest_file = run_artifact_dir / f"manifest-{run_id}.json"
    if not manifest_file.is_file():
        raise SmokeFailure(f"manifest was not written to {manifest_file}")
    _ok(f"manifest written: {manifest_file.name} ({len(lessons)} lesson(s))")

    # Clean up the smoke run's artifacts so we don't leave debris around.
    shutil.rmtree(run_artifact_dir, ignore_errors=True)
    return len(lessons)


def _check_cache_write(cache_root: Path) -> None:
    """Write + read + remove a probe under CACHE_ROOT (the JIRA_CACHE_PATH root)."""
    cache_root.mkdir(parents=True, exist_ok=True)
    probe = cache_root / ".smoke_cache_probe.json"
    probe.write_text(json.dumps({"smoke": True}), encoding="utf-8")
    json.loads(probe.read_text(encoding="utf-8"))
    probe.unlink()
    _ok(f"cache root writable: {cache_root}")


def _check_drafts_write(drafts_root: Path) -> None:
    """Write a draft via the real LocalDiskDraftStorage at DRAFTS_ROOT.

    This is the exact code path the lesson-edit-save route uses; an
    unwritable/unprovisioned root surfaces as DraftStorageUnavailable (the
    503 in audit finding #1).
    """
    from app.services.draft_storage import (
        DraftStorageUnavailable,
        LocalDiskDraftStorage,
    )

    storage = LocalDiskDraftStorage(root=drafts_root)
    try:
        location = asyncio.run(
            storage.write(
                to_version=SMOKE_TO_VERSION,
                path="smoke-lp/smoke-course/smoke-lesson",
                html="<html><body><p>smoke draft</p></body></html>",
            )
        )
    except DraftStorageUnavailable as exc:
        raise SmokeFailure(
            f"DRAFTS_ROOT ({drafts_root}) is not writable by this user — "
            f"this is the lesson-edit-save 503 (audit finding #1): {exc}"
        ) from exc
    written = Path(location.key)
    if not written.is_file():
        raise SmokeFailure(f"draft was not written to {written}")
    # Clean up the probe draft subtree (<root>/<to_version>/...).
    version_subtree = drafts_root / SMOKE_TO_VERSION
    if version_subtree.is_dir():
        shutil.rmtree(version_subtree, ignore_errors=True)
    else:
        written.unlink(missing_ok=True)
    _ok(f"drafts root writable: {drafts_root}")


def main() -> int:
    _step("starting hermetic Docker smoke check (KNOW-2354)")
    _step(f"running as uid={_uid()} cwd={Path.cwd()}")
    try:
        roots = _resolve_roots()
        lesson_count = _check_content_read(
            roots["content_root"], roots["artifacts_root"]
        )
        _check_cache_write(roots["cache_root"])
        _check_drafts_write(roots["drafts_root"])

        if lesson_count < 1:
            raise SmokeFailure(
                "manifest resolved 0 lessons — content root is not seeing the "
                "fixture (the KNOW-2353 failure mode). Expected >= 1."
            )
        _ok(f">= 1 lesson resolved (got {lesson_count})")
    except (PermissionError, FileNotFoundError) as exc:
        print("\n[smoke] FAILED — fatal path/permission error:", file=sys.stderr)
        print(f"        {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 1
    except SmokeFailure as exc:
        print(f"\n[smoke] FAILED — {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # noqa: BLE001 — smoke must fail loudly on anything
        print(f"\n[smoke] FAILED — unexpected error: {type(exc).__name__}: {exc}",
              file=sys.stderr)
        traceback.print_exc()
        return 1

    print("\n[smoke] PASSED — content read + cache/artifacts/drafts writes all OK.")
    return 0


def _uid() -> str:
    try:
        import os

        return str(os.getuid())
    except AttributeError:  # pragma: no cover — non-POSIX
        return "n/a"


if __name__ == "__main__":
    # Hermetic guard: make doubly sure no live OpenAI/Jira call can be made
    # even if some imported module tries. We never invoke the LLM/Jira paths,
    # but blanking the keys turns any accidental call into a clean failure
    # rather than real spend.
    import os

    for _k in ("OPENAI_API_KEY", "JIRA_API_KEY", "JIRA_API_TOKEN"):
        os.environ.pop(_k, None)
    # Ensure the repo root (which holds the app/ + pipeline/ packages) is
    # importable regardless of the working directory the container runs from.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    sys.exit(main())
