# AGENTS.md — Rules for AI Agents Working in This Repository

## Issue Tracking

Track issues in `ISSUES.md`. Use headers to indicate if issues are **Open**, **In Review**, or **Closed** (currently uses **Fixed**/**Won't Do**/**Future Work**). Number issues sequentially. Keep the file up-to-date when making changes — move issues between sections and add new ones as appropriate. Focus on issues listed under **Open** unless the user specifies otherwise.

## Critical Rules

1. **You are working in a sensitive environment. Do not attempt to commit files in the /data or /artifacts folder, and always use environment variables for credentials.**

2. **Never hardcode credentials or print API keys to stdout/logs.**
   The `OPENAI_API_KEY` and any other secrets must only be read from the `.env` file via `python-dotenv`. Never commit `.env`.

3. **The lesson index.html files are read-only inputs — never write to them.**
   HTML training content under version folders (e.g. `2025.0/`, `2024.1/`) is source content. Do not modify these files.

4. **Artifact files are run-specific.**
   Once a `manifest/changelog/recommendations` file is written for a `run_id`, do not overwrite it. The report (`report-{RUN_ID}.html`) may be regenerated via `--report-only`.

## Development Notes

- Python 3.11+ required
- Install dependencies: `pip install -r requirements.txt`
- Copy `.env.sample` to `.env` and fill in `OPENAI_API_KEY` before running
- Preview scope without API calls: `python pipeline.py --dry-run`
- Run steps 1 and 2 first to validate scope and Jira filtering before incurring API costs: `python pipeline.py --steps 1,2`
- Resume an interrupted run: `python pipeline.py --resume <RUN_ID>`

## Repository Structure

```
{version}/{learning_path}/{course}/{lesson}/index.html
```

- Version folders: top-level, e.g. `2025.0/`
- Learning paths: e.g. `fme-form-basic/`
- Courses: include version suffix in folder name, e.g. `Connect To Data 2025.0/`
- Lessons: contain `index.html` and `images/`

---

## Agent Team Structure

This project has no automated test suite. Changes to the pipeline, renderer, and launcher frequently appear to work in isolation but break the actual browser UI or produce malformed output. All non-trivial changes must go through the full team workflow below before being considered done.

### Roles

| Role | Responsibility |
|------|---------------|
| **Research** | Reads the relevant source files, artifacts, and ISSUES.md. Produces a written diagnosis: what the code currently does, why it is wrong, and what constraints any fix must satisfy. Does not propose solutions yet. |
| **Planner** | Takes the Research output. Designs the fix: which files change, what the logic is, and what edge cases exist. Writes an explicit plan before any code is touched. |
| **Builder** | Implements exactly the plan. Makes no scope additions. Flags any deviation from the plan back to Planner before proceeding. |
| **Test Author** | After Builder is done, writes concrete test cases covering the fix and the most likely regressions. For pipeline code this means Python assertions or a short script. For renderer/launcher JS this means a checklist of browser-observable states to verify. |
| **Tester** | Executes the test cases. For Python: runs the test script and captures stdout. For browser UI: runs the pipeline end-to-end on a real run, opens the report, and confirms each checklist item. Reports pass/fail per case — never "looks fine." |
| **Verifier** | Reads the Tester output. Checks that every test case was actually executed and that no test was marked passing without evidence. Rejects the change if any case is untested or failing. |
| **Reviewer** | Final gate. Confirms the plan was followed, the tests are meaningful, and ISSUES.md has been updated. Approves or sends back with specific objections. |

### Workflow

```
Research → Planner → Builder → Test Author → Tester → Verifier → Reviewer
                       ↑                                    |
                       └────────────── re-plan ─────────────┘
```

If Verifier or Reviewer rejects, the loop returns to Planner — not to Builder. The fix strategy is reconsidered before any new code is written.

### What Counts as a Passing Test

- **Pipeline code** (steps 1–6, `edit_suggestions.py`, `report.py`, etc.): run the affected function with a known input and assert the output. Use real artifact files from `artifacts/` where possible. A test that only checks that the code runs without error is not sufficient.
- **Renderer / Lesson Edits tab**: open the report in a browser, load a lesson with at least two changes sharing the same `original_text`, and confirm each occurrence is wrapped independently with its own accept/reject popup. Confirm no cascading markup appears.
- **Launcher UI** (Re-Run, Continue, Generate Edit Suggestions buttons): open the launcher, trigger the action, and confirm the UI state matches the expected outcome (correct lessons selected, correct steps checked, button enabled/disabled correctly).
- **Step 6 incremental logic**: run step 6 twice on the same run. Confirm the second run skips the already-completed lesson and does not overwrite it.

### Key Failure Patterns to Guard Against

- **Silent failures in step 6**: a missing import, schema mismatch, or API error causes `_call_openai` to return `None` after retries. The lesson is silently skipped and `completed_lessons` stays 0. The step is still marked complete. **Test**: assert `completed_lessons > 0` after any step 6 run that is expected to produce output.
- **Cascading markup in the renderer**: multiple changes with the same `original_text` cause `html.replace()` to match inside already-injected spans. **Test**: render a lesson with two changes sharing `original_text` and confirm the output HTML contains exactly two non-nested `tc-wrap` spans.
- **Re-Run prefill fails silently**: `prefillConfigureRun` runs but the wrong content tree version is loaded, so no lessons are checked. **Test**: click Re-Run on a run whose scope is from version X. Confirm the browse-version dropdown changes to X and the correct lessons are checked.
- **`isLive` blocks buttons for completed runs**: `live_status` is `"done"` (truthy) for runs completed in the current server session, hiding Re-Run and Continue. **Test**: start a run, let it finish, reload Run History, confirm both buttons appear.

### Running the App Locally for Manual Tests

```bash
python serve.py 8080          # start server
# open http://localhost:8080  in browser
# open report: http://localhost:8080/artifacts/report-{RUN_ID}.html
```

Port forwarding must be active in VS Code (Ports tab). If the port times out, kill and restart `serve.py` and re-forward the port.
