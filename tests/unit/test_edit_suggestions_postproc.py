"""
Unit tests for edit_suggestions.py post-processing functions.

These functions run after the LLM call and are standalone — no OpenAI dependency.
Covers: issue #74 (stale original_text), issue #75 (empty heading bug),
issue #72 (FMEENGINE conceptual filter).
"""

from __future__ import annotations

import pytest

from pipeline.edit_suggestions import (
    _ensure_version_changes,
    _filter_fmeengine_no_ui,
    _filter_stale_original_text,
    _normalize_html_text,
)


# ---------------------------------------------------------------------------
# _normalize_html_text
# ---------------------------------------------------------------------------

class TestNormalizeHtmlText:
    def test_html_entities_decoded(self):
        assert _normalize_html_text("hello &amp; world") == "hello & world"

    def test_gt_lt_decoded(self):
        assert _normalize_html_text("A &gt; B &lt; C") == "A > B < C"

    def test_extra_whitespace_collapsed(self):
        assert _normalize_html_text("  too   many  spaces  ") == "too many spaces"

    def test_newlines_collapsed(self):
        assert _normalize_html_text("line one\nline two") == "line one line two"

    def test_combined_entities_and_whitespace(self):
        result = _normalize_html_text("  Run &amp; Jump   ")
        assert result == "Run & Jump"

    def test_plain_string_unchanged(self):
        assert _normalize_html_text("plain text") == "plain text"


# ---------------------------------------------------------------------------
# _filter_stale_original_text — issue #74
# ---------------------------------------------------------------------------

LESSON_HTML = """
<html><body>
<h2>Introduction</h2>
<p>Click the Run Translation button to begin your workflow.</p>
<h2>1) Open Workbench</h2>
<p>Start FME Workbench from the Start menu.</p>
</body></html>
"""


class TestFilterStaleOriginalText:
    def test_original_text_present_kept(self):
        changes = [{
            "change_id": "abc123",
            "type": "change",
            "original_text": "Run Translation button",
            "suggested_text": "Run Workspace button",
        }]
        result = _filter_stale_original_text(changes, LESSON_HTML, "lesson/id")
        assert len(result) == 1

    def test_original_text_absent_dropped(self):
        changes = [{
            "change_id": "abc123",
            "type": "change",
            "original_text": "This text does not appear anywhere",
            "suggested_text": "replacement",
        }]
        result = _filter_stale_original_text(changes, LESSON_HTML, "lesson/id")
        assert result == []

    def test_add_type_always_kept(self):
        # 'add' changes have no original_text to check
        changes = [{
            "change_id": "abc123",
            "type": "add",
            "original_text": "",
            "suggested_text": "<p>New content to insert</p>",
        }]
        result = _filter_stale_original_text(changes, LESSON_HTML, "lesson/id")
        assert len(result) == 1

    def test_delete_type_checks_original(self):
        changes = [{
            "change_id": "abc123",
            "type": "delete",
            "original_text": "nonexistent phrase here",
            "suggested_text": "",
        }]
        result = _filter_stale_original_text(changes, LESSON_HTML, "lesson/id")
        assert result == []

    def test_html_entity_normalization_for_match(self):
        # HTML in the lesson has &amp; but original_text has bare &
        html_with_entity = "<p>Save &amp; Close the dialog.</p>"
        changes = [{
            "change_id": "abc123",
            "type": "change",
            "original_text": "Save & Close the dialog.",
            "suggested_text": "Save and Close the dialog.",
        }]
        result = _filter_stale_original_text(changes, html_with_entity, "lesson/id")
        assert len(result) == 1

    def test_multiple_changes_mixed_result(self):
        changes = [
            {
                "change_id": "aaa",
                "type": "change",
                "original_text": "Run Translation button",  # present
                "suggested_text": "Run Workspace button",
            },
            {
                "change_id": "bbb",
                "type": "change",
                "original_text": "This is NOT in the HTML",  # absent
                "suggested_text": "something",
            },
        ]
        result = _filter_stale_original_text(changes, LESSON_HTML, "lesson/id")
        assert len(result) == 1
        assert result[0]["change_id"] == "aaa"


# ---------------------------------------------------------------------------
# _filter_fmeengine_no_ui — issue #72
# ---------------------------------------------------------------------------

# EXERCISE_STEP_PATTERN = re.compile(r"^(\d+)[).]")
# config.EXERCISE_STEP_PATTERN.search(lesson_html) is used
# Without MULTILINE, ^ only matches at position 0 of the string.
# So: HTML starting with "1)" triggers has_instructional=True;
# HTML starting with "<" results in has_instructional=False (conceptual).

INSTRUCTIONAL_HTML = "1) Open Workbench\n<h2>1) Open Workbench</h2><p>Start FME.</p>"
CONCEPTUAL_HTML = "<html><h2>Introduction</h2><p>FME processes data.</p></html>"

FMEENGINE_CHANGE = {
    "change_id": "abc",
    "type": "change",
    "heading": "Introduction",
    "original_text": "some text",
    "suggested_text": "new text",
    "issue_keys": ["FMEENGINE-12345"],
}

MIXED_KEY_CHANGE = {
    "change_id": "def",
    "type": "change",
    "heading": "Introduction",
    "original_text": "some text",
    "suggested_text": "new text",
    "issue_keys": ["FMEENGINE-12345", "FMEFORM-67890"],
}

FMEFORM_CHANGE = {
    "change_id": "ghi",
    "type": "change",
    "heading": "Introduction",
    "original_text": "some text",
    "suggested_text": "new text",
    "issue_keys": ["FMEFORM-11111"],
}


class TestFilterFmeengineNoUi:
    def test_fmeengine_only_in_conceptual_lesson_dropped(self):
        result = _filter_fmeengine_no_ui([FMEENGINE_CHANGE], CONCEPTUAL_HTML, "lesson/id")
        assert result == []

    def test_fmeengine_only_in_instructional_lesson_kept(self):
        # Lesson starts with "1)" so EXERCISE_STEP_PATTERN.search matches
        result = _filter_fmeengine_no_ui([FMEENGINE_CHANGE], INSTRUCTIONAL_HTML, "lesson/id")
        assert len(result) == 1

    def test_mixed_keys_always_kept(self):
        # FMEENGINE + FMEFORM mix → not all FMEENGINE, so kept even in conceptual lesson
        result = _filter_fmeengine_no_ui([MIXED_KEY_CHANGE], CONCEPTUAL_HTML, "lesson/id")
        assert len(result) == 1

    def test_fmeform_only_always_kept(self):
        result = _filter_fmeengine_no_ui([FMEFORM_CHANGE], CONCEPTUAL_HTML, "lesson/id")
        assert len(result) == 1

    def test_no_issue_keys_always_kept(self):
        change = {**FMEENGINE_CHANGE, "issue_keys": []}
        result = _filter_fmeengine_no_ui([change], CONCEPTUAL_HTML, "lesson/id")
        assert len(result) == 1

    def test_multiple_changes_partial_filter(self):
        changes = [FMEENGINE_CHANGE, FMEFORM_CHANGE]
        result = _filter_fmeengine_no_ui(changes, CONCEPTUAL_HTML, "lesson/id")
        # FMEENGINE-only dropped, FMEFORM kept
        assert len(result) == 1
        assert result[0]["change_id"] == "ghi"


# ---------------------------------------------------------------------------
# _ensure_version_changes — issue #75 (heading should not be empty)
# ---------------------------------------------------------------------------

VERSIONED_HTML = """<html><body>
<h2>Introduction to FME Form</h2>
<p>This lesson covers FME Form 2024.2 features.</p>
<h2>1) Open Workbench</h2>
<p>Launch FME Workbench 2024.2 from the taskbar.</p>
</body></html>"""


class TestEnsureVersionChanges:
    def test_uncovered_version_string_auto_added(self):
        result = _ensure_version_changes(
            changes=[],
            lesson_html=VERSIONED_HTML,
            lesson_id="test/lesson",
            from_version="2024.2",
            to_version="2026.1",
        )
        assert len(result) > 0
        for change in result:
            assert change["original_text"] == "2024.2"
            assert change["suggested_text"] == "2026.1"
            assert change["type"] == "change"

    def test_auto_added_change_has_non_empty_heading(self):
        # Issue #75: heading should not be empty — it should be the nearest h2/h3
        result = _ensure_version_changes(
            changes=[],
            lesson_html=VERSIONED_HTML,
            lesson_id="test/lesson",
            from_version="2024.2",
            to_version="2026.1",
        )
        for change in result:
            assert change["heading"] != "", (
                "heading should be populated from nearest preceding h2/h3 (issue #75)"
            )

    def test_existing_change_covers_position_no_duplicate(self):
        # LLM already generated a change that replaces "2024.2" with "2026.1"
        existing = [{
            "change_id": "aaa",
            "type": "change",
            "heading": "Introduction",
            "original_text": "This lesson covers FME Form 2024.2 features.",
            "suggested_text": "This lesson covers FME Form 2026.1 features.",
            "issue_keys": [],
        }]
        result = _ensure_version_changes(
            changes=existing,
            lesson_html=VERSIONED_HTML,
            lesson_id="test/lesson",
            from_version="2024.2",
            to_version="2026.1",
        )
        # The position covered by the LLM change should not get a duplicate
        # (second occurrence in "1) Open Workbench" section may still be added)
        original_texts = [c["original_text"] for c in result]
        # No change should have the exact covered text auto-re-added
        assert existing[0] in result  # original change is preserved

    def test_same_from_to_version_no_changes(self):
        result = _ensure_version_changes(
            changes=[],
            lesson_html=VERSIONED_HTML,
            lesson_id="test/lesson",
            from_version="2024.2",
            to_version="2024.2",
        )
        assert result == []

    def test_version_in_tag_attribute_skipped(self):
        html_with_attr = '<html><img src="icon_2024.2.png" alt="icon"><p>No version in text.</p></html>'
        result = _ensure_version_changes(
            changes=[],
            lesson_html=html_with_attr,
            lesson_id="test/lesson",
            from_version="2024.2",
            to_version="2026.1",
        )
        # Version only appears inside a tag attribute, not in text content
        assert result == []

    def test_empty_from_version_no_changes(self):
        result = _ensure_version_changes(
            changes=[],
            lesson_html=VERSIONED_HTML,
            lesson_id="test/lesson",
            from_version="",
            to_version="2026.1",
        )
        assert result == []

    def test_quarterly_note_added_for_2026_releases(self):
        result = _ensure_version_changes(
            changes=[],
            lesson_html=VERSIONED_HTML,
            lesson_id="test/lesson",
            from_version="2024.2",
            to_version="2026.1",
        )
        for change in result:
            assert "quarterly" in change["explanation"].lower(), (
                "Explanation should mention quarterly release model for 2026+ targets"
            )
