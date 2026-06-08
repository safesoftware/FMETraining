"""
Jira API client for the FME Training Update Pipeline.

Fetches issues from a Jira filter via the REST API v3 and caches results
to .cache/jira_api_cache.json (gitignored) to avoid repeated API calls.

The cache is metadata-only: issue descriptions are NEVER written to disk
because they contain customer-identifying text (emails, support case URLs,
free-text reproduction narratives). Descriptions are returned in the
in-memory list from fetch_raw_issues, and re-fetched on demand via
fetch_descriptions(keys) for steps that need them in a later process.

Usage in changelog.py:
    from pipeline.jira_api import fetch_raw_issues
    raw_issues = fetch_raw_issues(refresh=False)

Usage when only descriptions are needed (e.g. resuming step 6):
    from pipeline.jira_api import fetch_descriptions
    descriptions = fetch_descriptions(["KNOW-1", "FMEFORM-2"])
"""

from __future__ import annotations

import base64
import json
import time
from datetime import datetime, timezone
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from pipeline import config


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def fetch_raw_issues(refresh: bool = False) -> list[dict]:
    """
    Return a list of raw issue dicts from the Jira filter.

    Uses the cache at inputs/jira_api_cache.json if it exists and
    refresh=False. Pass refresh=True to force a re-fetch from the API.

    The returned dicts have the same keys as the CSV-path output:
        issue_key, issue_id, summary, issue_type, status, project_key,
        description, affects_versions, fix_versions, affects_versions_parsed
    (affects_versions_parsed is omitted here; changelog.py adds it.)

    Raises EnvironmentError if required Jira credentials are missing.
    """
    cache_path = config.JIRA_CACHE_PATH

    if not refresh and cache_path.exists():
        print(f"  [Jira API] Using cache ({cache_path.name}). Pass --refresh-jira to re-fetch.")
        with open(cache_path, encoding="utf-8") as f:
            data = json.load(f)
        return data.get("issues", [])

    _validate_credentials()

    print(f"  [Jira API] Fetching issues from filter {config.JIRA_FILTER_ID}...")
    raw_issues = _fetch_all_pages()
    print(f"  [Jira API] Fetched {len(raw_issues)} issues from Jira API.")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    # Strip 'description' before persisting: it contains customer PII.
    # The full in-memory list (with descriptions) is still returned for the current call.
    slim_issues = [
        {k: v for k, v in i.items() if k != "description"}
        for i in raw_issues
    ]
    cache_payload = {
        "fetched_at": datetime.now(tz=timezone.utc).isoformat(),
        "filter_id": config.JIRA_FILTER_ID,
        "total": len(raw_issues),
        "issues": slim_issues,
    }
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(cache_payload, f, indent=2, ensure_ascii=False)
    print(f"  [Jira API] Cached -> {cache_path}")

    return raw_issues


def fetch_descriptions(issue_keys: list[str]) -> dict[str, str]:
    """
    Fetch only the description field for the given issue keys.

    Returns a dict mapping issue_key -> plain-text description (ADF→text).
    The result is held in memory by the caller and is never persisted to disk
    by this function. Issues whose description is empty or missing are not
    included in the returned dict.

    Pages through Jira in batches of 100 keys via JQL `key in (...)`.

    Raises EnvironmentError if Jira credentials are missing.
    """
    if not issue_keys:
        return {}

    _validate_credentials()

    base = config.JIRA_BASE_URL
    session = _make_session()
    session.headers.update(_auth_header())

    descriptions: dict[str, str] = {}
    batch_size = 100
    total_batches = (len(issue_keys) + batch_size - 1) // batch_size

    for batch_idx in range(total_batches):
        batch = issue_keys[batch_idx * batch_size : (batch_idx + 1) * batch_size]
        # JQL: key in (KNOW-1, KNOW-2, ...) — paginate within the batch in case of many results
        jql = "key in ({})".format(",".join(batch))
        next_page_token: str | None = None

        while True:
            url = f"{base}/rest/api/3/search/jql"
            params: dict = {
                "jql": jql,
                "fields": "description",
                "maxResults": batch_size,
            }
            if next_page_token:
                params["nextPageToken"] = next_page_token

            resp = session.get(url, params=params, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            for raw in data.get("issues", []):
                key = raw.get("key", "").strip()
                if not key:
                    continue
                desc_raw = (raw.get("fields") or {}).get("description")
                desc = _adf_to_text(desc_raw).strip() if desc_raw else ""
                if desc:
                    descriptions[key] = desc

            if data.get("isLast", True):
                break
            next_page_token = data.get("nextPageToken")
            if not next_page_token:
                break

    return descriptions


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _validate_credentials() -> None:
    missing = []
    if not config.JIRA_BASE_URL:
        missing.append("JIRA_BASE_URL")
    if not config.JIRA_USER:
        missing.append("JIRA_USER")
    if not config.JIRA_API_TOKEN:
        missing.append("JIRA_API_KEY")
    if not config.JIRA_FILTER_ID:
        missing.append("JIRA_FILTER_ID")
    if missing:
        raise EnvironmentError(
            f"Jira API credentials missing from .env: {', '.join(missing)}. "
            "Set JIRA_BASE_URL, JIRA_USER, JIRA_API_KEY, and JIRA_FILTER_ID."
        )


def _auth_header() -> dict[str, str]:
    token = base64.b64encode(
        f"{config.JIRA_USER}:{config.JIRA_API_TOKEN}".encode()
    ).decode()
    return {
        "Authorization": f"Basic {token}",
        "Accept": "application/json",
    }


def _make_session() -> requests.Session:
    """Return a requests Session with automatic retry on transient errors."""
    session = requests.Session()
    retry = Retry(
        total=5,
        backoff_factor=2,          # waits 2, 4, 8, 16, 32 s between retries
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,     # we call raise_for_status() ourselves
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


def _fetch_all_pages() -> list[dict]:
    """Paginate through all results for the Jira filter using cursor-based pagination.

    The /rest/api/3/search/jql endpoint does not return a 'total' count.
    Pagination uses nextPageToken (cursor) and stops when isLast=True.
    Transient connection errors are retried up to 5 times with exponential backoff.
    """
    base = config.JIRA_BASE_URL
    headers = _auth_header()
    # customfield_11765 = "Changelog Version" — the authoritative version for each
    # changelog entry (not fixVersions, which is empty for most issues in this filter).
    fields = "summary,issuetype,status,project,description,versions,fixVersions,id,customfield_11765"
    jql = f"filter={config.JIRA_FILTER_ID}"
    max_results = 100
    all_issues: list[dict] = []
    next_page_token: str | None = None
    session = _make_session()
    session.headers.update(headers)

    max_attempts = 5
    while True:
        url = f"{base}/rest/api/3/search/jql"
        params: dict = {
            "jql": jql,
            "fields": fields,
            "maxResults": max_results,
        }
        if next_page_token:
            params["nextPageToken"] = next_page_token

        # Retry loop for connection-level errors (e.g. ConnectionResetError)
        for attempt in range(1, max_attempts + 1):
            try:
                resp = session.get(url, params=params, timeout=30)
                resp.raise_for_status()
                break
            except (requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as exc:
                if attempt == max_attempts:
                    raise
                wait = 2 ** attempt
                print(f"\n    [retry {attempt}/{max_attempts - 1}] {exc} — retrying in {wait}s...",
                      end="\r")
                time.sleep(wait)

        data = resp.json()

        issues = data.get("issues", [])
        for raw in issues:
            normalized = _normalize_issue(raw)
            if normalized:
                all_issues.append(normalized)

        print(f"    fetched {len(all_issues)} issues...", end="\r")

        if data.get("isLast", True) or not issues:
            break

        next_page_token = data.get("nextPageToken")
        if not next_page_token:
            break

    print()  # newline after \r progress
    return all_issues


def _normalize_issue(raw: dict) -> dict | None:
    """Convert a Jira API issue object to the same dict format as the CSV path."""
    key = raw.get("key", "").strip()
    if not key:
        return None

    fields: dict[str, Any] = raw.get("fields", {})

    issue_id = str(raw.get("id", "")).strip()
    summary = (fields.get("summary") or "").strip()
    issue_type = (fields.get("issuetype") or {}).get("name", "").strip()
    status = (fields.get("status") or {}).get("name", "").strip()
    project_key = (fields.get("project") or {}).get("key", "").strip()

    # Description: Atlassian Document Format → plain text
    desc_raw = fields.get("description")
    description = _adf_to_text(desc_raw).strip() if desc_raw else None

    # Affected versions
    affects_versions = [
        v["name"] for v in (fields.get("versions") or []) if v.get("name")
    ]

    # Fix versions
    fix_versions = [
        v["name"] for v in (fields.get("fixVersions") or []) if v.get("name")
    ]

    # Changelog Version (customfield_11765) — the authoritative version for this
    # changelog entry, set by the changelog workflow. More reliable than fixVersions
    # for version-range filtering because fixVersions is often empty in this filter.
    cv_raw = fields.get("customfield_11765")
    changelog_version = cv_raw.get("name", "") if isinstance(cv_raw, dict) else ""

    return {
        "issue_key": key,
        "issue_id": issue_id,
        "summary": summary,
        "issue_type": issue_type,
        "status": status,
        "project_key": project_key,
        "description": description,
        "affects_versions": affects_versions,
        "fix_versions": fix_versions,
        "changelog_version": changelog_version,
    }


def _adf_to_text(node: Any, _depth: int = 0) -> str:
    """
    Recursively extract plain text from an Atlassian Document Format (ADF) node.

    ADF is a JSON structure used by Jira Cloud REST API v3 for rich text fields.
    We only need the plain text content for our prompts.
    """
    if node is None:
        return ""
    if isinstance(node, str):
        return node

    if not isinstance(node, dict):
        return ""

    node_type = node.get("type", "")

    # Leaf text node
    if node_type == "text":
        return node.get("text", "")

    # Inline code
    if node_type == "code":
        return node.get("text", "")

    # Hard break → newline
    if node_type == "hardBreak":
        return "\n"

    # Recurse into content array
    parts: list[str] = []
    for child in node.get("content") or []:
        parts.append(_adf_to_text(child, _depth + 1))

    text = "".join(parts)

    # Block-level nodes get a trailing newline
    if node_type in ("paragraph", "heading", "bulletList", "orderedList",
                     "listItem", "blockquote", "codeBlock", "rule"):
        text = text.rstrip() + "\n"

    return text
