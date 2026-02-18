#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from common import dump_json, load_json, load_jsonl


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


def validate_queue(queue: dict[str, Any]) -> None:
    if not isinstance(queue.get("tasks"), list):
        raise ValueError("update_queue.tasks must be a list")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--manifest", default="artifacts/lesson_manifest.json")
    ap.add_argument("--ledger", default="artifacts/docs_change_ledger.jsonl")
    ap.add_argument("--out", default="artifacts/update_queue.json")
    ap.add_argument("--min-confidence", type=float, default=0.25)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    manifest = load_json(args.manifest)
    ledger = load_jsonl(args.ledger)
    lessons = manifest.get("lessons", [])

    tasks = []
    for change in ledger:
        for lesson in lessons:
            confidence = score_lesson_change(lesson, change)
            if confidence < args.min_confidence:
                continue
            task = {
                "task_id": f"{change['change_id']}::{lesson['lesson_id']}",
                "change_id": change["change_id"],
                "lesson_id": lesson["lesson_id"],
                "lesson_path": lesson["lesson_path"],
                "confidence": round(confidence, 3),
                "required_update_types": required_update_types(change, confidence),
                "likely_stale_screenshots": [
                    i["filename"]
                    for i in lesson.get("image_references", [])
                    if i.get("filename") and "screenshot updates" in required_update_types(change, confidence)
                ],
            }
            tasks.append(task)

    tasks.sort(key=lambda t: (-t["confidence"], t["task_id"]))
    queue = {"schema_version": "1.0", "task_count": len(tasks), "tasks": tasks}
    validate_queue(queue)

    if args.dry_run:
        print({"task_count": len(tasks), "sample": tasks[:3]})
        return

    dump_json(args.out, queue)
    print(f"Wrote {len(tasks)} update tasks to {args.out}")


if __name__ == "__main__":
    main()
