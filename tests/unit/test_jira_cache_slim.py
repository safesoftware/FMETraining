"""
Regression tests for the slim-cache + slim-changelog contract.

The Jira cache and changelog are persisted to disk WITHOUT the 'description'
field, which contains customer PII. These tests lock in that invariant so
future changes can't quietly reintroduce description persistence.
"""

from __future__ import annotations

import json
from pathlib import Path


from pipeline import changelog as changelog_module


def _full_issue(key: str = "FMEFORM-1") -> dict:
    return {
        "issue_key": key,
        "issue_id": "10001",
        "summary": "Add a thing",
        "issue_type": "Story",
        "status": "Done",
        "project_key": "FMEFORM",
        "description": (
            "Customer reported via support@example.com that "
            "https://internal.example/case/123 is broken."
        ),
        "affects_versions": ["2025.0"],
        "fix_versions": ["2026.1"],
        "changelog_version": "2026.1",
        "affects_versions_parsed": [2025.0],
    }


def test_fetch_raw_issues_writes_slim_cache(tmp_path: Path, monkeypatch) -> None:
    """fetch_raw_issues must NOT write 'description' to the on-disk cache."""
    from pipeline import jira_api, config

    cache_path = tmp_path / "jira_api_cache.json"
    monkeypatch.setattr(config, "JIRA_CACHE_PATH", cache_path)

    raw_issues = [_full_issue("FMEFORM-1"), _full_issue("FMEFORM-2")]

    # Bypass network: stub _validate_credentials and _fetch_all_pages
    monkeypatch.setattr(jira_api, "_validate_credentials", lambda: None)
    monkeypatch.setattr(jira_api, "_fetch_all_pages", lambda: raw_issues)

    returned = jira_api.fetch_raw_issues(refresh=True)

    # In-memory return value retains descriptions for same-process consumers
    assert all("description" in i for i in returned)
    assert returned[0]["description"].startswith("Customer reported")

    # On-disk cache must be slim
    assert cache_path.exists()
    with open(cache_path, encoding="utf-8") as f:
        payload = json.load(f)
    for issue in payload["issues"]:
        assert "description" not in issue, (
            f"Slim-cache contract violated: {issue.get('issue_key')!r} "
            f"still contains a 'description' field on disk"
        )


def test_build_changelog_writes_slim_changelog(tmp_path: Path, monkeypatch) -> None:
    """build_changelog must NOT write 'description' to the on-disk changelog."""
    issues = [_full_issue("FMEFORM-1"), _full_issue("FMEFORM-2")]

    monkeypatch.setattr(
        changelog_module,
        "_filter_issues",
        lambda raw, fmin, tv: [{**i, "affects_versions_parsed": [2025.0]} for i in raw],
    )
    monkeypatch.setattr(
        changelog_module,
        "fetch_raw_issues" if hasattr(changelog_module, "fetch_raw_issues") else "_filter_issues",
        lambda *a, **kw: issues,
        raising=False,
    )

    # Patch the runtime import inside build_changelog
    import pipeline.jira_api as jira_api
    monkeypatch.setattr(jira_api, "fetch_raw_issues", lambda refresh=False: issues)

    manifest = {
        "job": {"to_version": "2026.1"},
        "lessons": [{"version": "2024.2"}],
    }
    changelog = changelog_module.build_changelog(
        run_id="test-run",
        manifest=manifest,
        output_dir=tmp_path,
        dry_run=False,
        jira_source="api",
        refresh_jira=False,
    )

    # In-memory dict keeps descriptions
    assert any("description" in i for i in changelog.get("issues", []))

    # On-disk changelog must be slim
    out_files = list(tmp_path.glob("changelog-*.json"))
    assert out_files, "expected changelog file to be written"
    with open(out_files[0], encoding="utf-8") as f:
        on_disk = json.load(f)
    for issue in on_disk.get("issues", []):
        assert "description" not in issue, (
            f"Slim-changelog contract violated: {issue.get('issue_key')!r} "
            f"still contains a 'description' field on disk"
        )


def test_fetch_descriptions_empty_input_no_api_call(monkeypatch) -> None:
    """fetch_descriptions([]) must short-circuit without hitting the API."""
    from pipeline import jira_api

    called = {"validate": False}

    def _fail_validate() -> None:
        called["validate"] = True
        raise AssertionError("fetch_descriptions([]) must not validate creds")

    monkeypatch.setattr(jira_api, "_validate_credentials", _fail_validate)

    result = jira_api.fetch_descriptions([])

    assert result == {}
    assert called["validate"] is False
