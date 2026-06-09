"""
Step 5: Generate the HTML Report.

Reads artifacts/update-recommendations-{RUN_ID}.json and writes
artifacts/report-{RUN_ID}.html — a self-contained paginated report
that loads the JSON via JavaScript fetch().

To view: run `python -m http.server 8080` from the project root,
then open http://localhost:8080/artifacts/report-{RUN_ID}.html in your browser.
(Most browsers block fetch() for file:// URLs.)
"""

from __future__ import annotations

import json
from pathlib import Path

from pipeline import config
from pipeline.utils import get_run_job, recommendations_path, report_path


def build_report(
    run_id: str,
    output_dir: Path,
    recs_path: Path | None = None,
    edit_plans_path: Path | None = None,
) -> Path:
    """
    Generate the HTML report for a completed run.

    Args:
        run_id:          The run ID to generate a report for.
        output_dir:      Artifacts directory (for writing the HTML).
        recs_path:       Override path to the recommendations JSON.
        edit_plans_path: Optional path to the edit plans JSON (enables Lesson Edits tab).

    Returns:
        Path to the written HTML report.
    """
    print("\n[Step 5] Generating HTML report...")

    if recs_path is None:
        recs_path = recommendations_path(run_id, output_dir)

    if not recs_path.exists():
        raise FileNotFoundError(
            f"Recommendations file not found: {recs_path}. Run steps 1-4 first."
        )

    with open(recs_path, encoding="utf-8") as f:
        recs = json.load(f)

    model = recs.get("model", "unknown")
    total = recs.get("total_pairs", 0)
    completed = recs.get("completed_pairs", 0)
    generated_at = recs.get("generated_at", "")

    edit_plans_filename = edit_plans_path.name if edit_plans_path and edit_plans_path.exists() else ""

    # Get to_version from runs.json for use in save functionality
    job = get_run_job(run_id, output_dir)
    to_version = job.get("to_version", "") if job else ""

    html = _build_html(
        run_id, recs_path.name, model, total, completed, generated_at,
        config.JIRA_BASE_URL, edit_plans_filename, to_version,
        config.APP_BASE_URL,
    )

    out_path = report_path(run_id, output_dir)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Report written: {out_path.name}")
    print("  To view: python serve.py  (run from project root, enables Save feature)")
    print(f"  Then open: http://localhost:8080/artifacts/{out_path.name}")
    return out_path


# ---------------------------------------------------------------------------
# HTML generation
# ---------------------------------------------------------------------------

def _build_html(
    run_id: str,
    json_filename: str,
    model: str,
    total_pairs: int,
    completed_pairs: int,
    generated_at: str,
    jira_base_url: str = "",
    edit_plans_filename: str = "",
    to_version: str = "",
    app_base_url: str = "http://localhost:8000",
) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>FME Training Update Report — {run_id}</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background: #f5f5f5; color: #333; }}
header {{ background: #1a3d6b; color: #fff; padding: 16px 24px; }}
header h1 {{ font-size: 1.3rem; margin-bottom: 4px; }}
header .meta {{ font-size: 0.8rem; opacity: 0.8; }}
.stats {{ display: flex; gap: 12px; padding: 12px 24px; background: #fff; border-bottom: 1px solid #ddd; flex-wrap: wrap; }}
.stat-chip {{ padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; }}
.stat-chip.high {{ background: #fee2e2; color: #991b1b; }}
.stat-chip.medium {{ background: #ffedd5; color: #9a3412; }}
.stat-chip.low {{ background: #fef9c3; color: #854d0e; }}
.stat-chip.none {{ background: #f3f4f6; color: #374151; }}
.stat-chip.total {{ background: #dbeafe; color: #1e40af; }}
.controls {{ display: flex; gap: 12px; padding: 12px 24px; background: #fff; border-bottom: 1px solid #ddd; flex-wrap: wrap; align-items: center; }}
.controls label {{ font-size: 0.85rem; font-weight: 500; }}
.controls select, .controls input {{ padding: 6px 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.85rem; }}
.controls input[type=text] {{ min-width: 200px; }}
.likelihood-filters {{ display: flex; gap: 8px; align-items: center; }}
.likelihood-filters label {{ display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 0.85rem; }}
.main {{ padding: 16px 24px; }}
.card {{ background: #fff; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 14px; overflow: hidden; }}
.card-header {{ padding: 12px 16px; border-bottom: 1px solid #f0f0f0; display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; }}
.card-title {{ font-size: 0.95rem; font-weight: 600; color: #111; }}
.card-meta {{ font-size: 0.78rem; color: #666; margin-top: 2px; }}
.card-badges {{ display: flex; gap: 6px; flex-wrap: wrap; align-items: center; flex-shrink: 0; }}
.badge {{ padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; white-space: nowrap; }}
.badge.high {{ background: #dc2626; color: #fff; }}
.badge.medium {{ background: #ea580c; color: #fff; }}
.badge.low {{ background: #ca8a04; color: #fff; }}
.badge.none {{ background: #6b7280; color: #fff; }}
.badge.screenshot {{ background: #7c3aed; color: #fff; }}
.badge.exercise {{ background: #0891b2; color: #fff; }}
.badge.fme-form {{ background: #0369a1; color: #fff; }}
.badge.fme-flow {{ background: #065f46; color: #fff; }}
.badge.issue-type {{ background: #e5e7eb; color: #374151; }}
.card-body {{ padding: 12px 16px; display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
.card-section h4 {{ font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; color: #888; margin-bottom: 4px; }}
.card-section p {{ font-size: 0.88rem; line-height: 1.5; }}
.card-section.full {{ grid-column: 1 / -1; }}
.justification {{ font-size: 0.88rem; line-height: 1.6; color: #222; }}
.assessment-section {{ margin-top: 6px; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }}
.assessment-section summary {{ cursor: pointer; font-size: 0.78rem; font-weight: 600; color: #555; padding: 5px 10px; background: #f9fafb; list-style: none; display: flex; align-items: center; gap: 4px; }}
.assessment-section summary::before {{ content: "▶"; font-size: 0.6rem; }}
.assessment-section[open] summary::before {{ content: "▼"; }}
.assessment-section .section-body {{ padding: 8px 10px; }}
.assessment-section ul {{ padding-left: 16px; margin: 0; }}
.assessment-section li {{ font-size: 0.82rem; color: #444; margin-bottom: 3px; }}
.assessment-section li.screenshot-item {{ list-style: none; margin-bottom: 10px; padding: 8px; background: #f5f3ff; border-radius: 4px; }}
.assessment-section li.screenshot-item .ss-img {{ display: block; margin-bottom: 6px; }}
.assessment-section li.screenshot-item .ss-img img {{ max-width: 100%; max-height: 512px; border-radius: 4px; border: 1px solid #ddd8fe; cursor: pointer; }}
.assessment-section li.screenshot-item .ss-src {{ font-family: monospace; font-size: 0.72rem; color: #5b21b6; font-weight: 600; margin-bottom: 3px; }}
.assessment-section li.screenshot-item .ss-exp {{ font-size: 0.82rem; color: #333; }}
.pagination {{ display: flex; justify-content: center; align-items: center; gap: 12px; padding: 20px; }}
.pagination button {{ padding: 8px 18px; border: 1px solid #ccc; border-radius: 4px; background: #fff; cursor: pointer; font-size: 0.85rem; }}
.pagination button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
.pagination button:not(:disabled):hover {{ background: #f0f4ff; }}
.pagination span {{ font-size: 0.85rem; color: #555; }}
.rec-id {{ font-family: monospace; font-size: 0.72rem; color: #aaa; margin-left: 8px; cursor: pointer; border-radius: 3px; padding: 1px 4px; transition: background 0.15s, color 0.15s; }}
.rec-id:hover {{ background: #e0e7ff; color: #4338ca; }}
.rec-id:hover::after {{ content: " copy"; font-size: 0.65rem; }}
.rec-id.copied {{ background: #d1fae5; color: #065f46; }}
#no-results {{ display: none; padding: 40px; text-align: center; color: #888; }}
.fetch-error {{ background: #fee2e2; color: #991b1b; padding: 20px 24px; margin: 20px 24px; border-radius: 8px; font-size: 0.9rem; line-height: 1.6; }}
/* Card status */
.status-btns {{ display: flex; gap: 4px; flex-shrink: 0; }}
.status-btn {{ padding: 3px 8px; border-radius: 4px; font-size: 0.72rem; font-weight: 600; cursor: pointer; border: 1px solid transparent; transition: all 0.12s; white-space: nowrap; }}
.status-btn.active  {{ background: #f3f4f6; color: #374151; border-color: #d1d5db; }}
.status-btn.active:hover  {{ background: #dbeafe; color: #1d4ed8; border-color: #93c5fd; }}
.status-btn.active.sel  {{ background: #dbeafe; color: #1d4ed8; border-color: #93c5fd; }}
.status-btn.done   {{ background: #f3f4f6; color: #374151; border-color: #d1d5db; }}
.status-btn.done:hover   {{ background: #dcfce7; color: #15803d; border-color: #86efac; }}
.status-btn.done.sel   {{ background: #dcfce7; color: #15803d; border-color: #86efac; }}
.status-btn.incorrect {{ background: #f3f4f6; color: #374151; border-color: #d1d5db; }}
.status-btn.incorrect:hover {{ background: #fee2e2; color: #b91c1c; border-color: #fca5a5; }}
.status-btn.incorrect.sel {{ background: #fee2e2; color: #b91c1c; border-color: #fca5a5; }}
.card[data-status="done"] {{ opacity: 0.45; }}
.card[data-status="done"] .card-title {{ text-decoration: line-through; }}
.card[data-status="incorrect"] {{ opacity: 0.45; border-left: 3px solid #ef4444; }}
/* Card highlight animation (cross-tab jump) */
@keyframes card-flash {{ 0%,100% {{ background:#fff; }} 50% {{ background:#fef08a; }} }}
.card-highlight {{ animation: card-flash 1s ease 2; }}
/* Highlight the originating edit suggestion link when jumping from a change popup */
.from-change-highlight {{ background:#fef3c7; border-radius:3px; padding:1px 4px; font-weight:600; }}
/* Status filter chips */
.status-filters {{ display: flex; gap: 8px; align-items: center; }}
.status-filters label {{ display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 0.85rem; }}
/* Tabs */
.tab-bar {{ display: flex; gap: 0; padding: 0 24px; background: #1a3d6b; }}
.tab-btn {{ padding: 8px 20px; border: none; border-radius: 6px 6px 0 0; cursor: pointer; font-size: 0.88rem; font-weight: 600; color: rgba(255,255,255,0.65); background: transparent; transition: background 0.15s, color 0.15s; }}
.tab-btn.active {{ background: #f5f5f5; color: #1a3d6b; }}
.tab-pane {{ display: none; }}
.tab-pane.active {{ display: block; }}
/* Lesson Edits tab */
.lesson-edit-controls {{ display: flex; gap: 12px; padding: 12px 24px; background: #fff; border-bottom: 1px solid #ddd; flex-wrap: wrap; align-items: center; }}
.lesson-edit-controls label {{ font-size: 0.85rem; font-weight: 500; }}
.lesson-edit-controls select {{ padding: 6px 10px; border: 1px solid #ccc; border-radius: 4px; font-size: 0.85rem; }}
.lesson-edit-body {{ padding: 16px 24px; max-width: 900px; margin: 0 auto; }}
.lesson-edit-body h2, .lesson-edit-body h3, .lesson-edit-body h4 {{ margin: 1.2em 0 0.5em; font-family: inherit; }}
.lesson-edit-body p {{ margin: 0.5em 0; line-height: 1.65; }}
.lesson-edit-body ul, .lesson-edit-body ol {{ padding-left: 1.5em; margin: 0.5em 0; }}
.lesson-edit-body img {{ max-width: 100%; height: auto; border-radius: 4px; border: 1px solid #e5e7eb; display: block; margin: 8px 0; }}
.lesson-edit-body table {{ border-collapse: collapse; width: 100%; margin: 0.5em 0; }}
.lesson-edit-body td, .lesson-edit-body th {{ border: 1px solid #ddd; padding: 6px 10px; font-size: 0.88rem; }}
.lesson-edit-body blockquote {{ border-left: 3px solid #e5e7eb; padding: 8px 12px; margin: 8px 0; background: #fafafa; }}
.lesson-edit-empty {{ padding: 60px 24px; text-align: center; color: #888; font-size: 0.95rem; }}
/* Track changes */
.tc-wrap {{ position: relative; display: inline; }}
del.tc-del {{ background: #fee2e2; color: #b91c1c; text-decoration: line-through; padding: 1px 2px; border-radius: 2px; }}
ins.tc-ins {{ background: #dcfce7; color: #15803d; text-decoration: none; padding: 1px 2px; border-radius: 2px; }}
ins.tc-add {{ display: block; background: #dcfce7; color: #15803d; padding: 4px 8px; margin: 4px 0; border-radius: 4px; border-left: 3px solid #16a34a; }}
span.tc-orig {{ background: #f3f4f6; color: #374151; padding: 1px 3px; border-radius: 2px; }}
.tc-change {{ cursor: help; border-bottom: 2px dotted #f59e0b; }}
.tc-wrap[data-state="accepted"] {{ background: #f0fdf4; border-radius: 2px; }}
.tc-wrap[data-state="rejected"] {{ background: transparent; border-radius: 2px; border-bottom-color: #9ca3af; cursor: default; }}
.tc-wrap[data-type="screenshot"] {{ display: block; }}
span.tc-orig-context {{ color: inherit; }}
/* Unified popup (tooltip + accept/reject) — shown/hidden via JS hover with delay */
.tc-popup {{ display: none; position: absolute; z-index: 300; background: #1e293b; color: #fff; font-size: 0.78rem; padding: 8px 10px; border-radius: 6px; max-width: 340px; line-height: 1.5; top: 100%; left: 0; box-shadow: 0 4px 12px rgba(0,0,0,0.25); white-space: normal; min-width: 200px; }}
.tc-popup.tc-popup-visible {{ display: block; }}
.tc-explanation {{ display: block; margin-bottom: 4px; }}
.tc-issue-links {{ display: block; font-size: 0.72rem; opacity: 0.8; margin-bottom: 6px; }}
.tc-btns {{ display: flex; gap: 4px; flex-wrap: wrap; }}
.tc-accept {{ padding: 3px 8px; border-radius: 4px; border: none; cursor: pointer; font-size: 0.75rem; font-weight: 600; background: #dcfce7; color: #15803d; }}
.tc-reject {{ padding: 3px 8px; border-radius: 4px; border: none; cursor: pointer; font-size: 0.75rem; font-weight: 600; background: #fee2e2; color: #b91c1c; }}
/* Screenshot notes */
.screenshot-note {{ background: #fef9c3; border-left: 3px solid #f59e0b; padding: 8px 12px; margin: 2px 0 12px; font-size: 0.82rem; line-height: 1.5; border-radius: 0 4px 4px 0; }}
.screenshot-note strong {{ display: block; margin-bottom: 2px; color: #92400e; }}
.screenshot-note-accepted {{ background: #f0fdf4; border-left-color: #16a34a; }}
.screenshot-note-accepted strong {{ color: #15803d; }}
.screenshot-note-rejected {{ background: #f9fafb; border-left-color: #9ca3af; opacity: 0.55; }}
/* Alt text update notes (issue 53) */
.alt-text-note {{ background: #eff6ff; border-left: 3px solid #3b82f6; padding: 8px 12px; margin: 2px 0 12px; font-size: 0.82rem; line-height: 1.5; border-radius: 0 4px 4px 0; }}
.alt-text-note strong {{ display: block; margin-bottom: 4px; color: #1d4ed8; }}
.alt-text-note .alt-row {{ display: flex; gap: 6px; align-items: baseline; margin-top: 2px; }}
.alt-text-note .alt-label {{ font-weight: 600; min-width: 4.5rem; color: #374151; }}
.alt-text-note .alt-val {{ color: #1f2937; }}
.alt-text-note-accepted {{ background: #f0fdf4; border-left-color: #16a34a; }}
.alt-text-note-accepted strong {{ color: #15803d; }}
.alt-text-note-rejected {{ background: #f9fafb; border-left-color: #9ca3af; opacity: 0.55; }}
.le-sticky-bars {{ position: sticky; top: 0; z-index: 400; background: #fff; box-shadow: 0 1px 0 rgba(0, 0, 0, 0.06); }}
.edit-toolbar {{ display: flex; gap: 8px; align-items: center; padding: 8px 24px; background: #f8fafc; border-bottom: 1px solid #e5e7eb; flex-wrap: wrap; }}
.edit-toolbar button {{ padding: 5px 12px; border: 1px solid #ccc; border-radius: 4px; background: #fff; cursor: pointer; font-size: 0.82rem; }}
.edit-toolbar button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
.edit-toolbar .save-btn {{ background: #1a3d6b; color: #fff; border-color: #1a3d6b; font-weight: 600; }}
.edit-toolbar .save-btn:hover:not(:disabled) {{ background: #1e4d8c; }}
.edit-toolbar .reset-btn {{ background: #fff; color: #b91c1c; border-color: #fca5a5; }}
.edit-toolbar .reset-btn:hover:not(:disabled) {{ background: #fef2f2; }}
.le-autosave-status {{ margin-left: auto; font-size: 0.78rem; color: #6b7280; min-width: 12em; text-align: right; }}
.le-autosave-status[data-state="saving"] {{ color: #2563eb; }}
.le-autosave-status[data-state="error"] {{ color: #b91c1c; }}

#le-lesson-body[contenteditable="true"]:focus {{ outline: 2px solid #6366f1; border-radius: 6px; }}
.fmt-toolbar {{ display: none; gap: 4px; align-items: center; padding: 6px 24px; background: #eef2ff; border-bottom: 1px solid #c7d2fe; flex-wrap: wrap; }}
.fmt-toolbar button {{ padding: 4px 10px; border: 1px solid #a5b4fc; border-radius: 4px; background: #fff; cursor: pointer; font-size: 0.82rem; min-width: 2rem; }}
.fmt-toolbar button:hover {{ background: #e0e7ff; border-color: #6366f1; }}
.fmt-toolbar .fmt-sep {{ width: 1px; height: 1.4em; background: #c7d2fe; margin: 0 4px; }}
/* Image-edit popover (KNOW-2279) */
#le-lesson-body img.le-img-selected {{ outline: 2px solid #2563eb; outline-offset: 2px; cursor: pointer; }}
.le-img-popover {{ position: absolute; z-index: 1000; background: #fff; border: 1px solid #d1d5db; border-radius: 6px; box-shadow: 0 4px 12px rgba(0,0,0,0.15); padding: 10px; min-width: 320px; display: none; font-size: 13px; }}
.le-img-popover.visible {{ display: block; }}
.le-img-popover label {{ display: block; font-weight: 600; margin-bottom: 4px; }}
.le-img-popover input[type=text] {{ width: 100%; padding: 6px 8px; box-sizing: border-box; font: inherit; }}
.le-img-popover .le-img-actions {{ display: flex; gap: 6px; margin-top: 8px; align-items: center; }}
.le-img-popover .le-img-replace-menu {{ position: relative; display: inline-block; }}
.le-img-popover .le-img-replace-menu > div {{ position: absolute; top: 100%; left: 0; background: #fff; border: 1px solid #d1d5db; border-radius: 4px; box-shadow: 0 2px 6px rgba(0,0,0,0.1); display: none; min-width: 180px; z-index: 1; }}
.le-img-popover .le-img-replace-menu.open > div {{ display: block; }}
.le-img-popover .le-img-replace-menu button {{ display: block; width: 100%; text-align: left; border: none; background: none; padding: 6px 10px; cursor: pointer; }}
.le-img-popover .le-img-replace-menu button:hover {{ background: #f3f4f6; }}
#le-img-file-input {{ display: none; }}
/* KNOW-2279: single floating toast for all editor feedback (was a static page
   banner that scrolled away at the top). Fixed near the top of the viewport so
   it travels with the editor; success/error variants below. */
.save-banner {{ display: none; position: fixed; top: 12px; left: 50%; transform: translateX(-50%); z-index: 1100; max-width: 90vw; background: #f0fdf4; border: 1px solid #86efac; color: #15803d; padding: 10px 16px; border-radius: 6px; font-size: 0.85rem; box-shadow: 0 4px 14px rgba(0,0,0,0.18); }}
.save-banner.le-msg-success {{ background: #f0fdf4; border-color: #86efac; color: #15803d; }}
.save-banner.le-msg-error {{ background: #fef2f2; border-color: #fca5a5; color: #b91c1c; }}
.change-count {{ font-size: 0.82rem; color: #555; margin-left: auto; }}
/* Floating next/prev edit nav (issue 47) */
.le-nav-float {{ position: fixed; bottom: 24px; right: 24px; z-index: 500; display: none; flex-direction: column; gap: 6px; align-items: stretch; }}
.le-nav-btn {{ padding: 7px 14px; border-radius: 6px; border: 1px solid #1a3d6b; background: #1a3d6b; color: #fff; cursor: pointer; font-size: 0.82rem; font-weight: 600; box-shadow: 0 2px 8px rgba(0,0,0,0.25); text-align: center; }}
.le-nav-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}
.le-nav-btn:not(:disabled):hover {{ background: #1e4d8c; }}
.le-nav-counter {{ text-align: center; font-size: 0.75rem; color: #555; background: rgba(255,255,255,0.92); padding: 3px 8px; border-radius: 10px; border: 1px solid #e5e7eb; box-shadow: 0 1px 4px rgba(0,0,0,0.1); }}
</style>
</head>
<body>

<header>
  <h1>FME Training Update Report</h1>
  <div class="meta">Run: {run_id} &nbsp;|&nbsp; Model: {model} &nbsp;|&nbsp; Generated: {generated_at} &nbsp;|&nbsp; Total pairs: {completed_pairs:,}</div>
</header>
<div class="tab-bar">
  <button class="tab-btn active" onclick="switchTab('recommendations', this)">Recommendations</button>
  <button class="tab-btn" onclick="switchTab('lesson-edits', this)" id="lesson-edits-tab-btn" style="{'' if edit_plans_filename else 'opacity:0.4;cursor:not-allowed'}" {'disabled' if not edit_plans_filename else ''}>Lesson Edits{' ✦' if edit_plans_filename else ' (run step 6)'}</button>
</div>

<div id="tab-recommendations" class="tab-pane active">
<div class="stats" id="stats"></div>

<div class="controls">
  <div class="likelihood-filters">
    <label><b>Likelihood:</b></label>
    <label><input type="checkbox" class="lf-check" value="high" checked> High</label>
    <label><input type="checkbox" class="lf-check" value="medium" checked> Medium</label>
    <label><input type="checkbox" class="lf-check" value="low" checked> Low</label>
    <label><input type="checkbox" class="lf-check" value="none"> None</label>
  </div>
  <div class="status-filters">
    <label><b>Status:</b></label>
    <label><input type="checkbox" class="sf-check" value="active" checked> Active</label>
    <label><input type="checkbox" class="sf-check" value="done"> Done</label>
    <label><input type="checkbox" class="sf-check" value="incorrect"> Incorrect</label>
  </div>
  <div class="status-filters">
    <label><input type="checkbox" id="exercise-filter"> Impacts Exercise only</label>
    <label><input type="checkbox" id="screenshot-filter"> Screenshots Needed only</label>
  </div>
  <div style="display:flex;gap:8px;align-items:center">
    <label>Learning Path: <select id="lp-filter"><option value="">All</option></select></label>
    <label>Course: <select id="course-filter"><option value="">All</option></select></label>
    <label>Lesson: <select id="lesson-filter"><option value="">All</option></select></label>
  </div>
  <div style="display:flex;gap:8px;align-items:center">
    <label>Sort: <select id="sort-select">
      <option value="likelihood-desc">Likelihood (High first)</option>
      <option value="likelihood-asc">Likelihood (Low first)</option>
      <option value="lesson-asc">Lesson (A-Z)</option>
      <option value="issue-asc">Issue Key (A-Z)</option>
    </select></label>
    <input type="text" id="search-box" placeholder="Search...">
  </div>
</div>

<div class="main">
  <div id="report-js-error" class="fetch-error" style="display:none">
    <b>JavaScript error — report may not display correctly.</b><br>
    <span class="rje-msg" style="font-family:monospace;font-size:0.85rem"></span><br>
    Check the terminal running <code>serve.py</code> for the full stack trace.
  </div>
  <div id="fetch-error" class="fetch-error" style="display:none">
    <b>Could not load report data.</b> Most browsers block <code>fetch()</code> for <code>file://</code> URLs.<br>
    To view this report, run: <code>python -m http.server 8080</code> from the project root,
    then open <a href="http://localhost:8080/artifacts/report-{run_id}.html">http://localhost:8080/artifacts/report-{run_id}.html</a>
  </div>
  <div class="pagination" id="pagination-top" style="display:none">
    <button id="prev-btn-top" onclick="prevPage()">← Previous</button>
    <span id="page-info-top"></span>
    <button id="next-btn-top" onclick="nextPage()">Next →</button>
  </div>
  <div id="cards-container"></div>
  <div id="no-results">No assessments match the current filters.</div>
  <div class="pagination" id="pagination-bottom" style="display:none">
    <button id="prev-btn-bottom" onclick="prevPage()">← Previous</button>
    <span id="page-info-bottom"></span>
    <button id="next-btn-bottom" onclick="nextPage()">Next →</button>
  </div>
</div>
</div><!-- end tab-recommendations -->

<div id="tab-lesson-edits" class="tab-pane">
  <div class="lesson-edit-controls">
    <label>Learning Path: <select id="le-lp-filter"><option value="">All</option></select></label>
    <label>Course: <select id="le-course-filter"><option value="">All</option></select></label>
    <label>Lesson: <select id="le-lesson-filter"><option value="">-- Select a lesson --</option></select></label>
    <span class="change-count" id="le-change-count"></span>
  </div>
  <div class="le-sticky-bars">
    <div class="edit-toolbar" id="le-toolbar" style="display:none">
      <button onclick="leUndo()" id="le-undo-btn" disabled>← Undo</button>
      <button onclick="leRedo()" id="le-redo-btn" disabled>Redo →</button>
      <button class="save-btn" onclick="leSave()" id="le-save-btn">Save to Version Folder</button>
      <button class="reset-btn" onclick="leResetLesson()" id="le-reset-btn">Reset to original</button>
      <span class="le-autosave-status" id="le-autosave-status" data-state="idle"></span>
    </div>
    <div class="fmt-toolbar" id="le-fmt-toolbar">
      <button onclick="leFormat('bold')" title="Bold (Ctrl+B)"><b>B</b></button>
      <button onclick="leFormat('italic')" title="Italic (Ctrl+I)"><i>I</i></button>
      <span class="fmt-sep"></span>
      <button onclick="leFormatBlock('h1')" title="Heading 1">H1</button>
      <button onclick="leFormatBlock('h2')" title="Heading 2">H2</button>
      <button onclick="leFormatBlock('h3')" title="Heading 3">H3</button>
      <button onclick="leFormatBlock('h4')" title="Heading 4">H4</button>
      <span class="fmt-sep"></span>
      <button onclick="leFormatList('ul')" title="Bullet list (Ctrl+Shift+8)">• List</button>
      <button onclick="leFormatList('ol')" title="Numbered list (Ctrl+Shift+7)">1. List</button>
      <span class="fmt-sep"></span>
      <button onclick="leInsertLink()" title="Insert / edit link">Link</button>
      <button onclick="leEditImage(event)" title="Edit image (alt text / replace)">Image</button>
    </div>
  </div>
  <div class="save-banner" id="le-save-banner"></div>
  <div id="le-lesson-body" class="lesson-edit-body">
    <div class="lesson-edit-empty">Select a lesson above to view suggested edits.</div>
  </div>
</div><!-- end tab-lesson-edits -->

<!-- Image-edit popover (KNOW-2279) — anchored at runtime to the selected <img> -->
<div id="le-img-popover" class="le-img-popover" role="dialog" aria-label="Edit image">
  <label for="le-img-alt" id="le-img-alt-label">Alt text</label>
  <input type="text" id="le-img-alt" placeholder="Describe the image" />
  <div class="le-img-actions">
    <span class="le-img-replace-menu" id="le-img-replace-menu">
      <button type="button" id="le-img-replace-btn" onclick="leImgToggleReplaceMenu()">Replace ▾</button>
      <div>
        <button type="button" onclick="leImgReplaceFromClipboard()">Paste from clipboard</button>
        <button type="button" onclick="leImgReplaceFromFile()">Upload from file…</button>
      </div>
    </span>
    <span style="flex:1"></span>
    <button type="button" id="le-img-save-btn" onclick="leImgSave()">Save</button>
    <button type="button" onclick="leImgClosePopover()">Cancel</button>
  </div>
</div>
<input type="file" id="le-img-file-input" accept="image/*" />

<!-- Floating next/prev edit nav — visible only when Lesson Edits tab is active and a lesson is loaded (issue 47) -->
<div class="le-nav-float" id="le-nav-float">
  <div class="le-nav-counter" id="le-nav-counter">0 / 0</div>
  <button class="le-nav-btn" id="le-prev-edit-btn" onclick="lePrevEdit()" disabled>↑ Prev Edit</button>
  <button class="le-nav-btn" id="le-next-edit-btn" onclick="leNextEdit()" disabled>↓ Next Edit</button>
</div>

<script>
// Early error handler — separate block so it survives syntax errors in the main script
window.onerror = function(message, source, lineno, colno, error) {{
  const stack = (error && error.stack) ? error.stack : '';
  const loc = source ? ' (' + source + ':' + lineno + ':' + colno + ')' : '';
  const banner = document.getElementById('report-js-error');
  if (banner) {{ banner.style.display = 'block'; banner.querySelector('.rje-msg').textContent = message + loc; }}
  fetch('/api/client-error', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{message: message, source: source, lineno: lineno, colno: colno, stack: stack}}),
  }}).catch(function() {{}});
}};
window.addEventListener('unhandledrejection', function(e) {{
  const msg = (e.reason && e.reason.message) ? e.reason.message : String(e.reason);
  const stack = (e.reason && e.reason.stack) ? e.reason.stack : '';
  const banner = document.getElementById('report-js-error');
  if (banner) {{ banner.style.display = 'block'; banner.querySelector('.rje-msg').textContent = 'Unhandled error: ' + msg; }}
  fetch('/api/client-error', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{message: 'Unhandled rejection: ' + msg, source: '', lineno: '', colno: '', stack: stack}}),
  }}).catch(function() {{}});
}});
</script>
<script>
const JSON_FILE = '{json_filename}';
const EDIT_PLANS_FILE = '{edit_plans_filename}';
const JIRA_BASE_URL = '{jira_base_url}';
const TO_VERSION = '{to_version}';
const RUN_ID = {json.dumps(run_id)};
const APP_BASE = {json.dumps(app_base_url)};
const PAGE_SIZE = 25;
const LIKELIHOOD_ORDER = {{ high: 3, medium: 2, low: 1, none: 0 }};
const STATUS_KEY = 'fme_report_status_{run_id}';

let allData = [];
let filteredData = [];
let currentPage = 1;
let statusMap = {{}};  // rec_id -> "active" | "done" | "incorrect"

function loadStatusMap() {{
  try {{ statusMap = JSON.parse(localStorage.getItem(STATUS_KEY) || '{{}}'); }}
  catch(e) {{ statusMap = {{}}; }}
}}

function saveStatusMap() {{
  try {{ localStorage.setItem(STATUS_KEY, JSON.stringify(statusMap)); }}
  catch(e) {{}}
}}

function getStatus(rec_id) {{
  return statusMap[rec_id] || 'active';
}}

// Deep-link coordination: wait for both data sources before applying URL params
let _recsLoaded = false, _plansLoaded = false;
function leCheckBothLoaded() {{
  if (_recsLoaded && (_plansLoaded || !EDIT_PLANS_FILE)) leApplyUrlParams();
}}

// Load data
fetch(JSON_FILE)
  .then(r => {{
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }})
  .then(data => {{
    allData = data.assessments || [];
    loadStatusMap();
    initFilters();
    applyFilters();
    _recsLoaded = true;
    leCheckBothLoaded();
  }})
  .catch(err => {{
    document.getElementById('fetch-error').style.display = 'block';
    console.error('Failed to load', JSON_FILE, err);
  }});

function initFilters() {{
  // Populate learning path dropdown
  const lps = [...new Set(allData.map(a => a.learning_path))].sort();
  const lpSel = document.getElementById('lp-filter');
  lps.forEach(lp => {{
    const o = document.createElement('option');
    o.value = lp; o.textContent = lp;
    lpSel.appendChild(o);
  }});

  // Stats chips
  const counts = {{ high: 0, medium: 0, low: 0, none: 0 }};
  allData.forEach(a => {{ if (counts[a.update_likelihood] !== undefined) counts[a.update_likelihood]++; }});
  const statsEl = document.getElementById('stats');
  statsEl.innerHTML =
    `<span class="stat-chip total">Total: ${{allData.length.toLocaleString()}}</span>` +
    `<span class="stat-chip high">High: ${{counts.high}}</span>` +
    `<span class="stat-chip medium">Medium: ${{counts.medium}}</span>` +
    `<span class="stat-chip low">Low: ${{counts.low}}</span>` +
    `<span class="stat-chip none">None: ${{counts.none}}</span>`;

  // Bind events
  document.querySelectorAll('.lf-check').forEach(cb => cb.addEventListener('change', applyFilters));
  document.querySelectorAll('.sf-check').forEach(cb => cb.addEventListener('change', applyFilters));
  document.getElementById('lp-filter').addEventListener('change', () => {{ updateCourseFilter(); updateLessonFilter(); applyFilters(); }});
  document.getElementById('course-filter').addEventListener('change', () => {{ updateLessonFilter(); applyFilters(); }});
  document.getElementById('lesson-filter').addEventListener('change', applyFilters);
  document.getElementById('sort-select').addEventListener('change', applyFilters);
  document.getElementById('search-box').addEventListener('input', applyFilters);
  document.getElementById('exercise-filter').addEventListener('change', applyFilters);
  document.getElementById('screenshot-filter').addEventListener('change', applyFilters);
  updateCourseFilter();
  updateLessonFilter();
}}

function updateCourseFilter() {{
  const lp = document.getElementById('lp-filter').value;
  const courses = [...new Set(
    allData.filter(a => !lp || a.learning_path === lp).map(a => a.course_canonical)
  )].sort();
  const sel = document.getElementById('course-filter');
  sel.innerHTML = '<option value="">All</option>';
  courses.forEach(c => {{
    const o = document.createElement('option');
    o.value = c; o.textContent = c;
    sel.appendChild(o);
  }});
}}

function updateLessonFilter() {{
  const lp = document.getElementById('lp-filter').value;
  const course = document.getElementById('course-filter').value;
  const lessons = [...new Set(
    allData
      .filter(a => (!lp || a.learning_path === lp) && (!course || a.course_canonical === course))
      .map(a => a.lesson_name)
  )].sort();
  const sel = document.getElementById('lesson-filter');
  sel.innerHTML = '<option value="">All</option>';
  lessons.forEach(l => {{
    const o = document.createElement('option');
    o.value = l; o.textContent = l;
    sel.appendChild(o);
  }});
}}

function applyFilters() {{
  const checkedLikelihoods = new Set(
    [...document.querySelectorAll('.lf-check:checked')].map(cb => cb.value)
  );
  const lp = document.getElementById('lp-filter').value;
  const course = document.getElementById('course-filter').value;
  const lesson = document.getElementById('lesson-filter').value;
  const search = document.getElementById('search-box').value.toLowerCase().trim();
  const sort = document.getElementById('sort-select').value;

  const checkedStatuses = new Set(
    [...document.querySelectorAll('.sf-check:checked')].map(cb => cb.value)
  );
  const exerciseOnly = document.getElementById('exercise-filter').checked;
  const screenshotOnly = document.getElementById('screenshot-filter').checked;

  filteredData = allData.filter(a => {{
    if (!checkedLikelihoods.has(a.update_likelihood)) return false;
    if (!checkedStatuses.has(getStatus(a.rec_id))) return false;
    if (exerciseOnly && !a.impacts_exercise) return false;
    if (screenshotOnly && !a.screenshots_need_retaking) return false;
    if (lp && a.learning_path !== lp) return false;
    if (course && a.course_canonical !== course) return false;
    if (lesson && a.lesson_name !== lesson) return false;
    if (search) {{
      const hay = [a.lesson_name, a.course_canonical, a.learning_path,
                   a.issue_key, a.issue_summary, a.justification].join(' ').toLowerCase();
      if (!hay.includes(search)) return false;
    }}
    return true;
  }});

  filteredData.sort((a, b) => {{
    if (sort === 'likelihood-desc') return (LIKELIHOOD_ORDER[b.update_likelihood] || 0) - (LIKELIHOOD_ORDER[a.update_likelihood] || 0);
    if (sort === 'likelihood-asc') return (LIKELIHOOD_ORDER[a.update_likelihood] || 0) - (LIKELIHOOD_ORDER[b.update_likelihood] || 0);
    if (sort === 'lesson-asc') return (a.lesson_name || '').localeCompare(b.lesson_name || '');
    if (sort === 'issue-asc') return (a.issue_key || '').localeCompare(b.issue_key || '');
    return 0;
  }});

  currentPage = 1;
  renderPage();
}}

function renderPage() {{
  const container = document.getElementById('cards-container');
  const noResults = document.getElementById('no-results');

  if (filteredData.length === 0) {{
    container.innerHTML = '';
    noResults.style.display = 'block';
    document.getElementById('pagination-top').style.display = 'none';
    document.getElementById('pagination-bottom').style.display = 'none';
    return;
  }}

  noResults.style.display = 'none';
  const totalPages = Math.ceil(filteredData.length / PAGE_SIZE);
  const start = (currentPage - 1) * PAGE_SIZE;
  const pageItems = filteredData.slice(start, start + PAGE_SIZE);

  container.innerHTML = pageItems.map(renderCard).join('');

  // Sync both pagination bars
  ['top', 'bottom'].forEach(side => {{
    document.getElementById('pagination-' + side).style.display = 'flex';
    document.getElementById('page-info-' + side).textContent =
      `Page ${{currentPage}} of ${{totalPages}} (${{filteredData.length.toLocaleString()}} results)`;
    document.getElementById('prev-btn-' + side).disabled = currentPage === 1;
    document.getElementById('next-btn-' + side).disabled = currentPage === totalPages;
  }});
}}

function prevPage() {{ if (currentPage > 1) {{ currentPage--; renderPage(); window.scrollTo(0,0); }} }}
function nextPage() {{
  const totalPages = Math.ceil(filteredData.length / PAGE_SIZE);
  if (currentPage < totalPages) {{ currentPage++; renderPage(); window.scrollTo(0,0); }}
}}

function setStatus(rec_id, status) {{
  statusMap[rec_id] = status;
  saveStatusMap();
  // Update card in-place without full re-render
  const card = document.querySelector(`.card[data-rec="${{rec_id}}"]`);
  if (card) {{
    card.dataset.status = status;
    card.querySelectorAll('.status-btn').forEach(btn => {{
      btn.classList.toggle('sel', btn.dataset.status === status);
    }});
  }}
  // Issue 30: if marked Incorrect, auto-reject all corresponding HTML changes
  if (status === 'incorrect') {{
    const rec = allData.find(a => a.rec_id === rec_id);
    if (rec && rec.issue_key) {{
      leRejectAllForIssueKey(rec.issue_key);
    }}
  }}
  // Re-apply filters so card disappears if status filter hides it
  applyFilters();
}}

function renderCard(a) {{
  const likelihoodClass = a.update_likelihood || 'none';
  const status = getStatus(a.rec_id);
  const screenshotBadge = a.screenshots_need_retaking
    ? '<span class="badge screenshot">📷 Screenshots needed</span>' : '';
  const exerciseBadge = a.impacts_exercise
    ? '<span class="badge exercise">🏋 Impacts Exercise</span>' : '';
  const productBadges = (a.product || []).map(p => {{
    const cls = p === 'fme_form' ? 'fme-form' : 'fme-flow';
    const label = p === 'fme_form' ? 'FME Form' : 'FME Flow';
    return `<span class="badge ${{cls}}">${{label}}</span>`;
  }}).join('');

  const headings = a.affected_headings || [];
  const affectedHtml = headings.length > 0
    ? `<details class="assessment-section">
        <summary>${{headings.length}} affected heading${{headings.length !== 1 ? 's' : ''}}</summary>
        <div class="section-body"><ul>${{headings.map(h => `<li>${{escHtml(h)}}</li>`).join('')}}</ul></div>
      </details>`
    : '';

  const screenshots = a.affected_screenshots || [];
  const lessonDir = a.lesson_dir || '';
  const screenshotDetailsHtml = screenshots.length > 0
    ? `<details class="assessment-section">
        <summary>📷 ${{screenshots.length}} screenshot${{screenshots.length !== 1 ? 's' : ''}} need retaking</summary>
        <div class="section-body"><ul>
          ${{screenshots.map(s => {{
            const imgUrl = lessonDir ? `../${{lessonDir}}/${{escHtml(s.src || '')}}` : escHtml(s.src || '');
            return `<li class="screenshot-item">
              <a class="ss-img" href="${{imgUrl}}" target="_blank" title="Open full size">
                <img src="${{imgUrl}}" alt="${{escHtml(s.src || '')}}" loading="lazy">
              </a>
              <div class="ss-src">${{escHtml(s.src || '')}}</div>
              <div class="ss-exp">${{escHtml(s.explanation || '')}}</div>
            </li>`;
          }}).join('')}}
        </ul></div>
      </details>`
    : '';

  const rid = escHtml(a.rec_id || '');

  // Issue 37: build Update Suggestions section from leEditPlans
  let updateSuggestionsHtml = '';
  if (leEditPlans.length && a.issue_key) {{
    const relatedChanges = [];
    leEditPlans.forEach(plan => {{
      (plan.changes || []).forEach(ch => {{
        if ((ch.issue_keys || []).includes(a.issue_key)) {{
          relatedChanges.push({{ lessonId: plan.lesson_id, lessonName: plan.lesson_name, changeId: ch.change_id, heading: ch.heading }});
        }}
      }});
    }});
    if (relatedChanges.length) {{
      const links = relatedChanges.map(c =>
        `<li data-change-id="${{escHtml(c.changeId)}}"><a href="?tab=lesson-edits&lesson=${{encodeURIComponent(c.lessonId)}}&change=${{encodeURIComponent(c.changeId)}}" onclick="leNavigateToChange(event,'${{escHtml(c.lessonId)}}','${{escHtml(c.changeId)}}');return false;">${{escHtml(c.lessonName)}} — ${{escHtml(c.heading || 'change')}}</a></li>`
      ).join('');
      updateSuggestionsHtml = `<details class="assessment-section">
        <summary>✏ ${{relatedChanges.length}} edit suggestion${{relatedChanges.length !== 1 ? 's' : ''}}</summary>
        <div class="section-body"><ul class="edit-suggestion-list">${{links}}</ul></div>
      </details>`;
    }}
  }}

  return `
<div class="card" id="card-${{rid}}" data-rec="${{rid}}" data-status="${{status}}">
  <div class="card-header">
    <div>
      <div class="card-title">${{escHtml(a.lesson_name || '')}}</div>
      <div class="card-meta">
        ${{escHtml(a.course_canonical || '')}} &nbsp;›&nbsp; ${{escHtml(a.learning_path || '')}}
        &nbsp;|&nbsp; v${{escHtml(a.version || '')}}
        ${{a.rec_id ? `<span class="rec-id" onclick="copyRecId(this,'${{rid}}')" title="Click to copy">#${{rid}}</span>` : ''}}
      </div>
    </div>
    <div class="card-badges">
      <span class="badge ${{likelihoodClass}}">${{(likelihoodClass).toUpperCase()}}</span>
      ${{exerciseBadge}}
      ${{screenshotBadge}}
      ${{productBadges}}
      <div class="status-btns">
        <button class="status-btn active${{status==='active'?' sel':''}}" data-status="active" onclick="setStatus('${{rid}}','active')" title="Mark as active">Active</button>
        <button class="status-btn done${{status==='done'?' sel':''}}" data-status="done" onclick="setStatus('${{rid}}','done')" title="Mark as done">Done</button>
        <button class="status-btn incorrect${{status==='incorrect'?' sel':''}}" data-status="incorrect" onclick="setStatus('${{rid}}','incorrect')" title="Mark as incorrect">Incorrect</button>
      </div>
    </div>
  </div>
  <div class="card-body">
    <div class="card-section">
      <h4>Jira Issue</h4>
      <p>
        ${{JIRA_BASE_URL
          ? `<a href="${{JIRA_BASE_URL}}/browse/${{escHtml(a.issue_key || '')}}" target="_blank" rel="noopener" style="font-weight:700;color:#1a3d6b">${{escHtml(a.issue_key || '')}}</a>`
          : `<strong>${{escHtml(a.issue_key || '')}}</strong>`
        }}
        <span class="badge issue-type" style="margin-left:6px">${{escHtml(a.issue_type || '')}}</span>
      </p>
      <p style="margin-top:4px">${{escHtml(a.issue_summary || '')}}</p>
      ${{(a.fix_versions || []).length ? `<p style="font-size:0.78rem;color:#888;margin-top:2px">Fix version: ${{escHtml((a.fix_versions || []).join(', '))}}</p>` : ''}}
    </div>
    <div class="card-section">
      <h4>Assessment</h4>
      <details class="assessment-section" open>
        <summary>Summary</summary>
        <div class="section-body"><p class="justification">${{escHtml(a.justification || '')}}</p></div>
      </details>
      ${{affectedHtml}}
      ${{screenshotDetailsHtml}}
      ${{updateSuggestionsHtml}}
    </div>
  </div>
</div>`;
}}

function copyRecId(el, id) {{
  navigator.clipboard.writeText(id).then(() => {{
    el.classList.add('copied');
    el.textContent = '✓ copied';
    setTimeout(() => {{
      el.classList.remove('copied');
      el.textContent = '#' + id;
    }}, 1500);
  }}).catch(() => {{
    const range = document.createRange();
    range.selectNode(el);
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(range);
  }});
}}

function escHtml(str) {{
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}}

// ---------------------------------------------------------------------------
// KNOW-2279: one floating toast for all editor feedback (success/error).
// ---------------------------------------------------------------------------
let leMsgTimer = null;
function leShowMessage(text, variant, opts) {{
  opts = opts || {{}};
  const banner = document.getElementById('le-save-banner');
  if (!banner) return;
  if (leMsgTimer) {{ clearTimeout(leMsgTimer); leMsgTimer = null; }}
  banner.classList.remove('le-msg-success', 'le-msg-error');
  banner.classList.add(variant === 'error' ? 'le-msg-error' : 'le-msg-success');
  if (opts.html != null) banner.innerHTML = opts.html; else banner.textContent = text || '';
  banner.style.display = 'block';
  if (opts.autoHide) leMsgTimer = setTimeout(() => {{ banner.style.display = 'none'; }}, opts.autoHide);
}}
function leHideMessage() {{
  const banner = document.getElementById('le-save-banner');
  if (!banner) return;
  banner.style.display = 'none';
  banner.classList.remove('le-msg-success', 'le-msg-error');
}}

// ---------------------------------------------------------------------------
// Tab switching
// ---------------------------------------------------------------------------
function switchTab(name, btn) {{
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
  // Show/hide floating edit nav (issue 47)
  if (name === 'lesson-edits') {{
    leUpdateNavFloat();
  }} else {{
    document.getElementById('le-nav-float').style.display = 'none';
  }}
}}

// ---------------------------------------------------------------------------
// Lesson Edits tab
// ---------------------------------------------------------------------------
let leEditPlans = [];
let leUndoStack = [];
let leRedoStack = [];
let leSelectedImage = null; // KNOW-2279: <img> targeted by the alt-text/replace popover
let leImgPendingTarget = null; // KNOW-2279: <img> captured when a replace/upload begins (survives the async file dialog)
let leImgPendingMode = null;   // KNOW-2279: 'replace' | 'insert'
let leRejectedIssueKeys = new Set(); // tracks keys rejected from Recommendations tab (issue 30)

// KNOW-2277: per-run draft state from the FastAPI /api/runs/<id>/report-drafts
// endpoint. Keyed by lesson_dir. Populated once on page load via leLoadDrafts(),
// then mutated as the user edits and auto-saves.
let leDrafts = {{}};
let leDraftsLoaded = false;
// Autosave plumbing — debounced single-timer trailing-edge.
let leAutosaveTimer = null;
let leAutosaveBackoff = 0;          // 0 = no error; otherwise next retry delay in ms
let leAutosaveLastTrigger = null;   // {{ lessonDir }} held while a save is in-flight
let leAutosaveStatusInterval = null;// updates the "Saved 5s ago" relative time

function leAutosaveStatusEl() {{ return document.getElementById('le-autosave-status'); }}
function leSetAutosaveState(state, msg) {{
  const el = leAutosaveStatusEl();
  if (!el) return;
  el.dataset.state = state;
  el.textContent = msg;
}}
function leFormatRelativeTime(t) {{
  if (!t) return '';
  const sec = Math.max(1, Math.round((Date.now() - t) / 1000));
  if (sec < 60) return sec + 's ago';
  const m = Math.round(sec / 60);
  if (m < 60) return m + 'm ago';
  const h = Math.round(m / 60);
  return h + 'h ago';
}}
function leTickIdleStatus() {{
  const el = leAutosaveStatusEl();
  if (!el || el.dataset.state !== 'idle') return;
  const t = parseInt(el.dataset.savedAt || '0', 10);
  el.textContent = t ? 'Saved ' + leFormatRelativeTime(t) : '';
}}
if (typeof window !== 'undefined' && !leAutosaveStatusInterval) {{
  leAutosaveStatusInterval = setInterval(leTickIdleStatus, 5000);
}}

function leCurrentLessonDir() {{
  const lessonId = document.getElementById('le-lesson-filter').value;
  if (!lessonId) return null;
  const plan = leEditPlans.find(l => l.lesson_id === lessonId);
  return plan ? (plan.lesson_dir || null) : null;
}}

function leDraftPayload(lessonDir) {{
  // Decisions map (changeId -> accepted/rejected/pending) harvested from
  // every .tc-wrap currently in the editor.
  const decisions = {{}};
  document.querySelectorAll('#le-lesson-body .tc-wrap[data-id]').forEach(wrap => {{
    decisions[wrap.dataset.id] = wrap.dataset.state || 'pending';
  }});
  const bodyEl = document.getElementById('le-lesson-body');
  const body_html = bodyEl && bodyEl.contentEditable === 'true' ? bodyEl.innerHTML : null;
  const existing = leDrafts[lessonDir] || {{}};
  return {{
    lesson_dir: lessonDir,
    decisions: decisions,
    body_html: body_html,
    expected_updated_at: existing.updated_at || null,
  }};
}}

async function leAutosaveNow() {{
  if (!leDraftsLoaded) return;
  const trigger = leAutosaveLastTrigger;
  leAutosaveLastTrigger = null;
  if (!trigger) return;
  const lessonDir = trigger.lessonDir;
  if (!lessonDir) return;
  const payload = leDraftPayload(lessonDir);
  leSetAutosaveState('saving', 'Saving…');
  try {{
    const res = await fetch(APP_BASE + '/api/runs/' + encodeURIComponent(RUN_ID) + '/report-drafts', {{
      method: 'PUT',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify(payload),
    }});
    if (res.status === 409) {{
      const data = await res.json().catch(() => ({{}}));
      const current = (data && data.detail && data.detail.current) || null;
      if (current) {{
        leDrafts[lessonDir] = current;
        leApplyDraftToDom(lessonDir, current);
      }}
      leSetAutosaveState('error', 'Reloaded from another tab');
      leAutosaveBackoff = 0;
      return;
    }}
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    leDrafts[lessonDir] = Object.assign({{}}, leDrafts[lessonDir] || {{}}, {{
      decisions: payload.decisions,
      body_html: payload.body_html,
      updated_at: data.updated_at,
    }});
    const el = leAutosaveStatusEl();
    if (el) el.dataset.savedAt = String(Date.now());
    leSetAutosaveState('idle', 'Saved a moment ago');
    leAutosaveBackoff = 0;
  }} catch (err) {{
    // Network or 5xx — back off and retry. Drop older queued payloads;
    // we're sending a full snapshot, so the latest one supersedes them.
    leAutosaveBackoff = leAutosaveBackoff ? Math.min(leAutosaveBackoff * 2, 30000) : 1000;
    leSetAutosaveState('error', "Couldn't save — retrying");
    leAutosaveLastTrigger = {{ lessonDir }};
    if (leAutosaveTimer) clearTimeout(leAutosaveTimer);
    leAutosaveTimer = setTimeout(leAutosaveNow, leAutosaveBackoff);
  }}
}}

function leScheduleAutosave(lessonDir) {{
  if (!leDraftsLoaded || !lessonDir) return;
  leAutosaveLastTrigger = {{ lessonDir }};
  if (leAutosaveTimer) clearTimeout(leAutosaveTimer);
  // 1000ms trailing-edge debounce. Faster when we're already retrying.
  const delay = leAutosaveBackoff || 1000;
  leAutosaveTimer = setTimeout(leAutosaveNow, delay);
}}

async function leLoadDrafts() {{
  try {{
    const res = await fetch(APP_BASE + '/api/runs/' + encodeURIComponent(RUN_ID) + '/report-drafts');
    if (!res.ok) throw new Error('HTTP ' + res.status);
    const data = await res.json();
    leDrafts = (data && data.lessons) || {{}};
  }} catch (err) {{
    // Drafts are best-effort — if the FastAPI app isn't reachable (e.g.
    // dev opening the report from file:// or via serve.py only), the
    // editor still works without persistence. Log and move on.
    console.warn('Could not load drafts:', err);
    leDrafts = {{}};
  }}
  leDraftsLoaded = true;
}}

function leApplyDraftToDom(lessonDir, draft) {{
  if (!draft) return;
  const decisions = draft.decisions || {{}};
  document.querySelectorAll('#le-lesson-body .tc-wrap[data-id]').forEach(wrap => {{
    const persisted = decisions[wrap.dataset.id];
    if (persisted && persisted !== wrap.dataset.state) {{
      leApplyState(wrap, persisted);
    }}
  }});
  // body_html replacement is intentionally skipped here. The full
  // body innerHTML is re-applied during leRenderLesson() before this
  // is called, so re-setting it would no-op; and on a 409 reload mid-
  // edit we don't want to clobber the user's keystrokes between the
  // moment they hit save and the moment we got back the conflict.
  // Decisions alone are enough to bring the editor back into sync.
}}

async function leResetLesson() {{
  const lessonDir = leCurrentLessonDir();
  if (!lessonDir) return;
  if (!confirm('Discard editor changes for this lesson and reload the original suggestions?')) return;
  try {{
    const res = await fetch(APP_BASE + '/api/runs/' + encodeURIComponent(RUN_ID) + '/report-drafts/reset', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{ lesson_dir: lessonDir }}),
    }});
    if (!res.ok) throw new Error('HTTP ' + res.status);
  }} catch (err) {{
    alert("Couldn't reset draft: " + err.message);
    return;
  }}
  delete leDrafts[lessonDir];
  // Re-render the lesson from scratch — leRenderLesson() reads from
  // leEditPlans so this restores the original recommendations DOM.
  // Suppress autosave while we do this to avoid resaving the freshly-
  // reset state back to the server. try/finally so a thrown render
  // never leaves leDraftsLoaded=false (which would silently kill all
  // future autosaves until reload).
  leDraftsLoaded = false;
  try {{
    leRenderLesson();
  }} finally {{
    leDraftsLoaded = true;
  }}
  const el = leAutosaveStatusEl();
  if (el) {{ el.dataset.savedAt = ''; }}
  leSetAutosaveState('idle', 'Reset');
}}

// Eager-load edit plans on page load (needed for cross-tab features in issues 37, 30)
if (EDIT_PLANS_FILE) {{
  Promise.all([
    fetch(EDIT_PLANS_FILE).then(r => r.json()),
    leLoadDrafts(),
  ])
    .then(([data]) => {{
      leEditPlans = data.lessons || [];
      lePopulateFilters();
      _plansLoaded = true;
      leCheckBothLoaded();
    }})
    .catch(() => {{
      document.getElementById('le-lesson-body').innerHTML =
        '<div class="lesson-edit-empty" style="color:#b91c1c">Could not load edit plans JSON.</div>';
    }});
}}

function lePopulateFilters() {{
  const lpSel = document.getElementById('le-lp-filter');
  const courseSel = document.getElementById('le-course-filter');
  const lessonSel = document.getElementById('le-lesson-filter');

  const lps = [...new Set(leEditPlans.map(l => l.learning_path).filter(Boolean))].sort();
  lps.forEach(lp => lpSel.appendChild(new Option(lp, lp)));

  lpSel.addEventListener('change', () => leUpdateCourses());
  courseSel.addEventListener('change', () => leUpdateLessons());
  lessonSel.addEventListener('change', () => leRenderLesson());
  leUpdateCourses();
}}

function leUpdateCourses() {{
  const lp = document.getElementById('le-lp-filter').value;
  const courseSel = document.getElementById('le-course-filter');
  courseSel.innerHTML = '<option value="">All</option>';
  const courses = [...new Set(
    leEditPlans.filter(l => !lp || l.learning_path === lp).map(l => l.course_canonical).filter(Boolean)
  )].sort();
  courses.forEach(c => courseSel.appendChild(new Option(c, c)));
  leUpdateLessons();
}}

function leUpdateLessons() {{
  const lp = document.getElementById('le-lp-filter').value;
  const course = document.getElementById('le-course-filter').value;
  const lessonSel = document.getElementById('le-lesson-filter');
  lessonSel.innerHTML = '<option value="">-- Select a lesson --</option>';
  leEditPlans
    .filter(l => (!lp || l.learning_path === lp) && (!course || l.course_canonical === course))
    .forEach(l => lessonSel.appendChild(new Option(l.lesson_name, l.lesson_id)));
  const _emptyBodyEl = document.getElementById('le-lesson-body');
  _emptyBodyEl.innerHTML = '<div class="lesson-edit-empty">Select a lesson above to view suggested edits.</div>';
  _emptyBodyEl.contentEditable = 'false';
  document.getElementById('le-fmt-toolbar').style.display = 'none';
  document.getElementById('le-change-count').textContent = '';
  document.getElementById('le-toolbar').style.display = 'none';
  document.getElementById('le-nav-float').style.display = 'none';
}}

function leRenderLesson() {{
  const lessonId = document.getElementById('le-lesson-filter').value;
  if (!lessonId) return;
  const plan = leEditPlans.find(l => l.lesson_id === lessonId);
  if (!plan) return;

  // KNOW-2279: drop any open image-edit popover before innerHTML below
  // detaches the <img> it points at, otherwise Save/Replace would silently
  // mutate the now-orphaned node.
  leImgClosePopover();

  leUndoStack = [];
  leRedoStack = [];
  leUpdateHistoryBtns();

  const changes = plan.changes || [];
  const screenshots = plan.screenshot_updates || [];
  const altTextUpdates = plan.alt_text_updates || [];
  const totalChanges = changes.length + screenshots.length + altTextUpdates.length;

  const parts = [];
  if (changes.length) parts.push(`${{changes.length}} text change${{changes.length !== 1 ? 's' : ''}}`);
  if (screenshots.length) parts.push(`${{screenshots.length}} screenshot note${{screenshots.length !== 1 ? 's' : ''}}`);
  if (altTextUpdates.length) parts.push(`${{altTextUpdates.length}} alt text suggestion${{altTextUpdates.length !== 1 ? 's' : ''}}`);
  document.getElementById('le-change-count').textContent = parts.length ? parts.join(', ') : 'No changes suggested';
  document.getElementById('le-toolbar').style.display = totalChanges > 0 ? 'flex' : 'none';

  let html = plan.lesson_html || '<p><em>No lesson HTML available.</em></p>';

  // Helper: build unified popup markup for a change
  function makePopup(changeId, explanation, issueKeys, type, lessonId) {{
    const keys = issueKeys || [];
    const issueLinks = keys.map(k =>
      JIRA_BASE_URL ? `<a href="${{JIRA_BASE_URL}}/browse/${{k}}" target="_blank" rel="noopener" style="color:#93c5fd">${{k}}</a>` : k
    ).join(', ');
    // Issues 29/51/68: view card link with pushState navigation
    const cardLink = keys.length
      ? `<span class="card-link-wrap" style="display:block;font-size:0.7rem;margin-top:2px"><a class="card-link" href="?tab=recommendations&card=${{encodeURIComponent(allData.find(a=>a.issue_key===keys[0])?.rec_id||'')}}&from_change=${{encodeURIComponent(changeId)}}" onclick="leNavigateToCard(event,'${{keys[0]}}','${{lessonId||''}}','${{changeId}}');return false;" style="color:#93c5fd">↗ View recommendation card (${{keys[0]}})</a></span>`
      : '';
    // Issue 51/66: copy-chip for linking directly to this change
    const copyChip = (lessonId && type !== 'screenshot')
      ? `<span class="rec-id" onclick="navigator.clipboard.writeText(location.origin+location.pathname+'?tab=lesson-edits&lesson='+encodeURIComponent('${{lessonId}}')+'&change='+encodeURIComponent('${{changeId}}'))" title="Copy link to this change" style="margin-left:4px">#${{changeId.slice(0,8)}}</span>`
      : '';
    // Issue 28: reject-all button for first issue key (text changes only)
    const rejectAllBtn = (keys.length && type !== 'screenshot')
      ? `<button class="tc-reject" style="font-size:0.68rem" onclick="leRejectAllForIssueKey('${{keys[0]}}');setStatus(allData.find(a=>a.issue_key==='${{keys[0]}}')?.rec_id||'','incorrect');event.stopPropagation()">✗✗ Reject all for ${{keys[0]}}</button>`
      : '';
    return `<span class="tc-popup" data-popup="${{changeId}}"><span class="tc-btns"><button class="tc-accept" onmousedown="event.stopPropagation();event.preventDefault();" onclick="leAccept('${{changeId}}',event)">✓ Accept</button><button class="tc-reject" onmousedown="event.stopPropagation();event.preventDefault();" onclick="leReject('${{changeId}}',event)">✗ Reject</button>${{rejectAllBtn}}</span><span class="tc-explanation">${{escHtml(explanation || '')}}</span><span class="tc-issue-links">${{issueLinks}}${{copyChip}}${{cardLink}}</span></span>`;
  }}

  // Apply text changes in a single right-to-left pass so that injected markup
  // (which contains orig in data-orig / <del>) never gets re-matched by a
  // subsequent change with the same original_text.
  //
  // Algorithm:
  //   1. For each change, find the next unmatched occurrence of orig in html
  //      (scanning left-to-right, skipping positions already claimed).
  //   2. If the position is inside an <a> element's content, expand the range
  //      to enclose the whole <a> — the wrap (with its popup containing
  //      buttons / links) cannot legally nest inside <a> per HTML5 rules
  //      (KNOW-2255), so it must surround the <a> instead.
  //   3. Collect all (position, change) pairs.
  //   4. Replace right-to-left so earlier offsets stay valid.

  // Walk back from `pos` to determine whether it sits inside the content of
  // an open <a> element. Returns [start, end] of the enclosing <a> if so.
  function findEnclosingAnchor(html, pos) {{
    let depth = 0;
    let i = pos - 1;
    while (i >= 0) {{
      const close = html.lastIndexOf('</a>', i);
      const open  = html.lastIndexOf('<a', i);
      if (open < 0 && close < 0) return null;
      if (close > open) {{
        depth -= 1;
        i = close - 1;
      }} else {{
        // confirm <a> tag (next char is whitespace, > or attribute-start)
        const after = html[open + 2];
        const isAnchor = after === ' ' || after === '>' || after === '\\t' || after === '\\n' || after === '\\r';
        if (isAnchor) {{
          if (depth === 0) {{
            const endOfOpenTag = html.indexOf('>', open);
            if (endOfOpenTag < 0) return null;
            const closeTag = html.indexOf('</a>', endOfOpenTag + 1);
            if (closeTag < 0) return null;
            return [open, closeTag + 4];
          }}
          depth += 1;
        }}
        i = open - 1;
      }}
    }}
    return null;
  }}

  function makeMarkup(ch, origHtml, origText) {{
    const popup = makePopup(ch.change_id, ch.explanation, ch.issue_keys, ch.type, plan.lesson_id);
    const issueKeysAttr = escHtml((ch.issue_keys || []).join(','));
    const dataOrig = escHtml(origHtml);
    const visibleOrig = escHtml(origText);
    const dataSugg = escHtml(ch.suggested_text || '');
    if (ch.type === 'delete') {{
      return `<span id="le-change-${{ch.change_id}}" class="tc-wrap tc-change" contenteditable="false" data-id="${{ch.change_id}}" data-orig="${{dataOrig}}" data-orig-text="${{visibleOrig}}" data-sugg="" data-type="delete" data-issue-keys="${{issueKeysAttr}}" data-state="pending"><del class="tc-del">${{visibleOrig}}</del>${{popup}}</span>`;
    }} else if (ch.type === 'add') {{
      return `<span id="le-change-${{ch.change_id}}" class="tc-wrap tc-change" contenteditable="false" data-id="${{ch.change_id}}" data-orig="${{dataOrig}}" data-orig-text="${{visibleOrig}}" data-sugg="${{dataSugg}}" data-type="add" data-issue-keys="${{issueKeysAttr}}" data-state="pending"><span class="tc-orig-context">${{visibleOrig}}</span><ins class="tc-add">${{dataSugg}}</ins>${{popup}}</span>`;
    }}
    return `<span id="le-change-${{ch.change_id}}" class="tc-wrap tc-change" contenteditable="false" data-id="${{ch.change_id}}" data-orig="${{dataOrig}}" data-orig-text="${{visibleOrig}}" data-sugg="${{dataSugg}}" data-type="change" data-issue-keys="${{issueKeysAttr}}" data-state="pending"><del class="tc-del">${{visibleOrig}}</del><ins class="tc-ins"> ${{dataSugg}}</ins>${{popup}}</span>`;
  }}

  const claimed = [];  // sorted list of [start, end] ranges already assigned
  const replacements = [];  // {{ pos, origLen, markup }}

  changes.forEach((ch) => {{
    const orig = ch.original_text || '';
    if (!orig) return;

    // Find the first occurrence of orig not overlapping an already-claimed range
    // and not inside an HTML tag's attributes. If the match sits inside the
    // content of an <a>, expand the chosen range to enclose the whole <a>.
    let searchFrom = 0;
    while (searchFrom <= html.length - orig.length) {{
      const pos = html.indexOf(orig, searchFrom);
      if (pos === -1) break;
      const end = pos + orig.length;
      // Skip matches inside HTML tag attributes: scan backward for nearest < or >
      let insideTag = false;
      for (let i = pos - 1; i >= 0; i--) {{
        if (html[i] === '>') break;
        if (html[i] === '<') {{ insideTag = true; break; }}
      }}
      if (insideTag) {{ searchFrom = pos + 1; continue; }}

      // Default: wrap exactly the matched substring
      let chosenStart = pos;
      let chosenEnd   = end;
      let chosenOrigHtml = orig;
      let chosenOrigText = orig;

      // If we're inside an <a>, expand to cover the whole <a>...</a>
      const enclosing = findEnclosingAnchor(html, pos);
      if (enclosing) {{
        const [aStart, aEnd] = enclosing;
        chosenStart = aStart;
        chosenEnd   = aEnd;
        chosenOrigHtml = html.slice(aStart, aEnd);
        chosenOrigText = chosenOrigHtml
          .replace(/^<a\\b[^>]*>/i, '')
          .replace(/<\\/a>\\s*$/i, '');
      }}

      const overlaps = claimed.some(([s, e]) => chosenStart < e && chosenEnd > s);
      if (!overlaps) {{
        claimed.push([chosenStart, chosenEnd]);
        replacements.push({{
          pos: chosenStart,
          origLen: chosenEnd - chosenStart,
          markup: makeMarkup(ch, chosenOrigHtml, chosenOrigText),
        }});
        break;
      }}
      searchFrom = pos + 1;
    }}
  }});

  // Replace right-to-left so earlier positions remain valid
  replacements.sort((a, b) => b.pos - a.pos);
  replacements.forEach(({{ pos, origLen, markup }}) => {{
    html = html.slice(0, pos) + markup + html.slice(pos + origLen);
  }});

  // Inject screenshot notes (wrapped in tc-wrap for accept/reject)
  screenshots.forEach((su, idx) => {{
    if (!su.src) return;
    const ssId = 'ss-' + idx;
    const issueLinks = (su.issue_keys || []).map(k =>
      JIRA_BASE_URL ? `<a href="${{JIRA_BASE_URL}}/browse/${{k}}" target="_blank" rel="noopener">${{k}}</a>` : k
    ).join(', ');
    const altTextLine = su.alt_text
      ? `<div style="font-size:0.8rem;margin-top:4px"><em>Suggested alt text:</em> ${{escHtml(su.alt_text)}}</div>`
      : '';
    const sourceBadge = su.source === 'vision'
      ? '<span style="font-size:0.68rem;background:#dbeafe;color:#1e40af;border-radius:3px;padding:1px 5px;margin-left:5px;font-weight:normal">👁 vision</span>'
      : '';
    const noteInner = `<div class="screenshot-note"><strong>📷 Screenshot update needed (${{issueLinks}})${{sourceBadge}}</strong>${{escHtml(su.explanation || '')}}${{altTextLine}}</div>`;
    const popup = makePopup(ssId, su.explanation, su.issue_keys, 'screenshot', plan.lesson_id);
    const wrapped = `<div class="tc-wrap tc-change" contenteditable="false" data-id="${{ssId}}" data-type="screenshot" data-issue-keys="${{escHtml((su.issue_keys||[]).join(','))}}" data-state="pending">${{noteInner}}${{popup}}</div>`;
    const imgPattern = new RegExp(`(<img[^>]*src="${{su.src.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&')}}"[^>]*>)`, 'i');
    html = html.replace(imgPattern, '$1' + wrapped);
  }});

  // Inject alt text update cards after matching <img> tags (issue 53)
  altTextUpdates.forEach((au, idx) => {{
    if (!au.src) return;
    const atId = 'at-' + idx;
    const noteInner = `<div class="alt-text-note">` +
      `<strong>🏷 Alt text update suggested</strong>` +
      `<div class="alt-row"><span class="alt-label">Current:</span><span class="alt-val">${{escHtml(au.original_alt || '(none)')}}</span></div>` +
      `<div class="alt-row"><span class="alt-label">Suggested:</span><span class="alt-val"><strong>${{escHtml(au.suggested_alt || '')}}</strong></span></div>` +
      `</div>`;
    const popup = makePopup(atId, au.explanation, [], 'alt-text', plan.lesson_id);
    const wrapped = `<div class="tc-wrap tc-change" contenteditable="false" data-id="${{atId}}" data-type="alt-text" data-src="${{escHtml(au.src)}}" data-orig-alt="${{escHtml(au.original_alt || '')}}" data-sugg-alt="${{escHtml(au.suggested_alt || '')}}" data-state="pending">${{noteInner}}${{popup}}</div>`;
    const imgPattern = new RegExp(`(<img[^>]*src="${{au.src.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&')}}"[^>]*>)`, 'i');
    html = html.replace(imgPattern, '$1' + wrapped);
  }});

  document.getElementById('le-lesson-body').innerHTML = html;

  // Fix relative image paths via DOM — more reliable than regex (issue 61)
  const lessonBase = '../' + (plan.lesson_dir || '').split('/').map(s => encodeURIComponent(s)).join('/') + '/';
  document.querySelectorAll('#le-lesson-body img').forEach(img => {{
    const src = img.getAttribute('src') || '';
    if (!src.startsWith('http') && !src.startsWith('/') && !src.startsWith('data:') && !src.startsWith('blob:') && !src.startsWith('..')) {{
      img.setAttribute('src', lessonBase + src);
    }}
  }});
  document.getElementById('le-save-banner').style.display = 'none';
  leBindPopups();
  const _lessonBodyEl = document.getElementById('le-lesson-body');
  _lessonBodyEl.contentEditable = 'true';
  _lessonBodyEl.spellcheck = false;
  // KNOW-2275 (QA issue 1): make contenteditable emit <p>, not <div>, for blocks it
  // creates — including the blocks produced when a list is toggled OFF. Chrome defaults
  // this to 'div', and .lesson-edit-body div has no margin (only <p> gets margin:0.5em 0),
  // so toggling a multi-line list off collapsed the original paragraph spacing. <p> keeps it.
  document.execCommand('defaultParagraphSeparator', false, 'p');
  // KNOW-2275: rebind list keyboard handler each render (innerHTML wipes listeners).
  if (_lessonBodyEl._leListKeydownHandler) {{
    _lessonBodyEl.removeEventListener('keydown', _lessonBodyEl._leListKeydownHandler);
  }}
  _lessonBodyEl._leListKeydownHandler = leHandleListKeydown;
  _lessonBodyEl.addEventListener('keydown', leHandleListKeydown);
  document.getElementById('le-fmt-toolbar').style.display = 'flex';
  leUpdateNavFloat();
  // KNOW-2279: image-edit popover wiring (idempotent across re-renders)
  if (!_lessonBodyEl.dataset.imgEditWired) {{
    _lessonBodyEl.addEventListener('click', leOnImageClick);
    document.getElementById('le-img-file-input').addEventListener('change', leImgOnFileChosen);
    document.addEventListener('click', (e) => {{
      const pop = document.getElementById('le-img-popover');
      if (!pop.classList.contains('visible')) return;
      if (pop.contains(e.target)) return;
      if (e.target.closest && e.target.closest('#le-lesson-body img')) return;
      leImgClosePopover();
    }});
    document.addEventListener('keydown', (e) => {{
      if (e.key === 'Escape' && document.getElementById('le-img-popover').classList.contains('visible')) {{
        leImgClosePopover();
      }}
    }});
    _lessonBodyEl.dataset.imgEditWired = '1';
  }}
  // Issue 30: apply any rejections that were triggered from the Recommendations tab
  if (leRejectedIssueKeys.size) {{
    document.querySelectorAll('#le-lesson-body .tc-wrap[data-issue-keys]').forEach(wrap => {{
      const keys = (wrap.dataset.issueKeys || '').split(',').map(s => s.trim());
      if (keys.some(k => leRejectedIssueKeys.has(k)) && wrap.dataset.state !== 'rejected') {{
        leApplyState(wrap, 'rejected');
      }}
    }});
  }}
  // KNOW-2277: restore any persisted decisions for this lesson, then wire
  // the input listener so user keystrokes auto-save. Apply draft AFTER
  // adding the listener so the initial replay does not auto-save itself.
  // The wired flag keeps the listener idempotent across lesson switches —
  // the same #le-lesson-body element is reused, so an unguarded
  // addEventListener would stack one new listener per re-render.
  if (!_lessonBodyEl.dataset.inputWired) {{
    _lessonBodyEl.addEventListener('input', () => {{
      leScheduleAutosave(leCurrentLessonDir());
    }});
    _lessonBodyEl.dataset.inputWired = '1';
  }}
  const _draft = leDrafts && leDrafts[plan.lesson_dir];
  if (_draft) {{
    // Replay decisions silently (no autosave during replay). try/finally
    // so a thrown apply never leaves leDraftsLoaded=false permanently.
    const _wasLoaded = leDraftsLoaded;
    leDraftsLoaded = false;
    try {{
      leApplyDraftToDom(plan.lesson_dir, _draft);
    }} finally {{
      leDraftsLoaded = _wasLoaded;
    }}
    if (_draft.body_html && _draft.updated_at) {{
      // The decisions replay above is the source of truth for accept/reject;
      // body_html on disk includes the WYSIWYG keystrokes the user made
      // *after* those decisions, so it's safe to swap in.
      _lessonBodyEl.innerHTML = _draft.body_html;
      // Re-bind popups since we replaced the DOM.
      leBindPopups();
      _lessonBodyEl.contentEditable = 'true';
    }}
    const el = leAutosaveStatusEl();
    if (el && _draft.updated_at) {{
      el.dataset.savedAt = String(new Date(_draft.updated_at).getTime());
      leSetAutosaveState('idle', 'Saved ' + leFormatRelativeTime(parseInt(el.dataset.savedAt, 10)));
    }}
  }} else {{
    leSetAutosaveState('idle', '');
  }}
}}

// Phase 2: accept/reject
function leAccept(changeId, evt) {{
  if (evt) {{ evt.stopPropagation(); evt.preventDefault(); }}
  const wrap = document.querySelector(`.tc-wrap[data-id="${{changeId}}"]`);
  if (!wrap) return;
  const prev = wrap.dataset.state;
  leUndoStack.push({{ changeId, prev }});
  leRedoStack = [];
  leApplyState(wrap, 'accepted');
  leUpdateHistoryBtns();
  leScheduleAutosave(leCurrentLessonDir());
  // Hide popup after action
  const popup = wrap.querySelector('.tc-popup');
  if (popup) popup.classList.remove('tc-popup-visible');
}}

function leReject(changeId, evt) {{
  if (evt) {{ evt.stopPropagation(); evt.preventDefault(); }}
  const wrap = document.querySelector(`.tc-wrap[data-id="${{changeId}}"]`);
  if (!wrap) return;
  const prev = wrap.dataset.state;
  leUndoStack.push({{ changeId, prev }});
  leRedoStack = [];
  leApplyState(wrap, 'rejected');
  leUpdateHistoryBtns();
  leScheduleAutosave(leCurrentLessonDir());
  // Hide popup after action
  const popup = wrap.querySelector('.tc-popup');
  if (popup) popup.classList.remove('tc-popup-visible');
}}

function leApplyState(wrap, state) {{
  wrap.dataset.state = state;
  const type = wrap.dataset.type;
  // data-orig is the FULL HTML to restore on reject (may include an <a>);
  // data-orig-text is the plain inner text used for visible <del>/<span class=tc-orig>.
  const orig     = wrap.dataset.orig || '';
  const origText = wrap.dataset.origText || orig;
  const sugg     = wrap.dataset.sugg || '';

  // Screenshot type: just update the note's CSS class
  if (type === 'screenshot') {{
    const note = wrap.querySelector('.screenshot-note');
    if (note) {{
      note.className = 'screenshot-note' +
        (state === 'accepted' ? ' screenshot-note-accepted' : state === 'rejected' ? ' screenshot-note-rejected' : '');
    }}
    return;
  }}

  // Alt text type: update the note's CSS class
  if (type === 'alt-text') {{
    const note = wrap.querySelector('.alt-text-note');
    if (note) {{
      note.className = 'alt-text-note' +
        (state === 'accepted' ? ' alt-text-note-accepted' : state === 'rejected' ? ' alt-text-note-rejected' : '');
    }}
    return;
  }}

  // Remove existing content nodes (del/ins/orig) — keep popup and itself
  [...wrap.querySelectorAll('del.tc-del, ins.tc-ins, ins.tc-add, span.tc-orig, span.tc-orig-context')].forEach(n => n.remove());

  if (state === 'pending') {{
    if (type === 'delete') wrap.insertAdjacentHTML('afterbegin', `<del class="tc-del">${{origText}}</del>`);
    else if (type === 'add') wrap.insertAdjacentHTML('afterbegin', `<span class="tc-orig-context">${{origText}}</span><ins class="tc-add">${{sugg}}</ins>`);
    else wrap.insertAdjacentHTML('afterbegin', `<del class="tc-del">${{origText}}</del><ins class="tc-ins"> ${{sugg}}</ins>`);
  }} else if (state === 'accepted') {{
    if (type === 'delete') {{ /* nothing — text removed */ }}
    else if (type === 'add') wrap.insertAdjacentHTML('afterbegin', `<span class="tc-orig-context">${{origText}}</span><ins class="tc-ins">${{sugg}}</ins>`);
    else wrap.insertAdjacentHTML('afterbegin', `<ins class="tc-ins">${{sugg}}</ins>`);
  }} else {{ // rejected
    // Restore the full original HTML (may include an <a>) so links survive a reject.
    wrap.insertAdjacentHTML('afterbegin', `<span class="tc-orig">${{orig}}</span>`);
  }}
}}

// Issue 28/30: reject all changes for a given issue key (cross-tab)
function leRejectAllForIssueKey(issueKey) {{
  // Always record the key so auto-rejection applies when any lesson renders (issue 30)
  leRejectedIssueKeys.add(issueKey);
  document.querySelectorAll('#le-lesson-body .tc-wrap[data-issue-keys]').forEach(wrap => {{
    const keys = (wrap.dataset.issueKeys || '').split(',').map(s => s.trim());
    if (keys.includes(issueKey)) {{
      const prev = wrap.dataset.state;
      if (prev !== 'rejected') {{
        leUndoStack.push({{ changeId: wrap.dataset.id, prev }});
        leApplyState(wrap, 'rejected');
      }}
    }}
  }});
  leUpdateHistoryBtns();
  leScheduleAutosave(leCurrentLessonDir());
}}

// Issues 29/67/68: scroll to a card by rec_id, handle pagination, highlight originating change
function leShowCard(recId, fromChangeId) {{
  const tabBtn = document.querySelector('.tab-btn[onclick*="recommendations"]');
  if (tabBtn) switchTab('recommendations', tabBtn);
  // Navigate to the correct page (issue 67)
  const idx = filteredData.findIndex(a => a.rec_id === recId);
  if (idx >= 0) {{
    const targetPage = Math.floor(idx / PAGE_SIZE) + 1;
    if (currentPage !== targetPage) {{ currentPage = targetPage; renderPage(); }}
  }}
  setTimeout(() => {{
    const card = document.getElementById('card-' + recId);
    if (!card) return;
    card.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    card.classList.remove('card-highlight');
    void card.offsetWidth;
    card.classList.add('card-highlight');
    card.addEventListener('animationend', () => card.classList.remove('card-highlight'), {{ once: true }});
    // Issue 51/68: expand edit suggestions and highlight the originating change entry
    if (fromChangeId) {{
      card.querySelectorAll('details.assessment-section').forEach(d => {{
        if (d.querySelector('summary')?.textContent.includes('edit suggestion')) {{
          d.open = true;
          const li = d.querySelector(`li[data-change-id="${{fromChangeId}}"]`);
          if (li) li.classList.add('from-change-highlight');
        }}
      }});
    }}
  }}, 150);
}}

// Issue 68: pushState then show card
function leNavigateToCard(evt, issueKey, lessonId, changeId) {{
  evt.preventDefault();
  const rec = allData.find(a => a.issue_key === issueKey);
  if (!rec) return;
  const params = new URLSearchParams();
  params.set('tab', 'recommendations');
  params.set('card', rec.rec_id);
  if (changeId) params.set('from_change', changeId);
  history.pushState({{ tab: 'recommendations', card: rec.rec_id, fromChange: changeId || null }}, '', '?' + params.toString());
  leShowCard(rec.rec_id, changeId || null);
}}

// Issues 37/68: switch to Lesson Edits tab, set dropdowns, render, scroll to change
function leShowChange(lessonId, changeId) {{
  const tabBtn = document.querySelector('.tab-btn[onclick*="lesson-edits"]');
  if (tabBtn && !tabBtn.disabled) switchTab('lesson-edits', tabBtn);
  setTimeout(() => {{
    const plan = leEditPlans.find(l => l.lesson_id === lessonId);
    if (!plan) return;
    const lpSel = document.getElementById('le-lp-filter');
    if (lpSel && plan.learning_path) {{ lpSel.value = plan.learning_path; leUpdateCourses(); }}
    const courseSel = document.getElementById('le-course-filter');
    if (courseSel && plan.course_canonical) {{ courseSel.value = plan.course_canonical; leUpdateLessons(); }}
    const lessonSel = document.getElementById('le-lesson-filter');
    if (!lessonSel) return;
    lessonSel.value = lessonId;
    leRenderLesson();
    if (changeId) {{
      setTimeout(() => {{
        const wrap = document.getElementById('le-change-' + changeId);
        if (wrap) {{
          wrap.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
          wrap.style.outline = '2px solid #f59e0b';
          wrap.style.borderRadius = '3px';
          setTimeout(() => {{ wrap.style.outline = ''; wrap.style.borderRadius = ''; }}, 2000);
        }}
      }}, 100);
    }}
  }}, 150);
}}

// Issue 68: pushState then show change
function leNavigateToChange(evt, lessonId, changeId) {{
  evt.preventDefault();
  const params = new URLSearchParams();
  params.set('tab', 'lesson-edits');
  params.set('lesson', lessonId);
  if (changeId) params.set('change', changeId);
  history.pushState({{ tab: 'lesson-edits', lesson: lessonId, change: changeId || null }}, '', '?' + params.toString());
  leShowChange(lessonId, changeId || null);
}}

// Backward-compat shims
function leGoToCard(issueKey) {{ leShowCard(allData.find(a => a.issue_key === issueKey)?.rec_id, null); }}
function leGoToChange(lessonId, changeId) {{ leShowChange(lessonId, changeId); }}

// Issue 68: read URL params on load and navigate to the correct view
function leApplyUrlParams() {{
  const params = new URLSearchParams(window.location.search);
  const tab = params.get('tab');
  const card = params.get('card');
  const fromChange = params.get('from_change');
  const lesson = params.get('lesson');
  const change = params.get('change');
  if (tab === 'recommendations' && card) {{
    leShowCard(card, fromChange);
  }} else if (tab === 'lesson-edits' && lesson && leEditPlans.length) {{
    leShowChange(lesson, change);
  }}
}}

// Issue 68: handle browser back/forward
window.addEventListener('popstate', function(evt) {{
  const s = evt.state;
  if (!s) {{ leApplyUrlParams(); return; }}
  if (s.tab === 'recommendations') leShowCard(s.card, s.fromChange || null);
  else if (s.tab === 'lesson-edits') leShowChange(s.lesson, s.change || null);
}});

// Issue 47: floating next/prev edit navigation
let leCurrentEditIdx = -1;
let leEditWraps = [];

function leUpdateNavFloat() {{
  const navFloat = document.getElementById('le-nav-float');
  const wraps = [...document.querySelectorAll('#le-lesson-body .tc-wrap.tc-change')];
  leEditWraps = wraps;
  leCurrentEditIdx = -1;
  if (wraps.length === 0) {{
    navFloat.style.display = 'none';
    return;
  }}
  navFloat.style.display = 'flex';
  document.getElementById('le-nav-counter').textContent = '0 / ' + wraps.length;
  document.getElementById('le-prev-edit-btn').disabled = true;
  document.getElementById('le-next-edit-btn').disabled = false;
}}

function leNextEdit() {{
  leEditWraps = [...document.querySelectorAll('#le-lesson-body .tc-wrap.tc-change')];
  if (!leEditWraps.length) return;
  leCurrentEditIdx = Math.min(leCurrentEditIdx + 1, leEditWraps.length - 1);
  leScrollToCurrentEdit();
}}

function lePrevEdit() {{
  leEditWraps = [...document.querySelectorAll('#le-lesson-body .tc-wrap.tc-change')];
  if (!leEditWraps.length) return;
  leCurrentEditIdx = Math.max(leCurrentEditIdx - 1, 0);
  leScrollToCurrentEdit();
}}

function leScrollToCurrentEdit() {{
  if (leCurrentEditIdx < 0 || leCurrentEditIdx >= leEditWraps.length) return;
  const wrap = leEditWraps[leCurrentEditIdx];
  wrap.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
  wrap.style.outline = '2px solid #f59e0b';
  wrap.style.borderRadius = '3px';
  setTimeout(() => {{ wrap.style.outline = ''; wrap.style.borderRadius = ''; }}, 1500);
  document.getElementById('le-nav-counter').textContent = (leCurrentEditIdx + 1) + ' / ' + leEditWraps.length;
  document.getElementById('le-prev-edit-btn').disabled = leCurrentEditIdx === 0;
  document.getElementById('le-next-edit-btn').disabled = leCurrentEditIdx === leEditWraps.length - 1;
}}

// JS-driven hover with delay to prevent popup disappearing when moving mouse to it
function leBindPopups() {{
  document.querySelectorAll('#le-lesson-body .tc-wrap').forEach(wrap => {{
    const popup = wrap.querySelector('.tc-popup');
    if (!popup) return;
    let hideTimer = null;  // per-popup timer so neighbouring popups don't interfere (issue 63)
    wrap.addEventListener('mouseenter', () => {{
      // Dismiss all other visible popups (issue 63)
      document.querySelectorAll('#le-lesson-body .tc-popup-visible').forEach(p => {{
        if (p !== popup) p.classList.remove('tc-popup-visible');
      }});
      clearTimeout(hideTimer);
      popup.classList.add('tc-popup-visible');
    }});
    wrap.addEventListener('mouseleave', () => {{
      hideTimer = setTimeout(() => popup.classList.remove('tc-popup-visible'), 300);
    }});
    popup.addEventListener('mouseenter', () => {{ clearTimeout(hideTimer); }});
    popup.addEventListener('mouseleave', () => {{
      hideTimer = setTimeout(() => popup.classList.remove('tc-popup-visible'), 300);
    }});
  }});
}}

function leUndo() {{
  if (!leUndoStack.length) return;
  const entry = leUndoStack.pop();
  const wrap = document.querySelector(`.tc-wrap[data-id="${{entry.changeId}}"]`);
  if (wrap) {{
    leRedoStack.push({{ changeId: entry.changeId, prev: wrap.dataset.state }});
    leApplyState(wrap, entry.prev);
  }}
  leUpdateHistoryBtns();
  leScheduleAutosave(leCurrentLessonDir());
}}

function leRedo() {{
  if (!leRedoStack.length) return;
  const entry = leRedoStack.pop();
  const wrap = document.querySelector(`.tc-wrap[data-id="${{entry.changeId}}"]`);
  if (wrap) {{
    leUndoStack.push({{ changeId: entry.changeId, prev: wrap.dataset.state }});
    leApplyState(wrap, entry.prev);
  }}
  leUpdateHistoryBtns();
  leScheduleAutosave(leCurrentLessonDir());
}}

function leUpdateHistoryBtns() {{
  document.getElementById('le-undo-btn').disabled = leUndoStack.length === 0;
  document.getElementById('le-redo-btn').disabled = leRedoStack.length === 0;
}}

// Extract clean lesson HTML from current tc-wrap state.
// Returns {{ html, plan }} or null if no lesson is selected.
function leGetCleanHtml() {{
  const lessonId = document.getElementById('le-lesson-filter').value;
  if (!lessonId) return null;
  const plan = leEditPlans.find(l => l.lesson_id === lessonId);
  if (!plan) return null;

  const body = document.getElementById('le-lesson-body').cloneNode(true);

  // Remove popups and any orphaned popup descendants (KNOW-2255: when a wrap
  // was rendered inside an <a>, the HTML parser re-parents the popup's
  // <button>s and inner <a>s out of .tc-popup, so a single .tc-popup selector
  // misses them).
  body.querySelectorAll(
    '.tc-popup, .tc-btns, .tc-explanation, .tc-issue-links, ' +
    '.tc-accept, .tc-reject, .card-link, .card-link-wrap, .rec-id'
  ).forEach(n => n.remove());
  body.querySelectorAll('a[href^="?tab=recommendations"]').forEach(n => n.remove());
  body.querySelectorAll('.tc-wrap[data-type="screenshot"]').forEach(wrap => wrap.remove());

  // Apply accepted alt text updates to matching <img> tags, then remove the wraps
  body.querySelectorAll('.tc-wrap[data-type="alt-text"]').forEach(wrap => {{
    if (wrap.dataset.state === 'accepted') {{
      const src = wrap.dataset.src || '';
      const suggestedAlt = wrap.dataset.suggAlt || '';
      if (src && suggestedAlt) {{
        const img = body.querySelector(`img[src="${{src}}"], img[src$="${{src}}"]`);
        if (img) img.setAttribute('alt', suggestedAlt);
      }}
    }}
    wrap.remove();
  }});

  // Resolve each text tc-wrap based on state (pending = keep original).
  // data-orig is the full original HTML (may include <a>) so a rejected
  // wrap can restore its link verbatim. Insert as HTML, not as a text node.
  body.querySelectorAll('.tc-wrap').forEach(wrap => {{
    const state = wrap.dataset.state || 'pending';
    const type = wrap.dataset.type;
    const orig = wrap.dataset.orig || '';
    const sugg = wrap.dataset.sugg || '';
    let replacement = '';
    if (state === 'accepted') replacement = (type === 'delete') ? '' : (type === 'add') ? orig + sugg : sugg;
    else replacement = orig;
    wrap.insertAdjacentHTML('beforebegin', replacement);
    wrap.remove();
  }});

  // Strip the ../lesson_dir/ image prefix added by leRenderLesson
  const lessonBase = '../' + (plan.lesson_dir || '').split('/').map(s => encodeURIComponent(s)).join('/') + '/';
  // KNOW-2274: a contenteditable edit can serialise that relative src into an
  // absolute URL against the page origin (e.g. http://localhost:8080/<dir>/images/x.png).
  // Strip the origin + lesson_dir prefix back to a relative images/<file> too.
  const absBase = window.location.origin + '/' + (plan.lesson_dir || '').split('/').map(s => encodeURIComponent(s)).join('/') + '/';
  body.querySelectorAll('img[src]').forEach(img => {{
    const attrSrc = img.getAttribute('src') || '';
    if (attrSrc.startsWith(lessonBase)) img.setAttribute('src', attrSrc.slice(lessonBase.length));
    else if (attrSrc.startsWith(absBase)) img.setAttribute('src', attrSrc.slice(absBase.length));
  }});

  // KNOW-2279: don't leak the popover-selection class into saved HTML
  body.querySelectorAll('img.le-img-selected').forEach(img => {{
    img.classList.remove('le-img-selected');
    if (!img.getAttribute('class')) img.removeAttribute('class');
  }});

  // KNOW-2279: don't leak the popover-selection class into saved HTML
  body.querySelectorAll('img.le-img-selected').forEach(img => {{
    img.classList.remove('le-img-selected');
    if (!img.getAttribute('class')) img.removeAttribute('class');
  }});

  return {{ html: body.innerHTML, plan }};
}}

function leSave() {{
  const result = leGetCleanHtml();
  if (!result) return;
  const {{ html: cleanHtml, plan }} = result;
  const hasDataUris = /<img[^>]+src=["']data:/i.test(cleanHtml);

  leShowMessage(null, 'success', {{ html: hasDataUris
    ? 'Saving — uploading pasted images, this can take a few seconds…'
    : 'Saving…' }});

  fetch('/api/save-lesson', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{ lesson_dir: plan.lesson_dir || '', to_version: TO_VERSION, html_content: cleanHtml }}),
  }})
  .then(async r => {{
    if (r.status === 409) {{
      const data = await r.json();
      if (confirm(`File already exists at:\\n${{data.target_path}}\\n\\nOverwrite?`)) {{
        return fetch('/api/save-lesson', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ lesson_dir: plan.lesson_dir || '', to_version: TO_VERSION, html_content: cleanHtml, force: true }}),
        }}).then(r2 => r2.json());
      }}
      return null;
    }}
    if (!r.ok) {{
      let serverMsg = 'HTTP ' + r.status;
      try {{ const data = await r.json(); if (data && data.error) serverMsg = data.error; }} catch (_) {{}}
      const err = new Error(serverMsg);
      err.serverError = true;
      throw err;
    }}
    return r.json();
  }})
  .then(result => {{
    if (!result) return;
    leShowMessage(null, 'success', {{ html: '✓ Saved to: <code>' + escHtml(result.target_path) + '</code>' }});
    // KNOW-2277: tell FastAPI we just pushed a durable snapshot, so the
    // Drafts page surfaces this lesson with a "saved" badge. Best-effort —
    // the version-folder file write is the source of truth either way.
    fetch(APP_BASE + '/api/runs/' + encodeURIComponent(RUN_ID) + '/report-drafts/mark-saved', {{
      method: 'POST',
      headers: {{ 'Content-Type': 'application/json' }},
      body: JSON.stringify({{
        lesson_dir: plan.lesson_dir || '',
        saved_to_version_path: result.target_path,
      }}),
    }}).then(r => r.ok ? r.json() : null).then(data => {{
      const lessonDir = plan.lesson_dir || '';
      if (data && lessonDir) {{
        leDrafts[lessonDir] = Object.assign({{}}, leDrafts[lessonDir] || {{}}, {{
          saved_to_version_at: data.saved_to_version_at,
          saved_to_version_path: data.saved_to_version_path,
        }});
      }}
    }}).catch(err => console.warn('mark-saved failed:', err));
  }})
  .catch(err => {{
    if (err && err.serverError) {{
      leShowMessage(null, 'error', {{ html: '⚠ Save failed: ' + escHtml(err.message) }});
      return;
    }}
    const blob = new Blob([cleanHtml], {{ type: 'text/html;charset=utf-8' }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'index.html'; a.click();
    URL.revokeObjectURL(url);
    leShowMessage(null, 'success', {{ html: 'Downloaded index.html — place it at: <code>' + escHtml(plan.lesson_dir || '') + '/index.html</code>. For direct saving, use <code>python serve.py</code>.' }});
  }});
}}


// WYSIWYG formatting helpers
function leFormat(cmd) {{
  document.getElementById('le-lesson-body').focus();
  document.execCommand(cmd, false, null);
}}

function leFormatBlock(tag) {{
  const editor = document.getElementById('le-lesson-body');
  editor.focus();
  const sel = window.getSelection();
  if (!sel.rangeCount) return;
  const range = sel.getRangeAt(0);
  // Find the block-level ancestor inside the editor
  let node = range.commonAncestorContainer;
  if (node.nodeType === Node.TEXT_NODE) node = node.parentElement;
  while (node && node !== editor && !['P','DIV','H1','H2','H3','H4','H5','H6','LI'].includes(node.tagName)) {{
    node = node.parentElement;
  }}
  if (node && node !== editor && node.tagName.toLowerCase() === tag) {{
    // Toggle off: replace heading with a plain paragraph
    const p = document.createElement('p');
    p.innerHTML = node.innerHTML;
    node.replaceWith(p);
  }} else {{
    document.execCommand('formatBlock', false, tag);
  }}
}}

function leInsertLink() {{
  const editor = document.getElementById('le-lesson-body');
  editor.focus();
  const sel = window.getSelection();
  const selectedText = sel.toString();
  const url = prompt('Enter URL:', 'https://');
  if (!url) return;
  if (selectedText) {{
    document.execCommand('createLink', false, url);
  }} else {{
    const text = prompt('Enter link text:', url);
    if (text === null) return;
    const a = `<a href="${{url}}">${{text || url}}</a>`;
    document.execCommand('insertHTML', false, a);
  }}
}}

// KNOW-2279: edit alt text and replace image source via floating popover.
function leOnImageClick(e) {{
  const img = e.target.closest && e.target.closest('img');
  if (!img) return;
  if (!document.getElementById('le-lesson-body').contains(img)) return;
  e.preventDefault();
  leOpenImgPopover(img);
}}

function leOpenImgPopover(img) {{
  document.querySelectorAll('#le-lesson-body img.le-img-selected').forEach(el => {{
    el.classList.remove('le-img-selected');
  }});
  img.classList.add('le-img-selected');
  leSelectedImage = img;

  const pop = document.getElementById('le-img-popover');
  // Restore edit-mode UI (it may have last been opened in insert mode).
  pop.classList.remove('le-insert-mode');
  document.getElementById('le-img-alt-label').style.display = '';
  document.getElementById('le-img-alt').style.display = '';
  document.getElementById('le-img-save-btn').style.display = '';
  document.getElementById('le-img-replace-btn').textContent = 'Replace ▾';
  document.getElementById('le-img-alt').value = img.getAttribute('alt') || '';
  document.getElementById('le-img-replace-menu').classList.remove('open');

  // Anchor the popover below the image, clamped horizontally to the viewport.
  const r = img.getBoundingClientRect();
  const top = window.scrollY + r.bottom + 6;
  const left = window.scrollX + Math.max(8, Math.min(r.left, window.innerWidth - 340));
  pop.style.top = top + 'px';
  pop.style.left = left + 'px';
  pop.classList.add('visible');
  document.getElementById('le-img-alt').focus();
}}

function leImgClosePopover() {{
  document.getElementById('le-img-popover').classList.remove('visible');
  document.getElementById('le-img-replace-menu').classList.remove('open');
  if (leSelectedImage) leSelectedImage.classList.remove('le-img-selected');
  leSelectedImage = null;
}}

function leImgSave() {{
  if (!leSelectedImage) {{
    // Alt-text edit needs a real target; insert is handled by the Replace menu.
    leImgClosePopover();
    leShowMessage('Select an image first.', 'error', {{ autoHide: 2500 }});
    return;
  }}
  const alt = document.getElementById('le-img-alt').value;
  leSelectedImage.setAttribute('alt', alt);
  leImgClosePopover();
  // setAttribute does not fire 'input' on the editor — trigger autosave explicitly.
  leScheduleAutosave(leCurrentLessonDir());
}}

function leImgToggleReplaceMenu() {{
  document.getElementById('le-img-replace-menu').classList.toggle('open');
}}

// KNOW-2279: drop any per-image dimensions so a replaced/inserted image shows at
// its natural size. The editor's max-width:100% is display-only and is never
// written to the saved HTML, so Skilljar controls the final width.
function leImgStripDimensions(img) {{
  if (!img) return;
  img.removeAttribute('width');
  img.removeAttribute('height');
  if (img.style) {{
    img.style.removeProperty('width');
    img.style.removeProperty('height');
    img.style.removeProperty('max-width');
    img.style.removeProperty('min-width');
    img.style.removeProperty('aspect-ratio');
  }}
  if (img.getAttribute('style') === '') img.removeAttribute('style');
}}

// KNOW-2279: insert a node at the caret when it's inside the editor, else append.
function leImgInsertAtCaret(node) {{
  const editor = document.getElementById('le-lesson-body');
  const sel = window.getSelection();
  let range = null;
  if (sel && sel.rangeCount) {{
    const r = sel.getRangeAt(0);
    if (editor.contains(r.commonAncestorContainer)) range = r;
  }}
  if (range) {{
    range.deleteContents();
    range.insertNode(node);
    range.setStartAfter(node);
    range.collapse(true);
    sel.removeAllRanges();
    sel.addRange(range);
  }} else {{
    editor.appendChild(node);
  }}
}}

// KNOW-2279: single funnel for paste/upload — replace the target's src (stripping
// its dimensions) in replace mode, or insert a fresh <img> in insert mode (also
// covers a replace target that has since left the DOM).
function leImgApplyDataUri(dataUri, target, mode) {{
  const editor = document.getElementById('le-lesson-body');
  if (mode === 'replace' && target && editor.contains(target)) {{
    target.setAttribute('src', dataUri);
    leImgStripDimensions(target);
  }} else {{
    const img = document.createElement('img');
    img.setAttribute('src', dataUri);
    img.setAttribute('alt', '');
    leImgInsertAtCaret(img);
  }}
  leImgClosePopover();
  leShowMessage(mode === 'replace' ? 'Image replaced.' : 'Image inserted.', 'success', {{ autoHide: 2500 }});
  // Programmatic DOM changes don't fire the editor 'input' listener.
  leScheduleAutosave(leCurrentLessonDir());
}}

async function leImgReplaceFromClipboard() {{
  // Capture the target now: a null target means "insert a new image".
  const target = leSelectedImage;
  const mode = target ? 'replace' : 'insert';
  document.getElementById('le-img-replace-menu').classList.remove('open');
  if (!navigator.clipboard || !navigator.clipboard.read) {{
    leShowMessage('Clipboard API unavailable here (needs HTTPS or localhost).', 'error', {{ autoHide: 4000 }});
    return;
  }}
  try {{
    const items = await navigator.clipboard.read();
    for (const item of items) {{
      const type = item.types.find(t => t.startsWith('image/'));
      if (!type) continue;
      const blob = await item.getType(type);
      const dataUri = await new Promise((res, rej) => {{
        const fr = new FileReader();
        fr.onload = () => res(fr.result);
        fr.onerror = () => rej(fr.error);
        fr.readAsDataURL(blob);
      }});
      leImgApplyDataUri(dataUri, target, mode);
      return;
    }}
    leShowMessage('No image on the clipboard. Copy an image first, then try again.', 'error', {{ autoHide: 4000 }});
  }} catch (ex) {{
    leShowMessage('Clipboard read failed: ' + (ex && ex.message ? ex.message : ex), 'error', {{ autoHide: 4000 }});
  }}
}}

function leImgReplaceFromFile() {{
  // Capture the target BEFORE opening the dialog — opening it clears the
  // selection/popover, so leSelectedImage can't be trusted in the change handler.
  leImgPendingTarget = leSelectedImage;
  leImgPendingMode = leSelectedImage ? 'replace' : 'insert';
  document.getElementById('le-img-replace-menu').classList.remove('open');
  document.getElementById('le-img-file-input').click();
}}

function leImgOnFileChosen(e) {{
  const file = e.target.files && e.target.files[0];
  const target = leImgPendingTarget;
  const mode = leImgPendingMode || 'insert';
  leImgPendingTarget = null;
  leImgPendingMode = null;
  e.target.value = ''; // allow re-picking the same file later
  if (!file) return; // dialog cancelled — nothing to report
  if (!file.type || !file.type.startsWith('image/')) {{
    leShowMessage('Please choose an image file.', 'error', {{ autoHide: 3000 }});
    return;
  }}
  const fr = new FileReader();
  fr.onload = () => leImgApplyDataUri(fr.result, target, mode);
  fr.onerror = () => leShowMessage('Could not read file.', 'error', {{ autoHide: 3000 }});
  fr.readAsDataURL(file);
}}

// KNOW-2279: open the popover in "insert" mode (no image selected) — only the
// Insert (paste/upload) actions apply; alt-text editing needs a real target.
function leOpenImgPopoverForInsert() {{
  document.querySelectorAll('#le-lesson-body img.le-img-selected').forEach(el => {{
    el.classList.remove('le-img-selected');
  }});
  leSelectedImage = null;
  const pop = document.getElementById('le-img-popover');
  pop.classList.add('le-insert-mode');
  document.getElementById('le-img-alt-label').style.display = 'none';
  document.getElementById('le-img-alt').style.display = 'none';
  document.getElementById('le-img-save-btn').style.display = 'none';
  document.getElementById('le-img-replace-btn').textContent = 'Insert ▾';
  document.getElementById('le-img-replace-menu').classList.remove('open');

  // Anchor near the caret if it's in the editor, otherwise near the toolbar.
  const editor = document.getElementById('le-lesson-body');
  const sel = window.getSelection();
  let rect = null;
  if (sel && sel.rangeCount && editor.contains(sel.getRangeAt(0).commonAncestorContainer)) {{
    rect = sel.getRangeAt(0).getBoundingClientRect();
  }}
  if (!rect || (rect.top === 0 && rect.left === 0 && rect.width === 0)) {{
    rect = document.getElementById('le-toolbar').getBoundingClientRect();
  }}
  pop.style.top = (window.scrollY + rect.bottom + 6) + 'px';
  pop.style.left = (window.scrollX + Math.max(8, Math.min(rect.left, window.innerWidth - 340))) + 'px';
  pop.classList.add('visible');
}}

function leEditImage(ev) {{
  // Stop this click from reaching the document outside-click handler, which
  // would otherwise immediately close the popover we're about to open.
  if (ev && ev.stopPropagation) ev.stopPropagation();
  // Prefer the explicitly-selected image; fall back to one found in the current selection.
  const editor = document.getElementById('le-lesson-body');
  if (leSelectedImage && editor.contains(leSelectedImage)) {{
    leOpenImgPopover(leSelectedImage);
    return;
  }}
  const sel = window.getSelection();
  if (sel && sel.rangeCount) {{
    const c = sel.getRangeAt(0).commonAncestorContainer;
    const root = (c.nodeType === 1 ? c : c.parentElement);
    const img = root && root.querySelector && root.querySelector('img');
    if (img && editor.contains(img)) {{
      leOpenImgPopover(img);
      return;
    }}
  }}
  // Nothing selected → open in insert mode so paste/upload add a NEW image.
  leOpenImgPopoverForInsert();
}}

// KNOW-2275: bullet / numbered list support.
// Uses document.execCommand('insertUnorderedList' | 'insertOrderedList') —
// the browser handles toggle-off natively and wraps block ancestors only,
// so contenteditable=false track-change spans (.tc-wrap) survive intact.
function leFormatList(kind) {{
  const editor = document.getElementById('le-lesson-body');
  editor.focus();
  const cmd = (kind === 'ol') ? 'insertOrderedList' : 'insertUnorderedList';
  document.execCommand(cmd, false, null);
}}

// Find the nearest <li> ancestor of a node, bounded by the editor root.
function leFindLiAncestor(node, editor) {{
  let n = node;
  if (n && n.nodeType === Node.TEXT_NODE) n = n.parentElement;
  while (n && n !== editor) {{
    if (n.tagName === 'LI') return n;
    n = n.parentElement;
  }}
  return null;
}}

// Find the nearest block-level ancestor of a node, bounded by the editor root.
function leFindBlockAncestor(node, editor) {{
  const BLOCKS = ['P','DIV','LI','H1','H2','H3','H4','H5','H6','BLOCKQUOTE','PRE'];
  let n = node;
  if (n && n.nodeType === Node.TEXT_NODE) n = n.parentElement;
  while (n && n !== editor) {{
    if (BLOCKS.includes(n.tagName)) return n;
    n = n.parentElement;
  }}
  return null;
}}

// KNOW-2275: keyboard handler — shortcuts, Tab nesting, Markdown auto-conversion.
function leHandleListKeydown(e) {{
  const editor = document.getElementById('le-lesson-body');
  // Branch 1: Ctrl/Cmd+Shift+8 / 7 shortcuts.
  if ((e.ctrlKey || e.metaKey) && e.shiftKey) {{
    if (e.code === 'Digit8') {{
      e.preventDefault();
      leFormatList('ul');
      return;
    }}
    if (e.code === 'Digit7') {{
      e.preventDefault();
      leFormatList('ol');
      return;
    }}
  }}
  const sel = window.getSelection();
  if (!sel.rangeCount) return;
  const range = sel.getRangeAt(0);
  // Branch 2: Tab / Shift+Tab inside an <li> indents/outdents.
  if (e.key === 'Tab') {{
    const li = leFindLiAncestor(range.startContainer, editor);
    if (!li) return;
    e.preventDefault();
    if (e.shiftKey) {{
      // Only outdent when the <li>'s grandparent is another list, i.e.
      // the item is genuinely nested. Calling execCommand('outdent') on
      // a top-level <li> in Chrome SILENTLY UNWRAPS it from its <ul>/<ol>
      // and replaces it with a plain block — destroying the list and
      // any attached track-change wrappers. Bail out instead.
      const parentList = li.parentElement;
      const grandparent = parentList ? parentList.parentElement : null;
      const isNested = grandparent && (
        grandparent.tagName === 'UL' || grandparent.tagName === 'OL' ||
        grandparent.tagName === 'LI'
      );
      if (!isNested) return;
      document.execCommand('outdent', false, null);
    }} else {{
      document.execCommand('indent', false, null);
    }}
    return;
  }}
  // Branch 3: Markdown auto-conversion on Space.
  // Pattern source: /^[-*]$/ for UL, /^\\d+\\.$/ for OL.
  if (e.key === ' ' && !e.ctrlKey && !e.metaKey && !e.altKey) {{
    const block = leFindBlockAncestor(range.startContainer, editor);
    if (!block || block.tagName === 'LI') return;
    // don't auto-convert blocks containing track-change spans —
    // block.textContent would include their text, fooling the
    // entire-block-content guard, and probe.deleteContents() could
    // destroy the pill's data-* attributes.
    if (block.querySelector('.tc-wrap')) return;
    // Build a range from the start of the block to the caret.
    const probe = document.createRange();
    probe.setStart(block, 0);
    probe.setEnd(range.startContainer, range.startOffset);
    const prefixText = probe.toString();
    // Only fire when the matched text is the entire content of the block —
    // avoid hijacking "- " mid-sentence.
    const blockText = block.textContent || '';
    if (prefixText !== blockText) return;
    let kind = null;
    if (/^[-*]$/.test(prefixText)) kind = 'ul';
    else if (/^\\d+\\.$/.test(prefixText)) kind = 'ol';
    if (!kind) return;
    e.preventDefault();
    // Delete the matched prefix. The prefixText === blockText guard above
    // guarantees the prefix WAS the block's entire content, so it is now empty.
    probe.deleteContents();
    // KNOW-2275 (QA issue 2): build the single-item list directly instead of
    // calling execCommand('insertUnorderedList') on the now-empty block. On an
    // empty block Chrome absorbs the FOLLOWING sibling block (the paragraph
    // below) into the new list. Replacing only this block starts the bullet on
    // its own line and leaves the paragraph below untouched.
    const listEl = document.createElement(kind === 'ol' ? 'ol' : 'ul');
    const li = document.createElement('li');
    li.appendChild(document.createElement('br'));
    listEl.appendChild(li);
    block.parentNode.replaceChild(listEl, block);
    const caret = document.createRange();
    caret.setStart(li, 0);
    caret.collapse(true);
    sel.removeAllRanges();
    sel.addRange(caret);
  }}
}}

</script>
</body>
</html>"""
