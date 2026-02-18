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
    return load_json(path)


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


def filter_lessons(
    lessons: list[dict[str, Any]],
    from_version: str | None,
    to_version: str | None,
    courses: list[str],
) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for lesson in lessons:
        meta = infer_metadata(lesson)
        version = meta.get("version")
        course_path = meta.get("course_path") or ""
        course_name = meta.get("course") or ""

        # We only update target-version lessons; from_version is included as run metadata.
        if to_version and version != to_version:
            continue

        if courses:
            if not any(fnmatch.fnmatch(course_path, pat) or fnmatch.fnmatch(course_name, pat) or pat in course_path for pat in courses):
                continue
        out.append(lesson)
    return out


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
    courses = normalize_list(args.courses) or scope_file.get("courses", [])

    scoped_lessons = filter_lessons(lessons, from_version, to_version, courses)

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
            }
            tasks.append(task)

    tasks.sort(key=lambda t: (-t["confidence"], t["task_id"]))
    queue = {
        "schema_version": "1.1",
        "task_count": len(tasks),
        "scope": {
            "from_version": from_version,
            "to_version": to_version,
            "courses": courses,
            "scoped_lesson_count": len(scoped_lessons),
            "total_manifest_lessons": len(lessons),
        },
        "tasks": tasks,
    }
    validate_queue(queue)

    if args.dry_run:
        print(json.dumps({"scope": queue["scope"], "task_count": len(tasks), "sample": tasks[:3]}, indent=2))
        return

    dump_json(args.out, queue)
    print(f"Wrote {len(tasks)} update tasks to {args.out}")


if __name__ == "__main__":
    main()
