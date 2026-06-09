"""
Step 1: Build the Lesson Manifest.

Resolves the update-job.json scope to a list of lesson paths, parses each
HTML file, and writes artifacts/manifest-{RUN_ID}.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from tqdm import tqdm

from pipeline.config import (
    VERSION_FOLDER_PATTERN,
    load_product_mapping,
)
from pipeline.html_parser import parse_lesson_html
from pipeline.utils import (
    lesson_id,
    manifest_path,
    parse_lesson_path,
    parse_version,
    strip_course_version,
)


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

    # Resolve scope → list of lesson record dicts
    print("\n[Step 1] Resolving scope...")
    lesson_records = _resolve_scope(job["scope"], to_version, repo_root)

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
        html_path = repo_root / record["path"]
        parsed = parse_lesson_html(html_path)

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

def _resolve_scope(scope: dict, to_version: float, repo_root: Path) -> list[dict]:
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
        if not (repo_root / rel_path).exists():
            print(f"  WARNING: Lesson path not found on disk, skipping: {rel_path}")
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
        records = _resolve_course(lp, course_canonical, to_version, repo_root)
        for r in records:
            add_record(r)

    # --- Learning path scope ---
    for lp in scope.get("learning_paths", []):
        records = _resolve_learning_path(lp, to_version, repo_root)
        for r in records:
            add_record(r)

    return results


def _get_sorted_version_folders(repo_root: Path, descending: bool = True) -> list[tuple[float, str]]:
    """
    Return a list of (version_float, folder_name) for all valid version directories,
    sorted by version float.
    """
    folders = []
    for entry in repo_root.iterdir():
        if entry.is_dir() and VERSION_FOLDER_PATTERN.match(entry.name):
            v = parse_version(entry.name)
            if v is not None:
                folders.append((v, entry.name))
    folders.sort(key=lambda x: x[0], reverse=descending)
    return folders


def _resolve_learning_path(lp: str, to_version: float, repo_root: Path) -> list[dict]:
    """
    Find all lessons in the most recent version of each unique lesson under a learning path.

    For each (course_canonical, lesson_name) pair, pick the highest version < to_version.
    """
    version_folders = _get_sorted_version_folders(repo_root, descending=True)
    seen_lessons: set[tuple] = set()
    results: list[dict] = []

    for version_float, version_str in version_folders:
        if version_float >= to_version:
            continue

        lp_dir = repo_root / version_str / lp
        if not lp_dir.is_dir():
            continue

        for course_dir in sorted(lp_dir.iterdir()):
            if not course_dir.is_dir():
                continue
            # Skip "Clone of" courses
            if course_dir.name.startswith("Clone of"):
                continue

            course_canonical = strip_course_version(course_dir.name)

            for lesson_dir in sorted(course_dir.iterdir()):
                if not lesson_dir.is_dir():
                    continue
                index_path = lesson_dir / "index.html"
                if not index_path.exists():
                    continue

                key = (course_canonical, lesson_dir.name)
                if key in seen_lessons:
                    continue  # Already have a more recent version

                seen_lessons.add(key)
                rel_path = index_path.relative_to(repo_root).as_posix()
                results.append({
                    "path": rel_path,
                    "version": version_str,
                    "version_str": version_str,
                    "from_version": version_float,
                    "learning_path": lp,
                    "course": course_dir.name,
                    "course_canonical": course_canonical,
                    "lesson_name": lesson_dir.name,
                })

    return results


def _resolve_course(lp: str, course_canonical: str, to_version: float, repo_root: Path) -> list[dict]:
    """
    Find all lessons in the most recent version of a specific course.

    Matches course folders whose canonical name (version stripped) equals course_canonical.
    """
    version_folders = _get_sorted_version_folders(repo_root, descending=True)

    for version_float, version_str in version_folders:
        if version_float >= to_version:
            continue

        lp_dir = repo_root / version_str / lp
        if not lp_dir.is_dir():
            continue

        # Find a course folder matching the canonical name
        for course_dir in lp_dir.iterdir():
            if not course_dir.is_dir():
                continue
            if course_dir.name.startswith("Clone of"):
                continue
            if strip_course_version(course_dir.name) == course_canonical:
                # Found the most recent version of this course
                records = []
                for lesson_dir in sorted(course_dir.iterdir()):
                    if not lesson_dir.is_dir():
                        continue
                    index_path = lesson_dir / "index.html"
                    if not index_path.exists():
                        continue
                    rel_path = index_path.relative_to(repo_root).as_posix()
                    records.append({
                        "path": rel_path,
                        "version": version_str,
                        "version_str": version_str,
                        "from_version": version_float,
                        "learning_path": lp,
                        "course": course_dir.name,
                        "course_canonical": course_canonical,
                        "lesson_name": lesson_dir.name,
                    })
                if records:
                    return records

    return []
