"""
Mocked LLM tests for pipeline/assessment.py — Step 3 cost-meter wiring.

Replaces AsyncOpenAI with unittest.mock so tests run without API keys.
Validates:
- cost_meter.check_before_call is invoked before each API call
- cost_meter.record_usage is invoked after a successful API call
- CostCeilingExceeded raised by check_before_call propagates out of _call_openai
- Default (cost_meter=None) preserves legacy behaviour (no cost calls)
- PII: a known description string is never written to the on-disk recs artifact
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest

from pipeline.assessment import _call_openai, run_assessment
from app.services.run_cost_meter import CostCeilingExceeded, RunCostMeter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_client(
    response_content: str | None = None,
    *,
    raise_exception: Exception | None = None,
    prompt_tokens: int = 150,
    completion_tokens: int = 80,
):
    """Build a mock AsyncOpenAI client for assessment tests."""
    client = MagicMock()
    if raise_exception is not None:
        client.chat.completions.create = AsyncMock(side_effect=raise_exception)
    else:
        if response_content is None:
            response_content = json.dumps({
                "update_likelihood": "low",
                "justification": "Minor UI changes only.",
                "impacts_exercise": False,
                "affected_headings": [],
                "screenshots_need_retaking": False,
                "affected_screenshots": [],
            })
        mock_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=response_content))],
            usage=SimpleNamespace(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            ),
        )
        client.chat.completions.create = AsyncMock(return_value=mock_response)
    return client


def _make_lesson(lesson_id: str = "2024.2/fme-form-basic/Course/Lesson") -> dict:
    return {
        "lesson_id": lesson_id,
        "path": f"{lesson_id}/index.html",
        "lesson_name": "Lesson",
        "course_canonical": "Course",
        "learning_path": "fme-form-basic",
        "version": "2024.2",
        "product": ["fme_form"],
        "headings": [],
        "exercise_steps": [],
        "ui_strings": [],
        "images": [],
    }


def _make_issue(issue_key: str = "FMEFORM-1001") -> dict:
    return {
        "issue_key": issue_key,
        "summary": "Update UI label",
        "issue_type": "Story",
        "status": "Done",
        "affects_versions": ["2024.2"],
        "fix_versions": ["2025.0"],
        "project_key": "FMEFORM",
    }


# ---------------------------------------------------------------------------
# _call_openai cost-meter wiring
# ---------------------------------------------------------------------------

class TestCallOpenaiCostMeter:
    """Verify the cost meter hook points inside _call_openai."""

    async def test_check_before_call_invoked_before_api(self):
        """check_before_call must fire before client.chat.completions.create."""
        call_order: list[str] = []

        meter = MagicMock(spec=RunCostMeter)

        def _check(**kwargs):
            call_order.append("check")

        meter.check_before_call.side_effect = _check

        client = MagicMock()

        async def _create(**kwargs):
            call_order.append("api")
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps({
                    "update_likelihood": "low",
                    "justification": "x",
                    "impacts_exercise": False,
                    "affected_headings": [],
                    "screenshots_need_retaking": False,
                    "affected_screenshots": [],
                })))],
                usage=SimpleNamespace(prompt_tokens=100, completion_tokens=50),
            )

        client.chat.completions.create = _create

        await _call_openai(client, _make_lesson(), _make_issue(), "prompt", cost_meter=meter)

        assert call_order == ["check", "api"], (
            "check_before_call must precede the OpenAI API call"
        )

    async def test_record_usage_called_after_success(self):
        """record_usage must be called with the actual token counts from the response."""
        meter = MagicMock(spec=RunCostMeter)
        client = _make_client(prompt_tokens=120, completion_tokens=60)

        await _call_openai(client, _make_lesson(), _make_issue(), "prompt", cost_meter=meter)

        meter.record_usage.assert_called_once()
        _, kwargs = meter.record_usage.call_args
        assert kwargs["prompt_tokens"] == 120
        assert kwargs["completion_tokens"] == 60

    async def test_cost_ceiling_exceeded_propagates(self):
        """CostCeilingExceeded from check_before_call must not be caught by the retry loop."""
        meter = MagicMock(spec=RunCostMeter)
        meter.check_before_call.side_effect = CostCeilingExceeded("over budget")
        client = _make_client()  # Would succeed if reached

        with pytest.raises(CostCeilingExceeded):
            await _call_openai(client, _make_lesson(), _make_issue(), "prompt", cost_meter=meter)

        # The API must never have been called
        client.chat.completions.create.assert_not_called()

    async def test_no_cost_meter_skips_all_meter_calls(self):
        """cost_meter=None (default) must never call any meter method."""
        client = _make_client()

        result = await _call_openai(client, _make_lesson(), _make_issue(), "prompt")
        # No AttributeError → no meter accessed; result should be a valid dict
        assert result is not None
        assert "lesson_id" in result

    async def test_record_usage_not_called_when_api_fails(self):
        """If the API raises (and we exhaust retries), record_usage must not be called."""
        meter = MagicMock(spec=RunCostMeter)
        client = _make_client(raise_exception=RuntimeError("flake"))

        result = await _call_openai(
            client, _make_lesson(), _make_issue(), "prompt", cost_meter=meter
        )

        assert result is None
        meter.record_usage.assert_not_called()


# ---------------------------------------------------------------------------
# run_assessment with mocked OpenAI — end-to-end (no real API calls)
# ---------------------------------------------------------------------------

def _patched_run_assessment_context():
    """Return a context manager that patches both AsyncOpenAI and the API key lookup.

    ``_assess_all`` instantiates ``AsyncOpenAI(api_key=config.get_openai_api_key())``
    at the start of its body. To avoid the EnvironmentError when OPENAI_API_KEY is
    not set, we patch ``get_openai_api_key`` as well as ``AsyncOpenAI`` itself.
    Both patches must be active for tests to run without real credentials.
    """
    from contextlib import contextmanager

    @contextmanager
    def _ctx(mock_client):
        with patch("pipeline.assessment.AsyncOpenAI") as mock_cls, \
             patch("pipeline.assessment.config.get_openai_api_key", return_value="sk-test"):
            mock_cls.return_value = mock_client
            yield mock_cls

    return _ctx


class TestRunAssessmentMockedOpenAI:
    """End-to-end tests for run_assessment with a mocked OpenAI client."""

    _ctx = staticmethod(_patched_run_assessment_context())

    def _make_manifest(self) -> dict:
        return {
            "run_id": "test-run",
            "job": {"to_version": "2026.1"},
            "lessons": [_make_lesson("2024.2/fme-form-basic/Course/Lesson A")],
        }

    def _make_changelog(self, *, description: str = "Some description text") -> dict:
        issue = _make_issue("FMEFORM-1001")
        issue["description"] = description
        return {"issues": [issue]}

    def _good_response_json(self) -> str:
        return json.dumps({
            "update_likelihood": "medium",
            "justification": "Label renamed.",
            "impacts_exercise": True,
            "affected_headings": ["Introduction"],
            "screenshots_need_retaking": False,
            "affected_screenshots": [],
        })

    def test_recs_artifact_written(self, tmp_path):
        """run_assessment should write update-recommendations-<run_id>.json."""
        manifest = self._make_manifest()
        changelog = self._make_changelog()
        run_id = "recs-write-test"

        with self._ctx(_make_client(self._good_response_json())):
            recs = run_assessment(
                run_id=run_id,
                manifest=manifest,
                changelog=changelog,
                output_dir=tmp_path,
                descriptions={"FMEFORM-1001": "Some description text"},
            )

        recs_file = tmp_path / f"update-recommendations-{run_id}.json"
        assert recs_file.exists(), f"recs file not found at {recs_file}"
        data = json.loads(recs_file.read_text(encoding="utf-8"))
        assert data["run_id"] == run_id
        assert len(data["assessments"]) >= 1

    def test_cost_meter_record_usage_called(self, tmp_path):
        """When cost_meter is passed, record_usage should be called for each pair."""
        manifest = self._make_manifest()
        changelog = self._make_changelog()
        meter = RunCostMeter(ceiling_usd=50.0)
        run_id = "recs-cost-test"

        with self._ctx(_make_client(self._good_response_json(), prompt_tokens=200, completion_tokens=80)):
            run_assessment(
                run_id=run_id,
                manifest=manifest,
                changelog=changelog,
                output_dir=tmp_path,
                descriptions={"FMEFORM-1001": "desc"},
                cost_meter=meter,
            )

        snap = meter.snapshot()
        assert snap["by_model"], "cost meter should have recorded at least one model's usage"
        model_key = list(snap["by_model"].keys())[0]
        assert snap["by_model"][model_key]["prompt_tokens"] > 0

    def test_scratch_recommendations_populated_via_pipeline_runner(
        self, tmp_path, monkeypatch
    ):
        """Sanity check: the dict returned from run_assessment is structurally valid.

        The pipeline_runner integration test (in test_pipeline_runner_steps.py)
        does the full DB-backed check; this just validates the return shape.
        """
        manifest = self._make_manifest()
        changelog = self._make_changelog()
        run_id = "recs-shape-test"

        with self._ctx(_make_client(self._good_response_json())):
            recs = run_assessment(
                run_id=run_id,
                manifest=manifest,
                changelog=changelog,
                output_dir=tmp_path,
                descriptions={"FMEFORM-1001": "desc"},
            )

        assert recs["run_id"] == run_id
        assert "assessments" in recs
        assert isinstance(recs["assessments"], list)

    def test_pii_description_not_in_recs_artifact(self, tmp_path):
        """The on-disk recs JSON must NOT contain any raw description string.

        This is the core PII-on-disk assertion for step 3.
        """
        PII_SENTINEL = "TOP_SECRET_JIRA_DESCRIPTION_DO_NOT_STORE"
        manifest = self._make_manifest()
        changelog = self._make_changelog(description=PII_SENTINEL)
        run_id = "recs-pii-test"

        with self._ctx(_make_client(self._good_response_json())):
            run_assessment(
                run_id=run_id,
                manifest=manifest,
                changelog=changelog,
                output_dir=tmp_path,
                descriptions={
                    "FMEFORM-1001": PII_SENTINEL,
                },
            )

        recs_file = tmp_path / f"update-recommendations-{run_id}.json"
        assert recs_file.exists(), "recs file should have been written"
        content = recs_file.read_text(encoding="utf-8")
        assert PII_SENTINEL not in content, (
            f"PII sentinel found in on-disk recs artifact! "
            f"Jira descriptions must never be written to disk.\n"
            f"File: {recs_file}"
        )

    def test_dry_run_returns_empty_assessments_without_api(self, tmp_path):
        """dry_run=True must skip all API calls and return an empty assessments list."""
        manifest = self._make_manifest()
        changelog = self._make_changelog()
        run_id = "recs-dry-run"

        with patch("pipeline.assessment.AsyncOpenAI") as mock_openai_cls:
            client = _make_client(self._good_response_json())
            mock_openai_cls.return_value = client

            recs = run_assessment(
                run_id=run_id,
                manifest=manifest,
                changelog=changelog,
                output_dir=tmp_path,
                dry_run=True,
            )

        assert recs["completed_pairs"] == 0
        assert recs["assessments"] == []
        # In dry_run mode the client should never be instantiated
        mock_openai_cls.assert_not_called()
