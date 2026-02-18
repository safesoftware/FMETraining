#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from typing import Any

from common import write_jsonl

JIRA_KEY_RE = re.compile(r"\b([A-Z][A-Z0-9]+-\d+)\b")


def make_record(change_id: str, summary: str, source: str, release: str | None = None) -> dict[str, Any]:
    return {
        "change_id": change_id,
        "source": source,
        "release": release,
        "feature_area": None,
        "user_visible_summary": summary,
        "change_type": "other",
        "ui_text_changes": [],
        "workflow_before": None,
        "workflow_after": None,
        "evidence": {"jira_key": change_id if "-" in change_id else None, "links": [], "fields_used": ["input"]},
        "docs_relevance_score": 0.5,
        "docs_relevance_reason": "Loaded from generic input; needs triage.",
    }


def parse_markdown(path: Path) -> list[dict[str, Any]]:
    records = []
    idx = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip().startswith(("-", "*")):
            continue
        idx += 1
        key_match = JIRA_KEY_RE.search(line)
        key = key_match.group(1) if key_match else f"MD-{idx}"
        summary = re.sub(r"^[\-*]\s*", "", line).strip()
        records.append(make_record(key, summary, "markdown"))
    return records


def parse_jira_json(path: Path) -> list[dict[str, Any]]:
    doc = json.loads(path.read_text(encoding="utf-8"))
    issues = doc.get("issues", doc if isinstance(doc, list) else [])
    records = []
    for issue in issues:
        key = issue.get("key", "UNKNOWN")
        fields = issue.get("fields", {})
        summary = fields.get("summary", "")
        release = (fields.get("fixVersions") or [{}])[0].get("name") if fields.get("fixVersions") else None
        records.append(make_record(key, summary, "jira_json", release=release))
    return records


def parse_jira_csv(path: Path) -> list[dict[str, Any]]:
    records = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            key = row.get("Issue key") or row.get("Key") or f"CSV-{i}"
            summary = row.get("Summary") or row.get("Issue summary") or ""
            release = row.get("Fix versions") or row.get("Fix Version/s")
            records.append(make_record(key, summary, "jira_csv", release=release))
    return records


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True)
    ap.add_argument("--type", choices=["markdown", "jira_json", "jira_csv"], required=True)
    ap.add_argument("--out", default="artifacts/docs_change_ledger.jsonl")
    args = ap.parse_args()

    path = Path(args.infile)
    if args.type == "markdown":
        records = parse_markdown(path)
    elif args.type == "jira_json":
        records = parse_jira_json(path)
    else:
        records = parse_jira_csv(path)

    write_jsonl(args.out, records)
    print(f"Wrote {len(records)} records to {args.out}")


if __name__ == "__main__":
    main()
