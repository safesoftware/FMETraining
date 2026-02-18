#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path
from typing import Any

from common import load_json


def get_release(fields: dict[str, Any]) -> str:
    versions = fields.get("fixVersions") or []
    if versions:
        return versions[0].get("name") or "Unreleased"
    return "Unreleased"


def guess_user_visible_change(summary: str) -> str:
    s = summary.lower()
    if "rename" in s or "label" in s:
        return "[inferred] UI label text changed."
    if "workflow" in s or "step" in s:
        return "[inferred] User workflow/steps changed."
    if "permission" in s or "role" in s:
        return "[inferred] User permissions/visibility changed."
    return "[inferred] User-facing behavior changed; confirm details in Jira issue body."


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="infile", default="inputs/jira_snapshot.json")
    ap.add_argument("--out", default="inputs/changelog_generated.md")
    args = ap.parse_args()

    snapshot = load_json(args.infile)
    issues = snapshot.get("issues", [])

    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for issue in sorted(issues, key=lambda i: i.get("key", "")):
        grouped[get_release(issue.get("fields", {}))].append(issue)

    lines = ["# Generated Docs Changelog", "", "_Deterministic output from Jira snapshot; inferred text is marked._", ""]
    for release in sorted(grouped):
        lines.append(f"## Release: {release}")
        lines.append("")
        for issue in grouped[release]:
            fields = issue.get("fields", {})
            key = issue.get("key")
            summary = fields.get("summary", "")
            issue_type = (fields.get("issuetype") or {}).get("name", "Unknown")
            guess = guess_user_visible_change(summary)
            lines.append(f"- **{key}** ({issue_type}): {summary}")
            lines.append(f"  - User-visible change guess: {guess}")
        lines.append("")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote changelog to {out}")


if __name__ == "__main__":
    main()
