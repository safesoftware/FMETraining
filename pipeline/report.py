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
from datetime import datetime, timezone
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
    )

    out_path = report_path(run_id, output_dir)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Report written: {out_path.name}")
    print(f"  To view: python serve.py  (run from project root, enables Save feature)")
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
.edit-toolbar {{ display: flex; gap: 8px; align-items: center; padding: 8px 24px; background: #f8fafc; border-bottom: 1px solid #e5e7eb; }}
.edit-toolbar button {{ padding: 5px 12px; border: 1px solid #ccc; border-radius: 4px; background: #fff; cursor: pointer; font-size: 0.82rem; }}
.edit-toolbar button:disabled {{ opacity: 0.4; cursor: not-allowed; }}
.edit-toolbar .save-btn {{ background: #1a3d6b; color: #fff; border-color: #1a3d6b; font-weight: 600; }}
.edit-toolbar .save-btn:hover {{ background: #1e4d8c; }}
.save-banner {{ display: none; background: #f0fdf4; border: 1px solid #86efac; color: #15803d; padding: 10px 16px; margin: 12px 24px; border-radius: 6px; font-size: 0.85rem; }}
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
  <div class="edit-toolbar" id="le-toolbar" style="display:none">
    <button onclick="leUndo()" id="le-undo-btn" disabled>← Undo</button>
    <button onclick="leRedo()" id="le-redo-btn" disabled>Redo →</button>
    <button class="save-btn" onclick="leSave()">Save to Version Folder</button>
  </div>
  <div class="save-banner" id="le-save-banner"></div>
  <div id="le-lesson-body" class="lesson-edit-body">
    <div class="lesson-edit-empty">Select a lesson above to view suggested edits.</div>
  </div>
</div><!-- end tab-lesson-edits -->

<!-- Floating next/prev edit nav — visible only when Lesson Edits tab is active and a lesson is loaded (issue 47) -->
<div class="le-nav-float" id="le-nav-float">
  <div class="le-nav-counter" id="le-nav-counter">0 / 0</div>
  <button class="le-nav-btn" id="le-prev-edit-btn" onclick="lePrevEdit()" disabled>↑ Prev Edit</button>
  <button class="le-nav-btn" id="le-next-edit-btn" onclick="leNextEdit()" disabled>↓ Next Edit</button>
</div>

<script>
const JSON_FILE = '{json_filename}';
const EDIT_PLANS_FILE = '{edit_plans_filename}';
const JIRA_BASE_URL = '{jira_base_url}';
const TO_VERSION = '{to_version}';
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
let leRejectedIssueKeys = new Set(); // tracks keys rejected from Recommendations tab (issue 30)

// Eager-load edit plans on page load (needed for cross-tab features in issues 37, 30)
if (EDIT_PLANS_FILE) {{
  fetch(EDIT_PLANS_FILE)
    .then(r => r.json())
    .then(data => {{
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
  document.getElementById('le-lesson-body').innerHTML =
    '<div class="lesson-edit-empty">Select a lesson above to view suggested edits.</div>';
  document.getElementById('le-change-count').textContent = '';
  document.getElementById('le-toolbar').style.display = 'none';
  document.getElementById('le-nav-float').style.display = 'none';
}}

function leRenderLesson() {{
  const lessonId = document.getElementById('le-lesson-filter').value;
  if (!lessonId) return;
  const plan = leEditPlans.find(l => l.lesson_id === lessonId);
  if (!plan) return;

  leUndoStack = [];
  leRedoStack = [];
  leUpdateHistoryBtns();

  const changes = plan.changes || [];
  const screenshots = plan.screenshot_updates || [];
  const totalChanges = changes.length + screenshots.length;

  document.getElementById('le-change-count').textContent =
    totalChanges > 0 ? `${{changes.length}} text change${{changes.length !== 1 ? 's' : ''}}, ${{screenshots.length}} screenshot note${{screenshots.length !== 1 ? 's' : ''}}` : 'No changes suggested';
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
      ? `<span style="display:block;font-size:0.7rem;margin-top:2px"><a href="?tab=recommendations&card=${{encodeURIComponent(allData.find(a=>a.issue_key===keys[0])?.rec_id||'')}}&from_change=${{encodeURIComponent(changeId)}}" onclick="leNavigateToCard(event,'${{keys[0]}}','${{lessonId||''}}','${{changeId}}');return false;" style="color:#93c5fd">↗ View recommendation card (${{keys[0]}})</a></span>`
      : '';
    // Issue 51/66: copy-chip for linking directly to this change
    const copyChip = (lessonId && type !== 'screenshot')
      ? `<span class="rec-id" onclick="navigator.clipboard.writeText(location.origin+location.pathname+'?tab=lesson-edits&lesson='+encodeURIComponent('${{lessonId}}')+'&change='+encodeURIComponent('${{changeId}}'))" title="Copy link to this change" style="margin-left:4px">#${{changeId.slice(0,8)}}</span>`
      : '';
    // Issue 28: reject-all button for first issue key (text changes only)
    const rejectAllBtn = (keys.length && type !== 'screenshot')
      ? `<button class="tc-reject" style="font-size:0.68rem" onclick="leRejectAllForIssueKey('${{keys[0]}}');setStatus(allData.find(a=>a.issue_key==='${{keys[0]}}')?.rec_id||'','incorrect');event.stopPropagation()">✗✗ Reject all for ${{keys[0]}}</button>`
      : '';
    return `<span class="tc-popup" data-popup="${{changeId}}"><span class="tc-btns"><button class="tc-accept" onclick="leAccept('${{changeId}}',event)">✓ Accept</button><button class="tc-reject" onclick="leReject('${{changeId}}',event)">✗ Reject</button>${{rejectAllBtn}}</span><span class="tc-explanation">${{escHtml(explanation || '')}}</span><span class="tc-issue-links">${{issueLinks}}${{copyChip}}${{cardLink}}</span></span>`;
  }}

  // Apply text changes
  changes.forEach((ch, idx) => {{
    const orig = ch.original_text || '';
    if (!orig) return;
    const popup = makePopup(ch.change_id, ch.explanation, ch.issue_keys, ch.type, plan.lesson_id);
    const issueKeysAttr = escHtml((ch.issue_keys || []).join(','));

    let markup;
    if (ch.type === 'delete') {{
      markup = `<span id="le-change-${{ch.change_id}}" class="tc-wrap tc-change" data-id="${{ch.change_id}}" data-orig="${{escHtml(orig)}}" data-sugg="" data-type="delete" data-issue-keys="${{issueKeysAttr}}" data-state="pending"><del class="tc-del">${{escHtml(orig)}}</del>${{popup}}</span>`;
    }} else if (ch.type === 'add') {{
      markup = `<span id="le-change-${{ch.change_id}}" class="tc-wrap tc-change" data-id="${{ch.change_id}}" data-orig="${{escHtml(orig)}}" data-sugg="${{escHtml(ch.suggested_text || '')}}" data-type="add" data-issue-keys="${{issueKeysAttr}}" data-state="pending"><span class="tc-orig-context">${{escHtml(orig)}}</span><ins class="tc-add">${{escHtml(ch.suggested_text || '')}}</ins>${{popup}}</span>`;
    }} else {{
      markup = `<span id="le-change-${{ch.change_id}}" class="tc-wrap tc-change" data-id="${{ch.change_id}}" data-orig="${{escHtml(orig)}}" data-sugg="${{escHtml(ch.suggested_text || '')}}" data-type="change" data-issue-keys="${{issueKeysAttr}}" data-state="pending"><del class="tc-del">${{escHtml(orig)}}</del><ins class="tc-ins"> ${{escHtml(ch.suggested_text || '')}}</ins>${{popup}}</span>`;
    }}

    html = html.replace(orig, markup);
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
    const noteInner = `<div class="screenshot-note"><strong>📷 Screenshot update needed (${{issueLinks}})</strong>${{escHtml(su.explanation || '')}}${{altTextLine}}</div>`;
    const popup = makePopup(ssId, su.explanation, su.issue_keys, 'screenshot', plan.lesson_id);
    const wrapped = `<div class="tc-wrap tc-change" data-id="${{ssId}}" data-type="screenshot" data-issue-keys="${{escHtml((su.issue_keys||[]).join(','))}}" data-state="pending">${{noteInner}}${{popup}}</div>`;
    const imgPattern = new RegExp(`(<img[^>]*src="${{su.src.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&')}}"[^>]*>)`, 'i');
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
  leUpdateNavFloat();
  // Issue 30: apply any rejections that were triggered from the Recommendations tab
  if (leRejectedIssueKeys.size) {{
    document.querySelectorAll('#le-lesson-body .tc-wrap[data-issue-keys]').forEach(wrap => {{
      const keys = (wrap.dataset.issueKeys || '').split(',').map(s => s.trim());
      if (keys.some(k => leRejectedIssueKeys.has(k)) && wrap.dataset.state !== 'rejected') {{
        leApplyState(wrap, 'rejected');
      }}
    }});
  }}
}}

// Phase 2: accept/reject
function leAccept(changeId, evt) {{
  if (evt) evt.stopPropagation();
  const wrap = document.querySelector(`.tc-wrap[data-id="${{changeId}}"]`);
  if (!wrap) return;
  const prev = wrap.dataset.state;
  leUndoStack.push({{ changeId, prev }});
  leRedoStack = [];
  leApplyState(wrap, 'accepted');
  leUpdateHistoryBtns();
  // Hide popup after action
  const popup = wrap.querySelector('.tc-popup');
  if (popup) popup.classList.remove('tc-popup-visible');
}}

function leReject(changeId, evt) {{
  if (evt) evt.stopPropagation();
  const wrap = document.querySelector(`.tc-wrap[data-id="${{changeId}}"]`);
  if (!wrap) return;
  const prev = wrap.dataset.state;
  leUndoStack.push({{ changeId, prev }});
  leRedoStack = [];
  leApplyState(wrap, 'rejected');
  leUpdateHistoryBtns();
  // Hide popup after action
  const popup = wrap.querySelector('.tc-popup');
  if (popup) popup.classList.remove('tc-popup-visible');
}}

function leApplyState(wrap, state) {{
  wrap.dataset.state = state;
  const type = wrap.dataset.type;
  const orig = wrap.dataset.orig || '';
  const sugg = wrap.dataset.sugg || '';

  // Screenshot type: just update the note's CSS class
  if (type === 'screenshot') {{
    const note = wrap.querySelector('.screenshot-note');
    if (note) {{
      note.className = 'screenshot-note' +
        (state === 'accepted' ? ' screenshot-note-accepted' : state === 'rejected' ? ' screenshot-note-rejected' : '');
    }}
    return;
  }}

  // Remove existing content nodes (del/ins/orig) — keep popup and itself
  [...wrap.querySelectorAll('del.tc-del, ins.tc-ins, ins.tc-add, span.tc-orig')].forEach(n => n.remove());

  if (state === 'pending') {{
    if (type === 'delete') wrap.insertAdjacentHTML('afterbegin', `<del class="tc-del">${{orig}}</del>`);
    else if (type === 'add') wrap.insertAdjacentHTML('afterbegin', `<span class="tc-orig-context">${{orig}}</span><ins class="tc-add">${{sugg}}</ins>`);
    else wrap.insertAdjacentHTML('afterbegin', `<del class="tc-del">${{orig}}</del><ins class="tc-ins"> ${{sugg}}</ins>`);
  }} else if (state === 'accepted') {{
    if (type === 'delete') {{ /* nothing — text removed */ }}
    else if (type === 'add') wrap.insertAdjacentHTML('afterbegin', `<span class="tc-orig-context">${{orig}}</span><ins class="tc-ins">${{sugg}}</ins>`);
    else wrap.insertAdjacentHTML('afterbegin', `<ins class="tc-ins">${{sugg}}</ins>`);
  }} else {{ // rejected
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
}}

// Issues 29/67/68: scroll to a card by rec_id, handle pagination, highlight originating change
function leShowCard(recId, fromChangeId) {{
  const tabBtn = document.querySelector('.tab-btn[onclick*="recommendations"]');
  if (tabBtn) switchTab('recommendations', tabBtn);
  // Navigate to the correct page (issue 67)
  const idx = filteredData.findIndex(a => a.rec_id === recId);
  if (idx >= 0) {{
    const targetPage = Math.floor(idx / PAGE_SIZE) + 1;
    if (currentPage !== targetPage) {{ currentPage = targetPage; renderCards(); }}
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
}}

function leUpdateHistoryBtns() {{
  document.getElementById('le-undo-btn').disabled = leUndoStack.length === 0;
  document.getElementById('le-redo-btn').disabled = leRedoStack.length === 0;
}}

function leSave() {{
  const lessonId = document.getElementById('le-lesson-filter').value;
  if (!lessonId) return;
  const plan = leEditPlans.find(l => l.lesson_id === lessonId);
  if (!plan) return;

  // Reconstruct clean HTML from current state
  const body = document.getElementById('le-lesson-body').cloneNode(true);

  // Remove popups and screenshot wraps (editorial markup only)
  body.querySelectorAll('.tc-popup').forEach(n => n.remove());
  // Remove screenshot tc-wraps entirely (they are notes, not content)
  body.querySelectorAll('.tc-wrap[data-type="screenshot"]').forEach(wrap => wrap.remove());

  // Resolve each text tc-wrap to plain text based on state
  body.querySelectorAll('.tc-wrap').forEach(wrap => {{
    const state = wrap.dataset.state || 'pending';
    const type = wrap.dataset.type;
    const orig = wrap.dataset.orig || '';
    const sugg = wrap.dataset.sugg || '';
    let replacement = '';
    if (state === 'accepted') replacement = (type === 'delete') ? '' : (type === 'add') ? orig + sugg : sugg;
    else replacement = orig; // rejected or pending → keep original text
    wrap.replaceWith(document.createTextNode(replacement));
  }});

  // Revert prefixed image paths back to relative (strip the ../lesson_dir/ prefix)
  const lessonBase = '../' + (plan.lesson_dir || '').split('/').map(s => encodeURIComponent(s)).join('/') + '/';
  body.querySelectorAll('img[src]').forEach(img => {{
    const attrSrc = img.getAttribute('src') || '';
    if (attrSrc.startsWith(lessonBase)) {{
      img.setAttribute('src', attrSrc.slice(lessonBase.length));
    }}
  }});

  const cleanHtml = body.innerHTML;
  const banner = document.getElementById('le-save-banner');

  // Try server-side save via serve.py /api/save-lesson endpoint
  fetch('/api/save-lesson', {{
    method: 'POST',
    headers: {{ 'Content-Type': 'application/json' }},
    body: JSON.stringify({{
      lesson_dir: plan.lesson_dir || '',
      to_version: TO_VERSION,
      html_content: cleanHtml,
    }}),
  }})
  .then(async r => {{
    if (r.status === 409) {{
      const body = await r.json();
      if (confirm(`File already exists at:\\n${{body.target_path}}\\n\\nOverwrite?`)) {{
        return fetch('/api/save-lesson', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ lesson_dir: plan.lesson_dir || '', to_version: TO_VERSION, html_content: cleanHtml, force: true }}),
        }}).then(r2 => r2.json());
      }}
      return null;
    }}
    if (!r.ok) throw new Error('HTTP ' + r.status);
    return r.json();
  }})
  .then(result => {{
    if (!result) return;
    banner.style.display = 'block';
    banner.innerHTML = `✓ Saved to: <code>${{escHtml(result.target_path)}}</code>`;
  }})
  .catch(() => {{
    // Fallback: browser download
    const blob = new Blob([cleanHtml], {{ type: 'text/html;charset=utf-8' }});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url; a.download = 'index.html'; a.click();
    URL.revokeObjectURL(url);
    banner.style.display = 'block';
    banner.innerHTML = `Downloaded index.html — place it at: <code>${{escHtml(plan.lesson_dir || lessonId)}}/index.html</code> (updated to target version). For direct saving, use <code>python serve.py</code> instead of <code>python -m http.server</code>.`;
  }});
}}
</script>
</body>
</html>"""
