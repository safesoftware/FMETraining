#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from common import load_json, write_jsonl

RENAME_RE = re.compile(r"rename\s+['\"]([^'\"]+)['\"]\s+to\s+['\"]([^'\"]+)['\"]", re.IGNORECASE)


CHANGE_TYPES = [
    "label rename",
    "workflow change",
    "new field",
    "navigation change",
    "permissions",
    "other",
]


def choose_change_type(summary: str, description: str) -> str:
    txt = f"{summary} {description}".lower()
    if "rename" in txt or "label" in txt:
        return "label rename"
    if "workflow" in txt or "step" in txt:
        return "workflow change"
    if "field" in txt:
        return "new field"
    if "menu" in txt or "navigation" in txt:
        return "navigation change"
    if "permission" in txt or "role" in txt:
        return "permissions"
    return "other"


def flatten_description(desc: Any) -> str:
    if isinstance(desc, str):
        return desc
    if isinstance(desc, dict):
        out: list[str] = []
        for item in desc.get("content", []):
            out.extend(flatten_description(item).split("\n"))
        if desc.get("text"):
            out.append(str(desc["text"]))
        return "\n".join([x for x in out if x])
    if isinstance(desc, list):
        return "\n".join(flatten_description(x) for x in desc)
    return ""


def detect_ui_text_changes(summary: str, description: str) -> list[dict[str, Any]]:
    combined = f"{summary}\n{description}"
    matches = list(RENAME_RE.finditer(combined))
    out = []
    for m in matches:
        out.append({"old_label": m.group(1).strip(), "new_label": m.group(2).strip(), "context": "jira_text"})
    return out


def split_records(issue: dict[str, Any]) -> list[dict[str, Any]]:
    fields = issue.get("fields", {})
    key = issue.get("key", "UNKNOWN")
    summary = fields.get("summary") or ""
    description = flatten_description(fields.get("description"))
    release = None
    fix_versions = fields.get("fixVersions") or []
    if fix_versions:
        release = fix_versions[0].get("name")

    ui_changes = detect_ui_text_changes(summary, description)
    if not ui_changes:
        ui_changes = [{"old_label": None, "new_label": None, "context": "not_detected"}]

    records = []
    for idx, ui in enumerate(ui_changes, start=1):
        ctype = choose_change_type(summary, description)
        reason = "Detected explicit rename pattern" if ui.get("old_label") else "Insufficient structured UI details in Jira fields"
        rec = {
            "change_id": f"{key}-{idx}" if len(ui_changes) > 1 else key,
            "source": "jira",
            "release": release,
            "feature_area": (fields.get("components") or [{}])[0].get("name") if fields.get("components") else None,
            "user_visible_summary": summary[:280],
            "change_type": ctype,
            "ui_text_changes": [ui] if ui else [],
            "workflow_before": None,
            "workflow_after": None,
            "evidence": {
                "jira_key": key,
                "links": [],
                "fields_used": ["summary", "description", "components", "fixVersions"],
            },
            "docs_relevance_score": 0.9 if ctype in {"label rename", "workflow change", "navigation change"} else 0.6,
            "docs_relevance_reason": reason,
        }
        records.append(rec)
    return records


def validate_record(rec: dict[str, Any]) -> None:
    required = [
        "change_id",
        "source",
        "user_visible_summary",
        "change_type",
        "ui_text_changes",
        "evidence",
        "docs_relevance_score",
        "docs_relevance_reason",
    ]
    for r in required:
        if r not in rec:
            raise ValueError(f"missing required field: {r}")
    if rec["change_type"] not in CHANGE_TYPES:
        raise ValueError(f"invalid change_type: {rec['change_type']}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default="inputs/jira_snapshot.json")
    ap.add_argument("--out", default="artifacts/docs_change_ledger.jsonl")
    ap.add_argument("--min-docs-score", type=float, default=0.0)
    args = ap.parse_args()

    snapshot = load_json(args.infile)
    issues = snapshot.get("issues", [])

    records: list[dict[str, Any]] = []
    for issue in issues:
        split = split_records(issue)
        for rec in split:
            validate_record(rec)
            if rec["docs_relevance_score"] >= args.min_docs_score:
                records.append(rec)

    records = sorted(records, key=lambda r: r["change_id"])
    write_jsonl(args.out, records)
    print(f"Wrote {len(records)} change ledger records to {args.out}")


if __name__ == "__main__":
    main()
