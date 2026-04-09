---
name: retrospective
description: >
  Run a retrospective analysis on an FME Training Automation update run.
  Compares the tool's suggested edits against the actual changes made in the
  target version folder to measure accuracy (accepted/rejected/reworded/missed).
  Use this skill whenever the user mentions: running a retrospective, checking
  tool accuracy, analyzing a run, comparing suggested vs actual changes,
  measuring accept/reject rates, or identifying improvements after an update
  cycle. Also trigger when the user references a run ID like 20260317T155430-28a8
  alongside words like "analyze", "review", "compare", or "retrospective".
---

# Retrospective Skill

## What this skill does

Runs `pipeline/retrospective.py` against a completed edit-plans run, displays
a per-lesson accuracy table, and optionally produces a narrative analysis
and/or new ISSUES.md entries based on the findings.

## Step 1 — Gather inputs

If the user supplied a run ID as an argument, use it. Otherwise ask:

```
Which run would you like to analyze?
- Run ID (e.g. 20260317T155430-28a8) — check artifacts/runs.json for available runs
- Source version (default: the run's source version from the edit-plans file)
- Target version (default: the run's target version from update-job.json)
```

To list available runs with edit plans:
```bash
python3 -c "
import json
from pathlib import Path
runs = json.loads(Path('artifacts/runs.json').read_text())
for r in runs.get('runs', []):
    if r.get('steps_completed') and 6 in r['steps_completed']:
        print(r['run_id'], '|', r.get('learning_path',''), '|', r.get('to_version',''))
"
```

## Step 2 — Run the script

```bash
python pipeline/retrospective.py \
  --run-id <RUN_ID> \
  [--source-version <SRC>] \
  [--target-version <TGT>] \
  --no-detail
```

- Omit `--source-version` and `--target-version` if the defaults (2024.2 / 2026.1) apply.
- The script prints the summary table and writes `artifacts/retrospective-<RUN_ID>.json`.
- If the script fails because `edit-plans-<RUN_ID>.json` doesn't exist, tell the user
  they need to run Step 6 (edit suggestions) first.

## Step 3 — Display the table

Reproduce the printed summary table in the conversation so the user can read it
without switching to the terminal. Include the legend below it.

## Step 4 — Ask what to do next

After showing the table, ask:

> Would you like me to:
> 1. **Narrative analysis** — identify patterns (which lesson types, Jira project types,
>    change types had the highest/lowest acceptance), explain what drove the numbers.
> 2. **ISSUES.md suggestions** — read `ISSUES.md` and the retrospective JSON, identify
>    gaps not yet tracked, and draft new numbered issue entries with enough detail to
>    implement in a future session.
> 3. **Both**
> 4. **Neither** — we're done.

Accept a number or plain text.

## Step 5a — Narrative analysis (if requested)

Read `artifacts/retrospective-<RUN_ID>.json`. Produce a written retrospective covering:

**Acceptance rate breakdown**
- Overall accept rate (combined text + screenshots)
- By Jira project prefix (e.g. FMEFORM vs FMEENGINE) — group `changes` by `issue_keys[0]` prefix
- By lesson type (exercise vs conceptual) — exercises have "Exercise_" in lesson_name
- By change type (text `changes` vs `screenshot_updates`)

**Missed change patterns**
- How many text sections and screenshots were missed?
- What kinds of headings appear in `missed_changes`? (step-by-step instructions,
  resources, conceptual sections?)
- Are missed screenshots concentrated in certain lessons?

**Top performers and worst performers**
- Which lessons had the highest accept rate? What made them different?
- Which lessons had 0%? What types of suggestions were made?

**Key insight**
- One or two sentences summarising the single most actionable takeaway.

Keep the analysis concise — bullet points preferred over prose paragraphs.

## Step 5b — ISSUES.md suggestions (if requested)

1. Read `ISSUES.md` in full to understand existing open issues and the next available number.
2. Read `artifacts/retrospective-<RUN_ID>.json` for evidence.
3. For each gap you identify:
   - Check whether it's already captured (open or fixed) in `ISSUES.md`.
   - If not captured, draft a new issue entry following this format:
     ```
     - N. **Short title.** One-sentence description of the failure mode observed,
       with a concrete example from the retrospective (lesson name, change ID, or stat).
       Fix: specific change to make in code or prompts, with file paths where known.
     ```
4. Ask the user to confirm before writing to `ISSUES.md`.
5. If confirmed, append the new issues to the Open / AI Accuracy section with the
   next sequential number.

## Tips for accurate classification

The script classifies each suggestion as:
- **accepted** — suggested_text (or close variant) found in target HTML
- **rejected** — original_text unchanged in target HTML
- **reworded** — section changed but not to the suggested text
- **missed** — actual edit made that no suggestion covered
- **na** — original_text not found in source (stale/hallucinated suggestion)

If classification results look wrong (e.g. many "reworded" when you know you accepted
most suggestions), the similarity thresholds in the script may need tuning:
- `ACCEPTED_THRESHOLD = 0.82` in `pipeline/retrospective.py`
- `REJECTED_THRESHOLD = 0.90`
