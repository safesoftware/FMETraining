"""
Utility functions for the FME Training Update Pipeline.

Covers: run ID generation, version parsing, path helpers, runs registry.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from pipeline.config import (
    COURSE_VERSION_SUFFIX_PATTERN,
)


# ---------------------------------------------------------------------------
# Run ID
# ---------------------------------------------------------------------------

def generate_run_id() -> str:
    """Generate a unique run ID: '{YYYYMMDDTHHmmss}-{hex4}'."""
    ts = datetime.now(tz=timezone.utc).strftime("%Y%m%dT%H%M%S")
    suffix = uuid.uuid4().hex[:4]
    return f"{ts}-{suffix}"


# ---------------------------------------------------------------------------
# Version parsing
# ---------------------------------------------------------------------------

def parse_version(version_str: str) -> float | None:
    """
    Parse an FME version string to a comparable float.

    Handles:
      "2025.0"   -> 2025.0
      "2025.1"   -> 2025.1
      "2025.2.1" -> 2025.2  (patch trimmed)
      "2026.1"   -> 2026.1  (FME 2026+ uses quarterly releases: .1–.4, no .0)
      Garbage    -> None

    The strategy is: take the first two numeric components separated by '.',
    form "MAJOR.MINOR", and return as float. Non-numeric or missing components
    yield None.
    """
    if not version_str or not isinstance(version_str, str):
        return None
    parts = version_str.strip().split(".")
    if len(parts) < 2:
        return None
    try:
        major = int(parts[0])
        # Minor may be a build number like "025058"; we only keep real minor versions
        # (0-99). If it looks like a build number (> 99), skip.
        minor_raw = parts[1]
        minor = int(minor_raw)
        if minor > 99:
            return None
        return float(f"{major}.{minor}")
    except (ValueError, IndexError):
        return None


def version_in_range(version_float: float, from_version: float, to_version: float) -> bool:
    """
    Return True if from_version < version_float <= to_version.

    Exclusive lower bound: we want changes that occurred AFTER the source content.
    Inclusive upper bound: we want up to and including the target version.
    """
    return from_version < version_float <= to_version


def sort_key_version(version_str: str) -> float:
    """Return a sortable float for a version string; unparseable → -1."""
    v = parse_version(version_str)
    return v if v is not None else -1.0


# ---------------------------------------------------------------------------
# Path & name helpers
# ---------------------------------------------------------------------------

def strip_course_version(course_folder_name: str) -> str:
    """
    Strip the version suffix from a course folder name.

    'Connect To Data 2025.0'                   -> 'Connect To Data'
    'Build a Library of Custom Transformers 2025.1' -> 'Build a Library of Custom Transformers'
    'No Version Suffix'                         -> 'No Version Suffix'
    """
    return COURSE_VERSION_SUFFIX_PATTERN.sub("", course_folder_name).strip()


def parse_lesson_path(rel_path: str) -> dict:
    """
    Parse a relative lesson path into its component parts.

    Expected format: '{version}/{learning_path}/{course_folder}/{lesson_folder}/index.html'

    Returns a dict with:
        version_str, from_version, learning_path,
        course, course_canonical, lesson_name

    Raises ValueError if the path does not match the expected depth or
    the version component is not a valid FME version.
    """
    # Normalise separators
    parts = Path(rel_path).parts
    if len(parts) < 5:
        raise ValueError(
            f"Lesson path too shallow (expected 5 parts: version/lp/course/lesson/index.html): {rel_path}"
        )

    version_str = parts[0]
    from_version = parse_version(version_str)
    if from_version is None:
        raise ValueError(f"Cannot parse version from path component '{version_str}': {rel_path}")

    learning_path = parts[1]
    course = parts[2]
    lesson_name = parts[3]
    course_canonical = strip_course_version(course)

    return {
        "version": version_str,       # canonical name used in manifest entries
        "version_str": version_str,   # alias kept for internal callers
        "from_version": from_version,
        "learning_path": learning_path,
        "course": course,
        "course_canonical": course_canonical,
        "lesson_name": lesson_name,
    }


def lesson_id(version: str, learning_path: str, course_canonical: str, lesson_name: str) -> str:
    """
    Build a stable, human-readable lesson identifier.

    Format: '{version}/{learning_path}/{course_canonical}/{lesson_name}'
    Uses forward slashes regardless of OS (logical ID, not filesystem path).
    """
    return "/".join([version, learning_path, course_canonical, lesson_name])


# ---------------------------------------------------------------------------
# Artifact path helpers
# ---------------------------------------------------------------------------

def manifest_path(run_id: str, output_dir: Path) -> Path:
    return output_dir / f"manifest-{run_id}.json"


def changelog_path(run_id: str, output_dir: Path) -> Path:
    return output_dir / f"changelog-{run_id}.json"


def recommendations_path(run_id: str, output_dir: Path) -> Path:
    return output_dir / f"update-recommendations-{run_id}.json"


def report_path(run_id: str, output_dir: Path) -> Path:
    return output_dir / f"report-{run_id}.html"


def edit_plans_path(run_id: str, output_dir: Path) -> Path:
    return output_dir / f"edit-plans-{run_id}.json"


# ---------------------------------------------------------------------------
# Runs registry
# ---------------------------------------------------------------------------

def _runs_registry_path(output_dir: Path) -> Path:
    return output_dir / "runs.json"


def _load_runs(output_dir: Path) -> dict:
    path = _runs_registry_path(output_dir)
    if path.exists():
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    return {"runs": []}


def _save_runs(data: dict, output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = _runs_registry_path(output_dir)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def register_run(run_id: str, job: dict, output_dir: Path) -> None:
    """Append a new run entry to artifacts/runs.json."""
    data = _load_runs(output_dir)
    entry = {
        "run_id": run_id,
        "started_at": datetime.now(tz=timezone.utc).isoformat(),
        "job": job,
        "steps_completed": [],
        "artifacts": {
            "manifest": f"manifest-{run_id}.json",
            "changelog": f"changelog-{run_id}.json",
            "recommendations": f"update-recommendations-{run_id}.json",
            "edit_plans": f"edit-plans-{run_id}.json",
            "report": f"report-{run_id}.html",
        },
    }
    data["runs"].append(entry)
    _save_runs(data, output_dir)


def mark_step_complete(run_id: str, step: int, output_dir: Path) -> None:
    """Record a completed step number for a run in runs.json."""
    data = _load_runs(output_dir)
    for run in data["runs"]:
        if run["run_id"] == run_id:
            if step not in run["steps_completed"]:
                run["steps_completed"].append(step)
                run["steps_completed"].sort()
            break
    _save_runs(data, output_dir)


def get_completed_steps(run_id: str, output_dir: Path) -> list[int]:
    """Return the list of completed step numbers for a run."""
    data = _load_runs(output_dir)
    for run in data["runs"]:
        if run["run_id"] == run_id:
            return run.get("steps_completed", [])
    return []


def get_run_job(run_id: str, output_dir: Path) -> dict | None:
    """Return the job dict for a run, or None if not found."""
    data = _load_runs(output_dir)
    for run in data["runs"]:
        if run["run_id"] == run_id:
            return run.get("job")
    return None
