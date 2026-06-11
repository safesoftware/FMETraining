"""Report HTML generation regressions (KNOW-2342).

Two bugs made a completed run's "Lesson Edits" tab show no lessons even though
step 6 produced a plan:

1. The edit-plans lesson list was loaded inside ``Promise.all([..., leLoadDrafts()])``,
   so a stalled best-effort drafts fetch left the list unpopulated.
2. ``APP_BASE_URL`` defaulted to ``http://localhost:8000``; baked into a report
   served same-origin, the drafts fetch hit the *viewer's* machine and hung.

These tests pin the fixes: same-origin (relative) ``APP_BASE`` and a drafts load
that is decoupled from the lesson list.
"""
from __future__ import annotations

import json

import pipeline.config as cfg
from pipeline.report import build_report


def _seed(output_dir, run_id, *, with_edit_plans=False):
    """Write the minimal artifacts build_report needs and return the recs path."""
    recs = {
        "model": "test-model",
        "total_pairs": 0,
        "completed_pairs": 0,
        "generated_at": "",
        "assessments": [],
    }
    recs_path = output_dir / f"update-recommendations-{run_id}.json"
    recs_path.write_text(json.dumps(recs), encoding="utf-8")

    (output_dir / "runs.json").write_text(
        json.dumps({"runs": [{"run_id": run_id, "job": {"to_version": "2026.1"}}]}),
        encoding="utf-8",
    )

    edit_plans_path = None
    if with_edit_plans:
        edit_plans = {
            "run_id": run_id,
            "total_lessons": 1,
            "completed_lessons": 1,
            "lessons": [
                {
                    "lesson_id": "lp/c/l",
                    "lesson_name": "Lesson L",
                    "course_canonical": "C",
                    "learning_path": "lp",
                    "changes": [],
                }
            ],
        }
        edit_plans_path = output_dir / f"edit-plans-{run_id}.json"
        edit_plans_path.write_text(json.dumps(edit_plans), encoding="utf-8")
    return recs_path, edit_plans_path


def test_app_base_url_default_is_relative():
    """Unset APP_BASE_URL must resolve to '' (same-origin), never localhost."""
    # The test environment does not set APP_BASE_URL (see Makefile / compose),
    # so the module-level value reflects the os.getenv default.
    assert cfg.APP_BASE_URL == ""


def test_report_uses_relative_app_base(tmp_path, monkeypatch):
    """The generated report wires APP_BASE relative — no hardcoded localhost."""
    monkeypatch.setattr(cfg, "APP_BASE_URL", "")
    run_id = "20260101T000000-aaaa"
    recs_path, _ = _seed(tmp_path, run_id)

    out = build_report(run_id, tmp_path, recs_path=recs_path)
    html = out.read_text(encoding="utf-8")

    assert 'const APP_BASE = "";' in html
    assert "http://localhost:8000" not in html


def test_report_decouples_edit_plans_from_drafts(tmp_path, monkeypatch):
    """The lesson list load must not be gated on the best-effort drafts fetch.

    ``leLoadDrafts()`` must be a standalone call, not an element of the
    ``Promise.all`` that assigns ``leEditPlans``.
    """
    monkeypatch.setattr(cfg, "APP_BASE_URL", "")
    run_id = "20260101T000000-bbbb"
    recs_path, edit_plans_path = _seed(tmp_path, run_id, with_edit_plans=True)

    out = build_report(
        run_id, tmp_path, recs_path=recs_path, edit_plans_path=edit_plans_path
    )
    html = out.read_text(encoding="utf-8")

    # Decoupled: edit-plans is fetched on its own (multi-line chain), the old
    # Promise.all element form (one line, trailing comma) is gone, and the
    # drafts load is a standalone best-effort call.
    assert "fetch(EDIT_PLANS_FILE)\n    .then(r => r.json())" in html
    assert "fetch(EDIT_PLANS_FILE).then(r => r.json())," not in html
    assert "leLoadDrafts();" in html
