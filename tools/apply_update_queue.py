#!/usr/bin/env python3
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common import dump_json, load_json, load_jsonl


def build_lookup(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {i[key]: i for i in items}


def build_spec(task: dict[str, Any], lesson: dict[str, Any], change: dict[str, Any]) -> dict[str, Any]:
    replacements = []
    for ui in change.get("ui_text_changes", []):
        if ui.get("old_label") and ui.get("new_label"):
            replacements.append(
                {
                    "action": "replace_text",
                    "old_text": ui["old_label"],
                    "new_text": ui["new_label"],
                    "evidence": change["change_id"],
                }
            )

    if not replacements:
        replacements.append(
            {
                "action": "insert_todo_marker",
                "marker": f"<!-- TODO(training-update): verify change {change['change_id']} - missing concrete UI labels -->",
                "evidence": change["change_id"],
            }
        )

    return {
        "schema_version": "1.0",
        "lesson_id": lesson["lesson_id"],
        "lesson_path": lesson["lesson_path"],
        "task_id": task["task_id"],
        "change_id": change["change_id"],
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "edits": replacements,
        "notes": [
            "Spec generated before applying edits.",
            "If no deterministic replacement exists, TODO marker is inserted.",
        ],
    }


def apply_spec_to_html(spec: dict[str, Any], dry_run: bool = False) -> tuple[int, bool]:
    html_path = Path(spec["lesson_path"])
    original = html_path.read_text(encoding="utf-8", errors="ignore")
    updated = original
    changes = 0

    for edit in spec.get("edits", []):
        if edit["action"] == "replace_text":
            old = edit["old_text"]
            new = edit["new_text"]
            if old in updated:
                count = updated.count(old)
                updated = updated.replace(old, new)
                changes += count
        elif edit["action"] == "insert_todo_marker":
            marker = edit["marker"]
            if marker not in updated:
                updated = marker + "\n" + updated
                changes += 1

    changed = updated != original
    if changed and not dry_run:
        html_path.write_text(updated, encoding="utf-8")
    return changes, changed


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", default="artifacts/update_queue.json")
    ap.add_argument("--manifest", default="artifacts/lesson_manifest.json")
    ap.add_argument("--ledger", default="artifacts/docs_change_ledger.jsonl")
    ap.add_argument("--lesson-id")
    ap.add_argument("--limit", type=int, default=1)
    ap.add_argument("--spec-dir", default="artifacts/update_specs")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    queue = load_json(args.queue)
    manifest = load_json(args.manifest)
    ledger = load_jsonl(args.ledger)

    lesson_by_id = build_lookup(manifest.get("lessons", []), "lesson_id")
    change_by_id = build_lookup(ledger, "change_id")

    tasks = queue.get("tasks", [])
    if args.lesson_id:
        tasks = [t for t in tasks if t.get("lesson_id") == args.lesson_id]
    tasks = tasks[: args.limit]

    spec_dir = Path(args.spec_dir)
    spec_dir.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        lesson = lesson_by_id[task["lesson_id"]]
        change = change_by_id[task["change_id"]]
        spec = build_spec(task, lesson, change)
        spec_path = spec_dir / f"{lesson['lesson_id']}.json"
        dump_json(spec_path, spec)
        changes, changed = apply_spec_to_html(spec, dry_run=args.dry_run)
        state = "DRY-RUN" if args.dry_run else ("CHANGED" if changed else "NO-CHANGE")
        print(f"{state}: {task['lesson_id']} (edits_applied={changes}) spec={spec_path}")


if __name__ == "__main__":
    main()
