"""
Step 1: Build the Lesson Manifest.

Resolves the update-job.json scope to a list of lesson paths, parses each
lesson's HTML, and writes artifacts/manifest-{RUN_ID}.json.

SOURCE-content reads (lesson HTML + lesson discovery) go through the shared
``pipeline.content_source`` resolver, so the manifest builds identically from
the local filesystem corpus (default ``CONTENT_SOURCE=local``) or the S3 mirror
(``CONTENT_SOURCE=s3mirror``). No direct filesystem read of SOURCE content
remains in this module. Target-write / saved-draft paths are untouched (there
are none here).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from tqdm import tqdm

from pipeline import config
from pipeline.config import load_product_mapping
from pipeline.content_source import (
    ContentSource,
    build_content_source,
    get_content_source,
)
from pipeline.html_parser import parse_lesson_html_from_str
from pipeline.utils import (
    lesson_id,
    manifest_path,
    parse_lesson_path,
    parse_version,
    strip_course_version,
)

# A lesson ``record["path"]`` is the lesson_dir plus this suffix; the resolver
# works in lesson_dirs (no suffix), so we bridge with this constant.
_INDEX_SUFFIX = "/index.html"


def _content_source_for(repo_root: Path) -> ContentSource:
    """Return the content source for manifest reads.

    Under the default ``local`` backend the explicit ``repo_root`` the caller
    threads in is honored (it equals ``config.LESSON_CONTENT_ROOT`` in prod/CLI,
    but tests pass a tmp tree), so local behaviour is byte-for-byte unchanged.
    For any non-local backend (e.g. ``s3mirror``) the config-selected resolver
    is used and ``repo_root`` is irrelevant.
    """
    if (config.CONTENT_SOURCE or "local").strip().lower() == "local":
        return build_content_source(source="local", content_root=repo_root)
    return get_content_source()


def _lesson_dir_to_path(lesson_dir: str) -> str:
    """Convert a resolver ``lesson_dir`` to a manifest ``record["path"]``."""
    return f"{lesson_dir}{_INDEX_SUFFIX}"


def _path_to_lesson_dir(rel_path: str) -> str:
    """Convert a manifest ``record["path"]`` to a resolver ``lesson_dir``.

    Strips a trailing ``/index.html`` (POSIX) if present; tolerates either
    separator since explicit scope paths may arrive with native separators.
    """
    posix = rel_path.replace("\\", "/")
    if posix.endswith(_INDEX_SUFFIX):
        return posix[: -len(_INDEX_SUFFIX)]
    return posix


def _record_from_lesson_dir(
    lesson_dir: str, version_str: str, version_float: float, lp: str
) -> dict:
    """Build a lesson record dict from a discovered ``lesson_dir``.

    ``lesson_dir`` is ``{version}/{lp}/{course folder}/{lesson folder}``; the
    course folder and lesson folder are its last two segments. ``path`` keeps
    the historical ``.../index.html`` form the rest of the pipeline threads.
    """
    segments = lesson_dir.split("/")
    course_folder = segments[-2]
    lesson_name = segments[-1]
    return {
        "path": _lesson_dir_to_path(lesson_dir),
        "version": version_str,
        "version_str": version_str,
        "from_version": version_float,
        "learning_path": lp,
        "course": course_folder,
        "course_canonical": strip_course_version(course_folder),
        "lesson_name": lesson_name,
    }


def build_manifest(
    run_id: str,
    job: dict,
    repo_root: Path,
    output_dir: Path,
    dry_run: bool = False,
) -> dict:
    """
    Build and write the lesson manifest for a run.

    Args:
        run_id:     The current run ID.
        job:        Parsed update-job.json contents.
        repo_root:  Repository root directory.
        output_dir: Directory to write the manifest JSON.
        dry_run:    If True, resolve scope but don't write output.

    Returns:
        The manifest dict.
    """
    to_version_str = str(job["to_version"])
    to_version = parse_version(to_version_str)
    if to_version is None:
        raise ValueError(f"Cannot parse to_version from job: {to_version_str!r}")

    product_mapping = load_product_mapping()

    source = _content_source_for(repo_root)

    # Resolve scope → list of lesson record dicts
    print("\n[Step 1] Resolving scope...")
    lesson_records = _resolve_scope(job["scope"], to_version, source)

    if not lesson_records:
        print("  WARNING: No lessons resolved from scope. Check update-job.json.")
        if dry_run:
            return {"run_id": run_id, "job": job, "lessons": []}

    print(f"  Resolved {len(lesson_records)} lesson(s) to process.")

    if dry_run:
        print("  [dry-run] Skipping HTML parsing and manifest write.")
        return {"run_id": run_id, "job": job, "lessons": lesson_records}

    # Parse HTML for each lesson
    lessons = []
    for record in tqdm(lesson_records, desc="Parsing lessons", unit="lesson"):
        lesson_dir = _path_to_lesson_dir(record["path"])
        html = source.get_lesson_html(lesson_dir)
        parsed = parse_lesson_html_from_str(html)

        product = product_mapping.get(record["learning_path"], ["fme_form", "fme_flow"])

        lid = lesson_id(
            record["version_str"],
            record["learning_path"],
            record["course_canonical"],
            record["lesson_name"],
        )

        entry = {
            "lesson_id": lid,
            "path": record["path"],
            "version": record["version_str"],
            "learning_path": record["learning_path"],
            "course": record["course"],
            "course_canonical": record["course_canonical"],
            "lesson_name": record["lesson_name"],
            "product": product,
            **parsed,
        }
        lessons.append(entry)

    manifest = {
        "run_id": run_id,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "job": job,
        "lessons": lessons,
    }

    out_path = manifest_path(run_id, output_dir)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    print(f"  Manifest written: {out_path.name}")
    return manifest


# ---------------------------------------------------------------------------
# Scope resolution
# ---------------------------------------------------------------------------

def _resolve_scope(scope: dict, to_version: float, source: ContentSource) -> list[dict]:
    """
    Resolve a scope dict to a deduplicated list of lesson record dicts.

    Each record contains: path, version_str, from_version, learning_path,
    course, course_canonical, lesson_name.

    Three scope types are unioned together when multiple are provided:
      scope.lessons       - explicit relative paths
      scope.courses       - {learning_path, course} pairs (course name without version)
      scope.learning_paths - LP folder names
    """
    results: list[dict] = []
    # Deduplication key: (course_canonical, lesson_name) within the same LP
    seen: set[tuple] = set()

    def add_record(record: dict) -> None:
        key = (record["learning_path"], record["course_canonical"], record["lesson_name"])
        if key not in seen:
            seen.add(key)
            results.append(record)

    # --- Explicit lesson paths ---
    for rel_path in scope.get("lessons", []):
        try:
            parsed = parse_lesson_path(rel_path)
        except ValueError as e:
            print(f"  WARNING: Skipping bad lesson path ({e})")
            continue
        if parsed["from_version"] >= to_version:
            print(
                f"  WARNING: Skipping lesson at version {parsed['version_str']} "
                f"which is >= to_version {to_version}: {rel_path}"
            )
            continue
        if not source.lesson_html_exists(_path_to_lesson_dir(rel_path)):
            print(f"  WARNING: Lesson path not found in content source, skipping: {rel_path}")
            continue
        parsed["path"] = rel_path
        add_record(parsed)

    # --- Course-level scope ---
    for course_entry in scope.get("courses", []):
        lp = course_entry.get("learning_path", "")
        course_canonical = course_entry.get("course", "")
        if not lp or not course_canonical:
            print(f"  WARNING: Invalid course entry (missing learning_path or course): {course_entry}")
            continue
        records = _resolve_course(lp, course_canonical, to_version, source)
        for r in records:
            add_record(r)

    # --- Learning path scope ---
    for lp in scope.get("learning_paths", []):
        records = _resolve_learning_path(lp, to_version, source)
        for r in records:
            add_record(r)

    return results


def _get_sorted_version_folders(source: ContentSource, descending: bool = True) -> list[tuple[float, str]]:
    """
    Return a list of (version_float, folder_name) for all valid version
    directories the content source exposes, sorted by version float.
    """
    folders = []
    for name in source.list_versions():
        v = parse_version(name)
        if v is not None:
            folders.append((v, name))
    folders.sort(key=lambda x: x[0], reverse=descending)
    return folders


def _resolve_learning_path(lp: str, to_version: float, source: ContentSource) -> list[dict]:
    """
    Find all lessons in the most recent version of each unique lesson under a learning path.

    For each (course_canonical, lesson_name) pair, pick the highest version < to_version.
    """
    version_folders = _get_sorted_version_folders(source, descending=True)
    seen_lessons: set[tuple] = set()
    results: list[dict] = []

    for version_float, version_str in version_folders:
        if version_float >= to_version:
            continue

        # discover_lessons() returns lesson_dirs (no index.html suffix) only for
        # lessons that HAVE an index.html, deduping punctuation variants — i.e.
        # the same lessons the old course/lesson iterdir walk surfaced. Sorted
        # so course/lesson order is deterministic, matching the legacy
        # sorted(iterdir()) traversal.
        for lesson_dir in sorted(source.discover_lessons(version_str, lp)):
            course_folder = lesson_dir.split("/")[-2]
            # Skip "Clone of" courses
            if course_folder.startswith("Clone of"):
                continue

            course_canonical = strip_course_version(course_folder)
            lesson_name = lesson_dir.split("/")[-1]

            key = (course_canonical, lesson_name)
            if key in seen_lessons:
                continue  # Already have a more recent version

            seen_lessons.add(key)
            results.append(
                _record_from_lesson_dir(lesson_dir, version_str, version_float, lp)
            )

    return results


def _resolve_course(lp: str, course_canonical: str, to_version: float, source: ContentSource) -> list[dict]:
    """
    Find all lessons in the most recent version of a specific course.

    Matches course folders whose canonical name (version stripped) equals course_canonical.
    """
    version_folders = _get_sorted_version_folders(source, descending=True)

    for version_float, version_str in version_folders:
        if version_float >= to_version:
            continue

        # All lessons under this version's LP (lesson_dirs, index.html-bearing,
        # variant-deduped), grouped by their course folder. Sorted to match the
        # legacy sorted(iterdir()) lesson ordering.
        lessons_by_course: dict[str, list[str]] = {}
        for lesson_dir in sorted(source.discover_lessons(version_str, lp)):
            lessons_by_course.setdefault(lesson_dir.split("/")[-2], []).append(lesson_dir)

        # Find a course folder matching the canonical name. list_courses() gives
        # the folder names in sorted order; the legacy code took the first
        # iterdir() match that yielded lessons.
        for course_folder in source.list_courses(version_str, lp):
            if course_folder.startswith("Clone of"):
                continue
            if strip_course_version(course_folder) != course_canonical:
                continue
            lesson_dirs = lessons_by_course.get(course_folder, [])
            if not lesson_dirs:
                continue
            # Found the most recent version of this course.
            return [
                _record_from_lesson_dir(ld, version_str, version_float, lp)
                for ld in lesson_dirs
            ]

    return []
