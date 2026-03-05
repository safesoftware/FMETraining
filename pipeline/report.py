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
from pipeline.utils import recommendations_path, report_path


def build_report(
    run_id: str,
    output_dir: Path,
    recs_path: Path | None = None,
) -> Path:
    """
    Generate the HTML report for a completed run.

    Args:
        run_id:     The run ID to generate a report for.
        output_dir: Artifacts directory (for writing the HTML).
        recs_path:  Override path to the recommendations JSON.

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

    html = _build_html(run_id, recs_path.name, model, total, completed, generated_at, config.JIRA_BASE_URL)

    out_path = report_path(run_id, output_dir)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  Report written: {out_path.name}")
    print(f"  To view: python -m http.server 8080  (run from project root)")
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
/* Status filter chips */
.status-filters {{ display: flex; gap: 8px; align-items: center; }}
.status-filters label {{ display: flex; align-items: center; gap: 4px; cursor: pointer; font-size: 0.85rem; }}
</style>
</head>
<body>

<header>
  <h1>FME Training Update Report</h1>
  <div class="meta">Run: {run_id} &nbsp;|&nbsp; Model: {model} &nbsp;|&nbsp; Generated: {generated_at} &nbsp;|&nbsp; Total pairs: {completed_pairs:,}</div>
</header>

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

<script>
const JSON_FILE = '{json_filename}';
const JIRA_BASE_URL = '{jira_base_url}';
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

  return `
<div class="card" data-rec="${{rid}}" data-status="${{status}}">
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
      <p style="font-size:0.78rem;color:#888;margin-top:2px">Affects: ${{(a.affects_versions || []).join(', ') || 'n/a'}}</p>
    </div>
    <div class="card-section">
      <h4>Assessment</h4>
      <details class="assessment-section" open>
        <summary>Summary</summary>
        <div class="section-body"><p class="justification">${{escHtml(a.justification || '')}}</p></div>
      </details>
      ${{affectedHtml}}
      ${{screenshotDetailsHtml}}
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
</script>
</body>
</html>"""
