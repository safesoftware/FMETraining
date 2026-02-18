#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

from common import dump_json, load_json


def load_field_map(path: str) -> dict[str, Any]:
    return load_json(path)


def split_multi(value: str, delimiters: list[str]) -> list[str]:
    if not value:
        return []
    vals = [value]
    for delim in delimiters:
        next_vals: list[str] = []
        for item in vals:
            next_vals.extend(item.split(delim))
        vals = next_vals
    return [v.strip() for v in vals if v.strip()]


def find_column(row: dict[str, str], aliases: list[str]) -> str | None:
    for alias in aliases:
        if alias in row:
            return alias
    lowered = {k.lower(): k for k in row.keys()}
    for alias in aliases:
        key = lowered.get(alias.lower())
        if key:
            return key
    return None


def normalize_issue_from_row(
    row: dict[str, str],
    field_map: dict[str, Any],
    resolved_columns: dict[str, str | None],
) -> dict[str, Any]:
    canonical = field_map["canonical_fields"]
    delims = field_map.get("multi_value_delimiters", [",", ";"])

    def get_value(name: str) -> str:
        col = resolved_columns.get(name)
        if not col:
            return ""
        return (row.get(col) or "").strip()

    key = get_value("key")
    summary = get_value("summary")
    description = get_value("description")
    issue_type = get_value("issue_type")
    parent = get_value("parent")
    components = split_multi(get_value("components"), delims)
    fix_versions = split_multi(get_value("fixVersions"), delims)
    labels = split_multi(get_value("labels"), delims)
    status = get_value("status")
    created = get_value("created")
    updated = get_value("updated")

    return {
        "key": key,
        "fields": {
            "summary": summary,
            "description": description,
            "issuetype": {"name": issue_type} if issue_type else None,
            "parent": {"key": parent} if parent else None,
            "components": [{"name": c} for c in components],
            "fixVersions": [{"name": v} for v in fix_versions],
            "labels": labels,
            "status": {"name": status} if status else None,
            "created": created or None,
            "updated": updated or None,
        },
    }


def normalize_csv(infile: Path, field_map: dict[str, Any]) -> dict[str, Any]:
    with infile.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        raise ValueError("CSV is empty and contains no Jira issues.")

    canonical = field_map["canonical_fields"]
    first_row = rows[0]
    resolved_columns = {name: find_column(first_row, aliases) for name, aliases in canonical.items()}

    missing_required = [name for name in field_map.get("required_canonical_fields", []) if not resolved_columns.get(name)]
    if missing_required:
        recommendations = ", ".join(field_map.get("recommended_jira_export_columns", []))
        missing_cols = ", ".join(missing_required)
        raise ValueError(
            f"Missing required Jira CSV canonical fields: {missing_cols}. "
            f"Include equivalent Jira export columns. Recommended columns: {recommendations}"
        )

    issues = [normalize_issue_from_row(row, field_map, resolved_columns) for row in rows]
    issues = [issue for issue in issues if issue.get("key")]
    issues = sorted(issues, key=lambda i: i.get("key", ""))

    return {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "source": {
            "type": "jira_csv_export",
            "input_path": infile.as_posix(),
            "field_map": "tools/jira_field_map.json",
            "resolved_columns": resolved_columns,
        },
        "issues": issues,
    }


def normalize_json(infile: Path) -> dict[str, Any]:
    doc = load_json(infile)
    if isinstance(doc, dict) and "issues" in doc and isinstance(doc["issues"], list):
        issues = doc["issues"]
    elif isinstance(doc, list):
        issues = doc
    else:
        raise ValueError("Unsupported Jira JSON format. Expected object with issues[] or list of issues.")

    normalized = []
    for issue in issues:
        key = issue.get("key")
        fields = issue.get("fields", {})
        if not key:
            continue
        normalized.append({"key": key, "fields": fields})

    normalized.sort(key=lambda i: i.get("key", ""))

    source = doc.get("source") if isinstance(doc, dict) else None
    return {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "source": {
            "type": "jira_json",
            "input_path": infile.as_posix(),
            "upstream_source": source,
        },
        "issues": normalized,
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", required=True, help="inputs/jira_export.csv OR inputs/jira_snapshot.json")
    ap.add_argument("--field-map", default="tools/jira_field_map.json")
    ap.add_argument("--out", default="inputs/jira_snapshot.json")
    args = ap.parse_args()

    infile = Path(args.infile)
    if not infile.exists():
        raise SystemExit(f"Input file not found: {infile}")

    field_map = load_field_map(args.field_map)

    try:
        suffix = infile.suffix.lower()
        if suffix == ".csv":
            normalized = normalize_csv(infile, field_map)
        elif suffix == ".json":
            normalized = normalize_json(infile)
        else:
            raise ValueError("Unsupported input type. Use a .csv Jira export or .json Jira snapshot.")
    except ValueError as exc:
        raise SystemExit(f"Ingestion failed: {exc}") from exc

    dump_json(args.out, normalized)
    print(f"Wrote normalized Jira snapshot with {len(normalized['issues'])} issues to {args.out}")


if __name__ == "__main__":
    main()
