#!/usr/bin/env python3
"""
Skilljar sync helper — generates a draft skilljar-mapping.json by fetching
courses and lessons from the Skilljar API, then auto-matching them to local
lesson IDs by extracting the version string from the course title and walking
the local repo tree.

Usage:
    python skilljar_sync.py --list-courses
    python skilljar_sync.py --generate-mapping
    python skilljar_sync.py --generate-mapping --output path/to/mapping.json

Auto-matched entries use the local lesson ID as the key:
    "2024.2/fme-form-basic/Connect To Data 2024.2/Connect and View Data": { ... }

Entries that couldn't be matched fall back to "UNMAPPED/<Course>/<Lesson>" keys.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).parent.resolve()

try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env")
except ImportError:
    pass

SKILLJAR_API_BASE = "https://api.skilljar.com/v1"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "skilljar-mapping.json"

# Matches a trailing FME version like " 2024.2" or " 2026.1" at end of a title
_VERSION_SUFFIX_RE = re.compile(r"\s+(\d{4}\.\d+)$")


# ---------------------------------------------------------------------------
# Auth / HTTP helpers
# ---------------------------------------------------------------------------

def _api_key() -> str:
    key = os.getenv("SKILLJAR_API_KEY", "")
    if not key:
        print("ERROR: SKILLJAR_API_KEY not set in .env", file=sys.stderr)
        sys.exit(1)
    return key


def _auth_header(api_key: str) -> str:
    token = base64.b64encode(f"{api_key}:".encode()).decode()
    return f"Basic {token}"


def _get(path: str, api_key: str) -> dict | list:
    url = f"{SKILLJAR_API_BASE}{path}"
    req = urllib.request.Request(
        url,
        headers={"Authorization": _auth_header(api_key), "Accept": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _paginated(path: str, api_key: str) -> list[dict]:
    results = []
    url_path = path
    while url_path:
        data = _get(url_path, api_key)
        if isinstance(data, list):
            return data
        results.extend(data.get("results", []))
        next_url = data.get("next")
        if next_url:
            url_path = next_url.replace(SKILLJAR_API_BASE, "")
        else:
            url_path = None
    return results


# ---------------------------------------------------------------------------
# Local repo matching
# ---------------------------------------------------------------------------

def _extract_version(course_title: str) -> tuple[str, str] | tuple[None, None]:
    """
    Extract (version, canonical_name) from a Skilljar course title.
    "Connect To Data 2024.2" → ("2024.2", "Connect To Data")
    Returns (None, None) if no version suffix found.
    """
    m = _VERSION_SUFFIX_RE.search(course_title)
    if m:
        return m.group(1), course_title[: m.start()].strip()
    return None, None


def _normalize(s: str) -> str:
    """Lowercase + collapse underscores/colons/extra spaces for fuzzy name matching."""
    s = s.lower().strip()
    s = re.sub(r"[_:]+", " ", s)
    s = re.sub(r"\s+", " ", s)
    return s


def _find_local_lesson(
    lesson_title: str, version: str, canonical_course: str, repo_root: Path
) -> str | None:
    """
    Walk repo_root/{version}/ to find a lesson folder matching the given
    canonical course name and lesson title.

    Returns "version/lp/course_folder/lesson_folder" or None if not found.
    """
    version_dir = repo_root / version
    if not version_dir.is_dir():
        return None

    norm_lesson = _normalize(lesson_title)
    norm_course = _normalize(canonical_course)

    for lp_dir in sorted(version_dir.iterdir()):
        if not lp_dir.is_dir():
            continue
        for course_dir in sorted(lp_dir.iterdir()):
            if not course_dir.is_dir():
                continue
            # Strip version suffix from folder name to get canonical course name
            course_canonical = _VERSION_SUFFIX_RE.sub("", course_dir.name).strip()
            if _normalize(course_canonical) != norm_course:
                continue
            for lesson_dir in sorted(course_dir.iterdir()):
                if not lesson_dir.is_dir():
                    continue
                if not (lesson_dir / "index.html").exists():
                    continue
                if _normalize(lesson_dir.name) == norm_lesson:
                    return f"{version}/{lp_dir.name}/{course_dir.name}/{lesson_dir.name}"

    return None


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_list_courses(api_key: str) -> None:
    courses = _paginated("/courses", api_key)
    print(f"{'ID':<36} Title")
    print("-" * 72)
    for c in courses:
        print(f"{c.get('id', ''):<36} {c.get('title', '')}")
    print(f"\n{len(courses)} course(s) found.")


def cmd_generate_mapping(api_key: str, output_path: Path) -> None:
    existing: dict = {}
    if output_path.exists():
        with open(output_path, encoding="utf-8") as f:
            existing = json.load(f)
        print(f"Loaded {len(existing)} existing mapping entries from {output_path}")

    courses = _paginated("/courses", api_key)
    print(f"Found {len(courses)} course(s)\n")

    draft: dict[str, dict] = {}
    auto_mapped = 0
    unmapped_count = 0

    for course in courses:
        course_id = course.get("id", "")
        course_title = course.get("title", "")
        version, canonical = _extract_version(course_title)

        print(f"  {course_title!r}", end="")
        if version:
            print(f"  [v{version}]", end="")
        print()

        try:
            lessons = _paginated(f"/lessons?course_id={course_id}", api_key)
        except urllib.error.HTTPError as exc:
            print(f"    SKIPPED (HTTP {exc.code})")
            continue

        for lesson in lessons:
            lesson_id = lesson.get("id", "")
            lesson_title = lesson.get("title", "")
            entry = {
                "skilljar_lesson_id": lesson_id,
                "skilljar_course_id": course_id,
                "_title": lesson_title,
                "_course_title": course_title,
            }

            local_id = None
            if version and canonical:
                local_id = _find_local_lesson(lesson_title, version, canonical, REPO_ROOT)

            if local_id:
                draft[local_id] = entry
                auto_mapped += 1
            else:
                draft[f"UNMAPPED/{course_title}/{lesson_title}"] = entry
                unmapped_count += 1

    # Draft is the base; only non-UNMAPPED existing entries win (manual corrections).
    # Old UNMAPPED entries are discarded — draft already has the best key for each lesson.
    merged = dict(draft)
    for k, v in existing.items():
        if not k.startswith("UNMAPPED/"):
            merged[k] = v  # user-edited key takes precedence over auto-mapped

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\nWritten to: {output_path}")
    print(f"  {auto_mapped} auto-mapped to local lesson IDs")
    print(f"  {unmapped_count} UNMAPPED (no version suffix, or no local content match)")
    if unmapped_count:
        print('  Replace UNMAPPED/... keys manually:')
        print('    "2024.2/fme-form-basic/Connect To Data 2024.2/My Lesson": { ... }')


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Skilljar API sync — generates draft skilljar-mapping.json",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--list-courses", action="store_true", help="List all Skilljar courses")
    parser.add_argument(
        "--generate-mapping",
        action="store_true",
        help="Fetch courses + lessons and auto-match to local lesson IDs",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help=f"Output path for --generate-mapping (default: {DEFAULT_OUTPUT})",
    )
    args = parser.parse_args()

    api_key = _api_key()

    if args.list_courses:
        cmd_list_courses(api_key)
    elif args.generate_mapping:
        cmd_generate_mapping(api_key, Path(args.output))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
