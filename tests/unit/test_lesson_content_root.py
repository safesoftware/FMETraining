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
# config.CACHE_ROOT — env-driven writable scratch, defaults to REPO_ROOT/.cache
# (KNOW-2354). In the container /app is root-owned; compose sets FME_CACHE_DIR
# to a writable bind-mounted dir so nothing writes under /app at runtime.
# ---------------------------------------------------------------------------

class TestConfigCacheRoot:
    def test_defaults_to_repo_root_cache_when_unset(self, monkeypatch):
        """Unset env → CACHE_ROOT == REPO_ROOT/.cache (CLI/box behaviour)."""
        monkeypatch.delenv("FME_CACHE_DIR", raising=False)
        import pipeline.config as config

        config = importlib.reload(config)
        try:
            assert config.CACHE_ROOT == config.REPO_ROOT / ".cache"
            # JIRA_CACHE_PATH must hang off CACHE_ROOT, not REPO_ROOT directly.
            assert config.JIRA_CACHE_PATH == config.CACHE_ROOT / "jira_api_cache.json"
            assert config.JIRA_CACHE_PATH == config.REPO_ROOT / ".cache" / "jira_api_cache.json"
        finally:
            importlib.reload(config)

    def test_honors_env_when_set(self, monkeypatch, tmp_path):
        """Set FME_CACHE_DIR → CACHE_ROOT (and JIRA_CACHE_PATH) relocate off
        REPO_ROOT to the writable dir (the container case: a writable mount
        rather than the root-owned /app)."""
        monkeypatch.setenv("FME_CACHE_DIR", str(tmp_path))
        import pipeline.config as config

        config = importlib.reload(config)
        try:
            assert config.CACHE_ROOT == Path(str(tmp_path))
            assert config.CACHE_ROOT != config.REPO_ROOT / ".cache"
            assert config.JIRA_CACHE_PATH == Path(str(tmp_path)) / "jira_api_cache.json"
        finally:
            monkeypatch.delenv("FME_CACHE_DIR", raising=False)
            importlib.reload(config)


# ---------------------------------------------------------------------------
# edit_suggestions resolves lesson HTML through the content source
# (KNOW-2353 root-resolution lives in pipeline/content_source.py now;
# KNOW-2360 migrated Step 6's reads onto it.)
# ---------------------------------------------------------------------------

class TestEditSuggestionsLessonHtmlResolver:
    def test_build_prompt_reads_html_via_content_source(
        self, monkeypatch, tmp_version_tree
    ):
        """Regression for KNOW-2353 / KNOW-2360: _build_prompt must NOT skip the
        lesson when content lives under LESSON_CONTENT_ROOT but REPO_ROOT is /app.
        Before the fix it returned None ("lesson HTML not found"), yielding an
        empty edit-plan (completed_lessons=0). The reads now go through a
        LocalFolderSource rooted at the content corpus."""
        from pipeline import edit_suggestions
        from pipeline.content_source import LocalFolderSource

        tree = tmp_version_tree
        content_root = tree["repo_root"]  # the tmp content corpus
        lesson_dir = f"{tree['version']}/{tree['lp']}/{tree['course_folder']}/{tree['lessons'][0]}"

        # Pin the resolver at the content corpus (the container case: /content),
        # independent of REPO_ROOT.
        source = LocalFolderSource(content_root)
        monkeypatch.setattr(edit_suggestions, "get_content_source", lambda: source)

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
        # The actual lesson HTML (from index.html on disk) made it into the prompt.
        assert source.get_lesson_html(lesson_dir).strip()[:20] in prompt

    def test_build_prompt_skips_silently_when_html_absent(
        self, monkeypatch, tmp_version_tree
    ):
        """A missing lesson HTML returns None (skip), preserving the historical
        silent-skip behaviour KNOW-2353 flagged — now routed through
        lesson_html_exists on the resolver."""
        from pipeline import edit_suggestions
        from pipeline.content_source import LocalFolderSource

        tree = tmp_version_tree
        source = LocalFolderSource(tree["repo_root"])
        monkeypatch.setattr(edit_suggestions, "get_content_source", lambda: source)

        group = [{
            "issue_key": "KNOW-1",
            "issue_summary": "x",
            "update_likelihood": "high",
            "justification": "x",
            "lesson_dir": f"{tree['version']}/{tree['lp']}/{tree['course_folder']}/Does Not Exist",
            "lesson_name": "Does Not Exist",
            "course_canonical": tree["course_canonical"],
            "learning_path": tree["lp"],
            "version": tree["version"],
        }]
        template = "{{LESSON_HTML}}"

        prompt = edit_suggestions._build_prompt(
            lesson_id="missing", group=group, template=template, to_version="2025.0"
        )
        assert prompt is None

    def test_build_prompt_returns_none_for_blank_lesson_dir(self, tmp_version_tree):
        from pipeline import edit_suggestions

        group = [{"issue_key": "KNOW-1", "lesson_dir": ""}]
        prompt = edit_suggestions._build_prompt(
            lesson_id="blank", group=group, template="{{LESSON_HTML}}", to_version="2025.0"
        )
        assert prompt is None
