"""
Unit tests for lesson-content-root resolution (KNOW-2353).

The pipeline must read lesson HTML/images from ``LESSON_CONTENT_ROOT`` (where
the content corpus is bind-mounted in the container, e.g. ``/content``) rather
than from ``REPO_ROOT`` (``/app``). When ``LESSON_CONTENT_ROOT`` is unset the
two are identical, preserving CLI / on-box behaviour.

See ``docs/PROJECT-STATE.md`` and the KNOW-2353 ticket for the diagnosis: step
5/6 logged "lesson HTML not found ... skipping" because ``edit_suggestions``
resolved ``config.REPO_ROOT / lesson_dir / index.html`` (= ``/app/...``), which
does not exist when content lives at ``/content/...``.
"""

from __future__ import annotations

import importlib
from pathlib import Path


# ---------------------------------------------------------------------------
# config.LESSON_CONTENT_ROOT — env-driven, defaults to REPO_ROOT
# ---------------------------------------------------------------------------

class TestConfigLessonContentRoot:
    def test_defaults_to_repo_root_when_unset(self, monkeypatch):
        """Unset env → LESSON_CONTENT_ROOT == REPO_ROOT (CLI/box behaviour)."""
        monkeypatch.delenv("LESSON_CONTENT_ROOT", raising=False)
        import pipeline.config as config

        config = importlib.reload(config)
        try:
            assert config.LESSON_CONTENT_ROOT == config.REPO_ROOT
        finally:
            importlib.reload(config)

    def test_honors_env_when_set(self, monkeypatch, tmp_path):
        """Set env → LESSON_CONTENT_ROOT points at the bind-mounted corpus."""
        monkeypatch.setenv("LESSON_CONTENT_ROOT", str(tmp_path))
        import pipeline.config as config

        config = importlib.reload(config)
        try:
            assert config.LESSON_CONTENT_ROOT == Path(str(tmp_path))
            assert config.LESSON_CONTENT_ROOT != config.REPO_ROOT
        finally:
            monkeypatch.delenv("LESSON_CONTENT_ROOT", raising=False)
            importlib.reload(config)


# ---------------------------------------------------------------------------
# edit_suggestions resolves lesson HTML under LESSON_CONTENT_ROOT
# ---------------------------------------------------------------------------

class TestEditSuggestionsLessonHtmlResolver:
    def test_resolves_under_lesson_content_root(self, monkeypatch, tmp_version_tree):
        """The lesson-HTML resolver finds index.html under LESSON_CONTENT_ROOT,
        even when REPO_ROOT points elsewhere (the container case: /content vs
        /app)."""
        from pipeline import config, edit_suggestions

        tree = tmp_version_tree
        content_root = tree["repo_root"]  # the tmp content corpus
        lesson_dir = f"{tree['version']}/{tree['lp']}/{tree['course_folder']}/{tree['lessons'][0]}"

        # Content lives under content_root; REPO_ROOT is somewhere else.
        monkeypatch.setattr(config, "LESSON_CONTENT_ROOT", content_root)
        monkeypatch.setattr(config, "REPO_ROOT", Path("/nonexistent-repo-root"))

        resolved = edit_suggestions._resolve_lesson_html_path(lesson_dir)

        assert resolved == content_root / lesson_dir / "index.html"
        assert resolved.exists()

    def test_returns_none_for_blank_lesson_dir(self, monkeypatch, tmp_version_tree):
        from pipeline import config, edit_suggestions

        monkeypatch.setattr(config, "LESSON_CONTENT_ROOT", tmp_version_tree["repo_root"])
        assert edit_suggestions._resolve_lesson_html_path("") is None

    def test_build_prompt_does_not_skip_lesson_under_content_root(
        self, monkeypatch, tmp_version_tree
    ):
        """Regression for KNOW-2353: _build_prompt must NOT skip the lesson when
        content lives under LESSON_CONTENT_ROOT but REPO_ROOT is /app. Before the
        fix it returned None ("lesson HTML not found"), yielding an empty
        edit-plan (completed_lessons=0)."""
        from pipeline import config, edit_suggestions

        tree = tmp_version_tree
        content_root = tree["repo_root"]
        lesson_dir = f"{tree['version']}/{tree['lp']}/{tree['course_folder']}/{tree['lessons'][0]}"

        monkeypatch.setattr(config, "LESSON_CONTENT_ROOT", content_root)
        monkeypatch.setattr(config, "REPO_ROOT", Path("/nonexistent-repo-root"))

        group = [{
            "issue_key": "KNOW-1",
            "issue_summary": "Update screenshot",
            "update_likelihood": "high",
            "justification": "UI changed",
            "lesson_dir": lesson_dir,
            "lesson_name": tree["lessons"][0],
            "course_canonical": tree["course_canonical"],
            "learning_path": tree["lp"],
            "version": tree["version"],
        }]
        template = "Lesson: {{LESSON_NAME}}\nHTML:\n{{LESSON_HTML}}\nIssues:\n{{ISSUES_LIST}}"

        prompt = edit_suggestions._build_prompt(
            lesson_id="lid-1", group=group, template=template, to_version="2025.0"
        )

        assert prompt is not None
        assert tree["lessons"][0] in prompt
