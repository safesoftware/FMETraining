# AGENTS.md — Rules for AI Agents Working in This Repository

## Git Workflow

These rules apply to **all work**, not just specific projects.

1. **Never commit directly to `main` or `master`.** Always work on a feature branch (e.g. `feature/<topic>`, `fix/<topic>`). Branch off the latest `main`.
2. **Commit messages must be descriptive.** Subject line in imperative mood, ≤72 characters. Body explains the *why* (motivation, trade-offs, links to Jira issue), not the *what* (the diff already shows that). Reference the Jira key (e.g. `KNOW-1234`) in the subject or body so commits link back to issues.
3. **Make small, focused commits.** Prefer many small commits with clear scope over one giant commit. Each commit should leave the tree in a buildable state.
4. **Push regularly.** Don't sit on local-only commits — push to the remote feature branch so work is visible and recoverable.
5. **Merge to `main` only via pull request.** Open the PR with `gh pr create` (see process at the bottom of this file). Do not fast-forward locally.
6. **Never commit secrets.** API keys, OAuth client secrets, session signing keys, AWS credentials, OpenAI / Jira / Skilljar tokens, database passwords — none of these go in git. They live in `.env` (local, gitignored) or AWS Secrets Manager (production). Add a `.env.example` with placeholder values instead.
7. **Before staging files, sanity-check the diff for accidental secret patterns** (`AKIA[0-9A-Z]{16}`, `sk-[A-Za-z0-9]{20,}`, `xoxb-`, `ghp_`, etc.). If you spot anything that looks like a credential, stop and ask.
8. **Never bypass hooks** (`--no-verify`, `--no-gpg-sign`) without explicit user permission. If a hook fails, fix the underlying problem.

## Issue Tracking

Issues are tracked in **Jira project KNOW** (https://safesoftware.atlassian.net/jira/software/projects/KNOW/boards). Do not add new items to `ISSUES.md` — it is a historical archive only.

### When to file an issue

File a Jira issue for **every meaningful unit of work** — features, bug fixes, refactors, infrastructure changes, doc updates that take more than a few minutes. Don't wait for someone to file it for you. Multi-step plans get a parent story plus child tasks.

When filing, use these standard fields:
- **Type:** Task
- **Assignee:** sam.walker@safe.com (account ID `5a6103bb9d0ea46a7a5b6cde`)
- **Component:** Development
- **Class of Service:** Standard (`customfield_10253`: `{"value": "Standard"}`)

Use the Jira MCP (`mcp__claude_ai_Atlassian__createJiraIssue`, cloud ID `646a4867-d35f-4b64-958d-eb9a1def6740`). See `memory/jira_config.md` for the full field config and workflow transition IDs.

### Workflow — agents move issues through states themselves

| State | When to move here | Transition |
|---|---|---|
| **In Backlog** | Default on creation. Use for anything not yet ready to start. | (create) |
| **Ready for Work** | Scope is clear, dependencies satisfied, ready to pick up. | `241` |
| **In Progress** | An agent is actively working on it. | `211` |
| **Ready for QA** | Implementation done, awaiting human review/testing. | `31` |
| **Closed** | Verified done. | `301` |
| **Closed (Won't Do)** | Decided not to pursue. | `201` |

Agents are responsible for moving their own issues. Don't leave an issue in **In Progress** when you've stopped working on it — either move it forward to **Ready for QA** with a verification comment, or back to **Ready for Work** / **In Backlog** with a note explaining what blocked you.

### Comments — leave a trail

After every meaningful chunk of progress, comment on the issue with:
- What was implemented (one or two sentences).
- Commit SHAs and/or PR link.
- Any decisions worth recording.

### Moving to "Ready for QA" — required comment format

Whenever you transition an issue to **Ready for QA** — whether the work is complete and awaiting human verification, or you've hit a question that blocks progress — the **same** transition comment must include:

1. **Status summary** — one or two sentences on where things stand.
2. **Verification steps** — numbered, copy-pasteable commands or click-paths a human can run, with expected output. Be specific. Bad: "test the new endpoint." Good: "1. `curl -i http://localhost:8000/api/runs` → expect 401 with body `{\"detail\":\"Not authenticated\"}`." **The Jira ticket is the canonical home for these steps**, not the PR. QA reads Jira, not GitHub. Putting the manual / browser / live-integration steps only in the PR's "Test plan" section is incomplete — they must also appear on the ticket. If every verification step is automated and there are no manual ones, say so explicitly: *"All verification automated; no manual steps required."* It is fine — encouraged — to mirror the steps in the PR body too, but the ticket is the source of truth.
3. **Open questions** — bulleted list, or "None" if there are none.
4. **`@mention`** — tag `sam.walker@safe.com` so the user gets notified.

This rule is non-negotiable. A "Ready for QA" issue without these four elements is incomplete and will be sent back.

### MCP tool reference

- `mcp__claude_ai_Atlassian__createJiraIssue` — file a new issue.
- `mcp__claude_ai_Atlassian__transitionJiraIssue` — move through workflow states (use the IDs above).
- `mcp__claude_ai_Atlassian__addCommentToJiraIssue` — leave progress comments.
- `mcp__claude_ai_Atlassian__editJiraIssue` — update summary, description, fields.
- `mcp__claude_ai_Atlassian__searchJiraIssuesUsingJql` — find existing issues before filing duplicates.

## Planning

Multi-step work (anything taking more than a few hours, anything touching multiple modules, anything with phasing or staging) gets a written plan **before** code starts. Use plan mode in Claude Code, or hand-write a Markdown plan otherwise.

### Challenge inherited plans before executing them

When you pick up a plan written by a previous session — whether it's a `docs/plans/*.md` file, a Jira description, or a half-written PR — your **first job is to confirm the plan's scope still fits the constraints**, not to start executing.

Specifically, before touching code, restate in chat:

1. **Who's the audience?** (Number of users, internal vs external, regulated workload, etc.)
2. **What's the SLA?** (Downtime tolerance in minutes, hours, or "during business hours.")
3. **What's the budget?** (Implicit if not stated — flag if the plan is implicitly above what a tool of this size would warrant.)
4. **What's the operator's experience level?** ("Has only deployed a static site" implies a different deployment than "runs a fleet of microservices.")

Then ask: **does the plan's complexity match these constraints?** If a 5-user internal tool's plan reads like a customer-facing SaaS architecture, push back before building anything. The cheapest token to spend is the one that says "this looks heavy for what you described — want me to draft a simpler alternative first?"

A plan inherited from another session does not get a free pass. The previous session may have had different information, or no information, or simply missed the scope mismatch.

### Saving approved plans

When a plan is **approved by the user**, save it to `docs/plans/YYYY-MM-DD-short-slug.md`:

- The date is the date of approval (not the date work begins).
- The slug is a 2–4 word kebab-case description (e.g. `multi-user-web-app-deployment`, `jira-pii-scrub`).
- Commit the plan file alongside the first piece of code that executes against it, on the same feature branch.

**Why save them:** future agent sessions need to know what was decided and why. The plan is the durable artifact; the original Claude Code chat may not be visible later. A reviewer also benefits from being able to compare the implementation against the agreed plan.

If a later plan supersedes an earlier one, mark the earlier file with a "Status: superseded by `<path>`" note at the top rather than deleting it — the chain of decisions is part of the audit trail.

Existing plans:
- `docs/plans/2026-04-29-multi-user-web-app.md` — architecture decisions for the multi-user web app rebuild (KNOW-2257). The deployment shape it sketches (App Runner + Fargate + RDS + …) is **superseded** by the EC2 alternative below for v1.
- `docs/plans/2026-05-05-multi-user-web-app-deployment.md` — original AWS managed-services deployment runbook. **Superseded** by the EC2 alternative.
- `docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md` — single-EC2 deployment for v1. The active deployment plan.
  - `docs/deployment.md` — operator-facing runbook for the active deployment plan: how to deploy, roll back, read `/health`, and triage when something looks wrong (KNOW-2294).

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

---

## Pull Requests

Use `gh pr create` to open PRs to `main`. Required structure:

- **Title:** short and concrete (≤70 chars). Reference the Jira key when applicable: `KNOW-1234: short description`.
- **Body:**
  - **Summary** — 1–3 bullets on what changed and why.
  - **Jira link** — full URL to the parent issue.
  - **Test plan** — bulleted checklist of how to verify (commands to run, click-paths for UI, what to look for).
  - **Notes for reviewer** — anything non-obvious: decisions made, alternatives considered, follow-ups deferred.

Open PRs as soon as the work is meaningfully reviewable, even if not 100% done — mark them as draft (`gh pr create --draft`) until ready for merge. Don't sit on a long-lived branch.

Never force-push to a branch someone else might be reviewing. If you need to rewrite history on your own feature branch (e.g., to clean up commits before merge), warn in a PR comment first.

When the PR is approved and CI is green, merge with **squash-and-merge** by default unless the commit history is intentionally meaningful. Delete the branch after merge.
