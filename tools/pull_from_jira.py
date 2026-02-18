#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_FIELDS = [
    "summary",
    "issuetype",
    "status",
    "project",
    "components",
    "labels",
    "fixVersions",
    "parent",
    "subtasks",
    "description",
    "updated",
]


def build_jql(base_jql: str | None, since: str | None, release: str | None) -> str:
    parts = []
    if base_jql:
        parts.append(f"({base_jql})")
    if since:
        dt.date.fromisoformat(since)
        parts.append(f"updated >= '{since}'")
    if release:
        release_q = release.replace("'", "\\'")
        parts.append(f"fixVersion = '{release_q}'")
    return " AND ".join(parts) if parts else "ORDER BY updated DESC"


def jira_auth_headers() -> tuple[str, dict[str, str]]:
    base_url = os.getenv("JIRA_BASE_URL", "").rstrip("/")
    user = os.getenv("JIRA_USER_EMAIL") or os.getenv("JIRA_USERNAME")
    token = os.getenv("JIRA_API_TOKEN") or os.getenv("JIRA_PAT")
    version = os.getenv("JIRA_API_VERSION", "auto")

    if not (base_url and user and token):
        print(
            "Missing Jira credentials. Set JIRA_BASE_URL, JIRA_USER_EMAIL (or JIRA_USERNAME), and JIRA_API_TOKEN (or JIRA_PAT).",
            file=sys.stderr,
        )
        sys.exit(2)

    import base64

    auth = base64.b64encode(f"{user}:{token}".encode("utf-8")).decode("ascii")
    if version == "auto":
        api_versions = ["3", "2"]
    else:
        api_versions = [str(version)]

    headers = {
        "Authorization": f"Basic {auth}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    return base_url, {"api_versions": json.dumps(api_versions), **headers}


def request_with_retry(url: str, payload: dict[str, Any], headers: dict[str, str], retries: int = 4) -> dict[str, Any]:
    body = json.dumps(payload).encode("utf-8")
    for i in range(retries + 1):
        try:
            req = urllib.request.Request(url, data=body, headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and i < retries:
                delay = (2**i) + 0.2
                time.sleep(delay)
                continue
            detail = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Jira request failed ({e.code}): {detail}") from e
        except urllib.error.URLError as e:
            if i < retries:
                time.sleep((2**i) + 0.2)
                continue
            raise RuntimeError(f"Jira URL error: {e}") from e
    raise RuntimeError("Jira request exhausted retries")


def fetch_issues(base_url: str, versions: list[str], headers: dict[str, str], jql: str, max_issues: int | None, fields: list[str]) -> dict[str, Any]:
    for version in versions:
        start_at = 0
        page_size = 50
        all_issues: list[dict[str, Any]] = []
        try:
            while True:
                if max_issues:
                    remaining = max_issues - len(all_issues)
                    if remaining <= 0:
                        break
                    page_size = min(page_size, remaining)

                payload = {
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": page_size,
                    "fields": fields,
                }
                url = f"{base_url}/rest/api/{version}/search"
                data = request_with_retry(url, payload, headers)
                issues = data.get("issues", [])
                total = int(data.get("total", 0))
                all_issues.extend(issues)
                start_at += len(issues)
                if not issues or start_at >= total:
                    break
            return {"api_version": version, "issues": all_issues}
        except RuntimeError as e:
            if version == versions[-1]:
                raise
            print(f"API /rest/api/{version} failed ({e}); trying next configured version", file=sys.stderr)
    raise RuntimeError("Unable to fetch from Jira")


def expand_epics(issues: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_key = {i.get("key"): i for i in issues}
    expanded = list(issues)
    for issue in issues:
        fields = issue.get("fields", {})
        parent = fields.get("parent") or {}
        parent_key = parent.get("key")
        if parent_key and parent_key in by_key:
            continue
        subtasks = fields.get("subtasks") or []
        for st in subtasks:
            st_key = st.get("key")
            if st_key and st_key in by_key:
                continue
    return expanded


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jql")
    ap.add_argument("--since")
    ap.add_argument("--release")
    ap.add_argument("--max-issues", type=int)
    ap.add_argument("--out", default="inputs/jira_snapshot.json")
    ap.add_argument("--include-comments", action="store_true")
    ap.add_argument("--include-attachments", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base_url, headers = jira_auth_headers()
    versions = json.loads(headers.pop("api_versions"))

    fields = DEFAULT_FIELDS.copy()
    if args.include_comments:
        fields.append("comment")
    if args.include_attachments:
        fields.append("attachment")

    resolved_jql = build_jql(args.jql, args.since, args.release)
    if args.dry_run:
        print(json.dumps({"resolved_jql": resolved_jql, "max_issues": args.max_issues, "fields": fields}, indent=2))
        return

    fetched = fetch_issues(base_url, versions, headers, resolved_jql, args.max_issues, fields)
    issues = expand_epics(fetched["issues"])
    snapshot = {
        "generated_at": dt.datetime.utcnow().isoformat() + "Z",
        "source": {
            "jira_base_url": base_url,
            "jql": resolved_jql,
            "api_version": fetched["api_version"],
            "fields": fields,
            "max_issues": args.max_issues,
        },
        "issues": issues,
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snapshot, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {len(issues)} issues to {out}")


if __name__ == "__main__":
    main()
