"""
Mocked LLM tests for pipeline/edit_suggestions.py — Step 6.

Replaces AsyncOpenAI with unittest.mock so tests run without API keys.
Validates: post-processing pipeline, silent failure detection, incremental logic,
safe_note.png filter, suggested_text HTML stripping, already-present add filter.
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest

from pipeline.edit_suggestions import _call_openai


def _make_client(response_content: str | None, raise_exception: Exception | None = None):
    """
    Build a mock AsyncOpenAI client whose chat.completions.create() returns
    a response with the given JSON content, or raises an exception.
    """
    client = MagicMock()

    if raise_exception is not None:
        client.chat.completions.create = AsyncMock(side_effect=raise_exception)
    else:
        mock_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=response_content))],
            usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50),
        )
        client.chat.completions.create = AsyncMock(return_value=mock_response)

    return client


def _make_group(lesson_html: str = "<p>Hello world.</p>", version: str = "2024.2") -> list[dict]:
    """Build a minimal assessment group dict for _call_openai."""
    return [{
        "issue_key": "FMEFORM-1000",
        "issue_summary": "Test issue",
        "update_likelihood": "high",
        "justification": "Test justification",
        "lesson_id": "2024.2/fme-form-basic/Connect To Data/My Lesson",
        "lesson_dir": ".",
        "lesson_name": "My Lesson",
        "course_canonical": "Connect To Data",
        "learning_path": "fme-form-basic",
        "version": version,
        "product": ["fme_form"],
        "_lesson_html": lesson_html,
        "_to_version": "2026.1",
    }]


def _make_edit_plan_response(changes=None, screenshot_updates=None, rename_pairs=None) -> str:
    """Build a JSON string matching the expected LLM response schema."""
    return json.dumps({
        "rename_pairs": rename_pairs or [],
        "changes": changes or [],
        "screenshot_updates": screenshot_updates or [],
    })


# ---------------------------------------------------------------------------
# Basic success path
# ---------------------------------------------------------------------------

class TestCallOpenaiSuccess:
    async def test_returns_lesson_dict_on_success(self):
        lesson_html = "<p>Hello world.</p>"
        response = _make_edit_plan_response(changes=[{
            "change_id": "aaaaaaaa",
            "type": "change",
            "heading": "Introduction",
            "original_text": "Hello world.",
            "suggested_text": "Greetings world.",
            "explanation": "Updated phrasing",
            "issue_keys": ["FMEFORM-1000"],
        }])
        client = _make_client(response)
        group = _make_group(lesson_html)

        result = await _call_openai(client, "test/lesson", group, "prompt text")

        assert result is not None
        assert result["lesson_id"] == "test/lesson"
        assert isinstance(result["changes"], list)

    async def test_change_ids_reassigned_as_stable_hashes(self):
        lesson_html = "<p>Hello world.</p>"
        response = _make_edit_plan_response(changes=[
            {
                "change_id": "llm-generated-id",
                "type": "change",
                "heading": "Intro",
                "original_text": "Hello world.",
                "suggested_text": "Greetings.",
                "explanation": "test",
                "issue_keys": [],
            }
        ])
        client = _make_client(response)
        group = _make_group(lesson_html)

        result = await _call_openai(client, "test/lesson", group, "prompt")

        # Change IDs are reassigned to md5-based stable hashes (8 hex chars)
        assert result is not None
        for change in result["changes"]:
            assert len(change["change_id"]) == 8


# ---------------------------------------------------------------------------
# Silent failure guard (AGENTS.md failure pattern)
# ---------------------------------------------------------------------------

class TestSilentFailureGuard:
    async def test_returns_none_after_all_retries_fail(self):
        client = _make_client(None, raise_exception=RuntimeError("API error"))

        result = await _call_openai(client, "test/lesson", _make_group(), "prompt")

        assert result is None, (
            "Should return None when all retries fail — caller must detect this "
            "and NOT mark completed_lessons as successful (AGENTS.md silent failure pattern)"
        )

    async def test_call_count_matches_retry_limit(self):
        client = _make_client(None, raise_exception=RuntimeError("API error"))

        await _call_openai(client, "test/lesson", _make_group(), "prompt")

        # max_retries = 3
        assert client.chat.completions.create.call_count == 3


# ---------------------------------------------------------------------------
# safe_note.png filter (issue #57)
# ---------------------------------------------------------------------------

class TestSafeNotePngFilter:
    async def test_safe_note_filtered_from_screenshot_updates(self):
        response = _make_edit_plan_response(
            screenshot_updates=[
                {"src": "images/safe_note.png", "explanation": "Update icon", "issue_keys": []},
                {"src": "images/real_screenshot.png", "explanation": "Update UI", "issue_keys": []},
            ]
        )
        client = _make_client(response)

        result = await _call_openai(client, "test/lesson", _make_group(), "prompt")

        assert result is not None
        srcs = [su["src"] for su in result["screenshot_updates"]]
        assert "images/safe_note.png" not in srcs
        assert "images/real_screenshot.png" in srcs

    async def test_safe_note_in_subdirectory_filtered(self):
        response = _make_edit_plan_response(
            screenshot_updates=[
                {"src": "images/sub/safe_note.png", "explanation": "x", "issue_keys": []},
            ]
        )
        client = _make_client(response)

        result = await _call_openai(client, "test/lesson", _make_group(), "prompt")

        assert result is not None
        assert result["screenshot_updates"] == []


# ---------------------------------------------------------------------------
# HTML tag stripping from suggested_text for 'change' type (issue #65)
# ---------------------------------------------------------------------------

class TestHtmlTagStripping:
    async def test_html_tags_stripped_from_change_type(self):
        lesson_html = "<p>Click Run Translation to begin.</p>"
        response = _make_edit_plan_response(changes=[{
            "change_id": "aaa",
            "type": "change",
            "heading": "Intro",
            "original_text": "Click Run Translation to begin.",
            "suggested_text": "Click <strong>Run Workspace</strong> to begin.",
            "explanation": "UI renamed",
            "issue_keys": [],
        }])
        client = _make_client(response)
        group = _make_group(lesson_html)

        result = await _call_openai(client, "test/lesson", group, "prompt")

        assert result is not None
        for change in result["changes"]:
            if change.get("type") == "change":
                assert "<strong>" not in change["suggested_text"]
                assert "<" not in change["suggested_text"]

    async def test_html_tags_preserved_in_add_type(self):
        lesson_html = "<p>Some existing content.</p>"
        response = _make_edit_plan_response(changes=[{
            "change_id": "bbb",
            "type": "add",
            "heading": "Intro",
            "original_text": "",
            "suggested_text": "<p class='note'><strong>Note:</strong> New content.</p>",
            "explanation": "Adding callout",
            "issue_keys": [],
        }])
        client = _make_client(response)
        group = _make_group(lesson_html)

        result = await _call_openai(client, "test/lesson", group, "prompt")

        assert result is not None
        for change in result["changes"]:
            if change.get("type") == "add":
                # HTML is preserved for 'add' type
                assert "<p" in change["suggested_text"]


# ---------------------------------------------------------------------------
# Already-present 'add' filter (issue #33)
# ---------------------------------------------------------------------------

class TestAlreadyPresentAddFilter:
    async def test_add_already_in_html_filtered(self):
        # The suggested_text is already in the lesson HTML
        lesson_html = "<p>Note: This feature requires FME Flow.</p><p>Other content.</p>"
        response = _make_edit_plan_response(changes=[{
            "change_id": "ccc",
            "type": "add",
            "heading": "Intro",
            "original_text": "",
            "suggested_text": "Note: This feature requires FME Flow.",
            "explanation": "Add note",
            "issue_keys": [],
        }])
        client = _make_client(response)
        group = _make_group(lesson_html)

        result = await _call_openai(client, "test/lesson", group, "prompt")

        assert result is not None
        assert result["changes"] == []

    async def test_add_not_in_html_kept(self):
        lesson_html = "<p>Other content only.</p>"
        response = _make_edit_plan_response(changes=[{
            "change_id": "ddd",
            "type": "add",
            "heading": "Intro",
            "original_text": "",
            "suggested_text": "Note: This feature requires FME Flow.",
            "explanation": "Add note",
            "issue_keys": [],
        }])
        client = _make_client(response)
        group = _make_group(lesson_html)

        result = await _call_openai(client, "test/lesson", group, "prompt")

        assert result is not None
        assert len(result["changes"]) == 1
