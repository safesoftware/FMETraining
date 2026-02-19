#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
from typing import Any

from common import dump_json, load_json, load_jsonl

VERSION_RE = re.compile(r"^\d{4}\.\d+$")


def lesson_text_blob(lesson: dict[str, Any]) -> str:
    parts = [lesson.get("title", "")]
    parts.extend(lesson.get("headings", []))
    parts.extend(lesson.get("ui_strings", []))
    return "\n".join(parts).lower()


def score_lesson_change(lesson: dict[str, Any], change: dict[str, Any]) -> float:
    score = 0.1
    blob = lesson_text_blob(lesson)
    summary = (change.get("user_visible_summary") or "").lower()
    for token in summary.split():
        if len(token) > 4 and token in blob:
            score += 0.08
    for ui in change.get("ui_text_changes", []):
        old = (ui.get("old_label") or "").lower()
        new = (ui.get("new_label") or "").lower()
        if old and old in blob:
            score += 0.4
        if new and new in blob:
            score += 0.2
    return max(0.0, min(1.0, score))


def required_update_types(change: dict[str, Any], confidence: float) -> list[str]:
    ctype = change.get("change_type")
    out = ["text edits"]
    if ctype == "workflow change":
        out.append("exercise step edits")
    if ctype in {"label rename", "navigation change", "workflow change"} and confidence >= 0.35:
        out.append("screenshot updates")
    return sorted(set(out))


def parse_scope_file(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        doc = load_json(path)
    except Exception as exc:
        raise ValueError(f"malformed scope file '{path}': {exc}") from exc
    if not isinstance(doc, dict):
        raise ValueError(f"malformed scope file '{path}': expected a JSON object")
    return doc


def infer_metadata(lesson: dict[str, Any]) -> dict[str, Any]:
    meta = lesson.get("metadata") or {}
    if meta.get("version") and meta.get("course"):
        return meta
    p = lesson.get("lesson_path", "")
    parts = p.split("/")
    return {
        "version": parts[0] if parts and VERSION_RE.match(parts[0]) else None,
        "course": parts[2] if len(parts) > 2 else None,
        "course_path": "/".join(parts[:3]) if len(parts) > 2 else None,
    }


def normalize_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [x.strip() for x in value.split(",") if x.strip()]


def normalize_scope_path(value: str) -> str:
    normalized = value.replace("\\", "/").strip()
    while "//" in normalized:
        normalized = normalized.replace("//", "/")
    return normalized.strip("/")


def normalize_course_scope(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        raw = normalize_list(value)
    elif isinstance(value, list):
        if not all(isinstance(v, str) for v in value):
            raise ValueError("malformed scope file: courses must contain only strings")
        raw = value
    else:
        raise ValueError("malformed scope file: courses must be a list of strings")
    return [normalize_scope_path(v) for v in raw if normalize_scope_path(v)]


def matches_course_pattern(course_path: str, course_name: str, from_version: str, pattern: str) -> bool:
    cp = normalize_scope_path(course_path)
    cn = normalize_scope_path(course_name)
    pat = normalize_scope_path(pattern)
    cp_rel = cp[len(from_version) + 1 :] if cp.startswith(f"{from_version}/") else cp
    return (
        fnmatch.fnmatch(cp, pat)
        or fnmatch.fnmatch(cp_rel, pat)
        or fnmatch.fnmatch(cn, pat)
        or pat in cp
        or pat in cp_rel
        or pat in cn
    )


def select_scoped_lessons(
    lessons: list[dict[str, Any]],
    from_version: str | None,
    courses: list[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if not from_version:
        raise ValueError("from_version is required (CLI --from-version or scope file)")

    lesson_meta = [(lesson, infer_metadata(lesson)) for lesson in lessons]
    available_versions = sorted({m.get("version") for _, m in lesson_meta if m.get("version")})
    if from_version not in available_versions:
        versions = ", ".join(available_versions) if available_versions else "(none)"
        raise ValueError(f"from_version not found in manifest: {from_version} (available: {versions})")

    from_version_rows = [(lesson, meta) for lesson, meta in lesson_meta if meta.get("version") == from_version]
    from_version_lessons = [lesson for lesson, _ in from_version_rows]
    from_version_lesson_count = len(from_version_lessons)

    course_paths = sorted(
        {
            normalize_scope_path(meta.get("course_path"))
            for _, meta in from_version_rows
            if meta.get("course_path")
        }
    )
    normalized_courses = [normalize_scope_path(c) for c in courses if normalize_scope_path(c)]

    if normalized_courses:
        matched_source_courses = sorted(
            {
                cp
                for cp in course_paths
                if any(matches_course_pattern(cp, cp.split("/")[-1], from_version, pattern) for pattern in normalized_courses)
            }
        )
        if not matched_source_courses:
            joined = ", ".join(normalized_courses)
            raise ValueError(
                f"none of the specified courses found under from_version {from_version}: [{joined}]"
            )
        matched_set = set(matched_source_courses)
        scoped = [
            lesson
            for lesson, meta in from_version_rows
            if meta.get("course_path") and normalize_scope_path(meta.get("course_path")) in matched_set
        ]
    else:
        matched_source_courses = course_paths
        scoped = from_version_lessons

    summary = {
        "from_version_lesson_count": from_version_lesson_count,
        "matched_source_course_count": len(matched_source_courses),
        "matched_source_lesson_count": len(scoped),
        "courses": normalized_courses,
    }
    return scoped, summary


def validate_queue(queue: dict[str, Any]) -> None:
    if not isinstance(queue.get("tasks"), list):
        raise ValueError("update_queue.tasks must be a list")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="artifacts/lesson_manifest.json")
    ap.add_argument("--ledger", default="artifacts/docs_change_ledger.jsonl")
    ap.add_argument("--out", default="artifacts/update_queue.json")
    ap.add_argument("--from-version", help="Archived source version context, e.g. 2024.0")
    ap.add_argument("--to-version", help="Target version to update, e.g. 2025.0")
    ap.add_argument("--courses", help="Comma-separated course names/patterns or path fragments")
    ap.add_argument("--scope-file", help="JSON file containing from_version, to_version, courses[]")
    ap.add_argument("--min-confidence", type=float, default=0.25)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest = load_json(args.manifest)
    ledger = load_jsonl(args.ledger)
    lessons = manifest.get("lessons", [])

    scope_file = parse_scope_file(args.scope_file)
    from_version = args.from_version or scope_file.get("from_version")
    to_version = args.to_version or scope_file.get("to_version")
    scope_courses = normalize_course_scope(scope_file.get("courses"))
    courses = normalize_course_scope(args.courses) or scope_courses
    scoped_lessons, scope_summary = select_scoped_lessons(lessons, from_version, courses)

    tasks = []
    for change in ledger:
        for lesson in scoped_lessons:
            confidence = score_lesson_change(lesson, change)
            if confidence < args.min_confidence:
                continue
            update_types = required_update_types(change, confidence)
            task = {
                "task_id": f"{change['change_id']}::{lesson['lesson_id']}",
                "change_id": change["change_id"],
                "lesson_id": lesson["lesson_id"],
                "lesson_path": lesson["lesson_path"],
                "confidence": round(confidence, 3),
                "required_update_types": update_types,
                "likely_stale_screenshots": [
                    i["filename"]
                    for i in lesson.get("image_references", [])
                    if i.get("filename") and "screenshot updates" in update_types
                ],
                "metadata": {
                    "source_version": from_version,
                    "target_version_intent": to_version,
                    "source_course_path": (lesson.get("metadata") or {}).get("course_path"),
                },
            }
            tasks.append(task)

    tasks.sort(key=lambda t: (-t["confidence"], t["task_id"]))
    queue = {
        "schema_version": "1.2",
        "task_count": len(tasks),
        "scope": {
            "from_version": from_version,
            "to_version": to_version,
            "courses": scope_summary["courses"],
            "source_filter": {
                "version": from_version,
                "courses": scope_summary["courses"],
                "from_version_lesson_count": scope_summary["from_version_lesson_count"],
                "matched_source_course_count": scope_summary["matched_source_course_count"],
                "matched_source_lesson_count": scope_summary["matched_source_lesson_count"],
            },
            "target_intent": {
                "to_version": to_version,
            },
            "scoped_lesson_count": scope_summary["matched_source_lesson_count"],
            "total_manifest_lessons": len(lessons),
        },
        "tasks": tasks,
    }
    validate_queue(queue)

    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run_summary": {
                        "from_version_lesson_count": scope_summary["from_version_lesson_count"],
                        "matched_source_course_count": scope_summary["matched_source_course_count"],
                        "matched_source_lesson_count": scope_summary["matched_source_lesson_count"],
                        "target_to_version_intent": to_version,
                    },
                    "scope": queue["scope"],
                    "task_count": len(tasks),
                    "sample": tasks[:3],
                },
                indent=2,
            )
        )
        return

    dump_json(args.out, queue)
    print(f"Wrote {len(tasks)} update tasks to {args.out}")


if __name__ == "__main__":
    main()
