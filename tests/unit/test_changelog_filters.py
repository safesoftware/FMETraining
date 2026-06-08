"""
Unit tests for changelog.py filtering logic.

Tests the _filter_issues() function directly with synthetic issue dicts,
so no file I/O or API calls are required.
"""

from __future__ import annotations


from pipeline.changelog import _filter_issues


def _make_issue(
    issue_key: str = "FMEFORM-1000",
    project_key: str = "FMEFORM",
    issue_type: str = "Story",
    summary: str = "Some feature improvement",
    fix_versions: list[str] | None = None,
    affects_versions: list[str] | None = None,
    changelog_version: str = "",
) -> dict:
    """Build a minimal raw issue dict matching the _filter_issues input format."""
    return {
        "issue_key": issue_key,
        "project_key": project_key,
        "issue_type": issue_type,
        "summary": summary,
        "fix_versions": fix_versions or [],
        "affects_versions": affects_versions or [],
        "changelog_version": changelog_version,
    }


# Version range used across tests: source 2024.2, target 2026.1
FROM_MIN = 2024.2
TO_VERSION = 2026.1


class TestBugTypeFiltered:
    def test_bug_issue_excluded(self):
        issues = [_make_issue(issue_type="Bug", fix_versions=["2025.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []

    def test_bug_case_insensitive(self):
        issues = [_make_issue(issue_type="bug", fix_versions=["2025.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []

    def test_non_bug_story_included(self):
        issues = [_make_issue(issue_type="Story", fix_versions=["2025.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1


class TestExcludedPrefixes:
    def test_quick_translator_prefix_excluded(self):
        issues = [_make_issue(
            summary="Quick Translator: Fix crash on startup",
            fix_versions=["2025.0"],
        )]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []

    def test_data_inspector_prefix_excluded(self):
        issues = [_make_issue(
            summary="Data Inspector: Improve rendering",
            fix_versions=["2025.0"],
        )]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []

    def test_transformer_designer_prefix_excluded(self):
        issues = [_make_issue(
            summary="Transformer Designer: New export option",
            fix_versions=["2025.0"],
        )]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []

    def test_non_excluded_prefix_included(self):
        issues = [_make_issue(
            summary="Workbench: Reorganized menus for clarity",
            fix_versions=["2025.0"],
        )]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1


class TestProjectKeyFilter:
    def test_unknown_project_key_excluded(self):
        issues = [_make_issue(project_key="UNKNOWN", fix_versions=["2025.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []

    def test_fmeform_included(self):
        issues = [_make_issue(project_key="FMEFORM", fix_versions=["2025.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1

    def test_fmeflow_included(self):
        issues = [_make_issue(project_key="FMEFLOW", fix_versions=["2025.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1

    def test_foundation_included(self):
        issues = [_make_issue(project_key="FOUNDATION", fix_versions=["2025.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1

    def test_fmeengine_included(self):
        issues = [_make_issue(project_key="FMEENGINE", fix_versions=["2025.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1


class TestVersionRangeFiltering:
    def test_fix_version_in_range_included(self):
        issues = [_make_issue(fix_versions=["2025.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1

    def test_fix_version_exactly_at_target_included(self):
        # Upper bound is inclusive
        issues = [_make_issue(fix_versions=["2026.1"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1

    def test_fix_version_exactly_at_from_min_excluded(self):
        # Lower bound is exclusive
        issues = [_make_issue(fix_versions=["2024.2"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []

    def test_fix_version_before_range_excluded(self):
        issues = [_make_issue(fix_versions=["2023.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []

    def test_fix_version_after_target_excluded(self):
        issues = [_make_issue(fix_versions=["2027.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []

    def test_affects_version_in_range_included(self):
        issues = [_make_issue(affects_versions=["2025.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1

    def test_multiple_fix_versions_one_in_range(self):
        # If any fix_version is in range, the issue is included
        issues = [_make_issue(fix_versions=["2023.0", "2025.0", "2027.0"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1

    def test_changelog_version_in_range_included(self):
        # changelog_version is the API-sourced version field
        issues = [_make_issue(changelog_version="2025.1")]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1

    def test_changelog_version_out_of_range_excluded(self):
        issues = [_make_issue(changelog_version="2023.0")]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []

    def test_no_version_fields_excluded(self):
        issues = [_make_issue(fix_versions=[], affects_versions=[], changelog_version="")]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert result == []


class TestDeduplication:
    def test_duplicate_issue_key_deduped(self):
        issues = [
            _make_issue(issue_key="FMEFORM-1000", fix_versions=["2025.0"]),
            _make_issue(issue_key="FMEFORM-1000", fix_versions=["2025.1"]),
        ]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 1

    def test_different_keys_both_included(self):
        issues = [
            _make_issue(issue_key="FMEFORM-1000", fix_versions=["2025.0"]),
            _make_issue(issue_key="FMEFORM-1001", fix_versions=["2025.0"]),
        ]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert len(result) == 2


class TestOutputStructure:
    def test_affects_versions_parsed_added(self):
        issues = [_make_issue(affects_versions=["2025.0", "2025.1"])]
        result = _filter_issues(issues, FROM_MIN, TO_VERSION)
        assert "affects_versions_parsed" in result[0]
        assert 2025.0 in result[0]["affects_versions_parsed"]
        assert 2025.1 in result[0]["affects_versions_parsed"]
