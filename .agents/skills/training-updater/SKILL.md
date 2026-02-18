# training-updater

Use this skill for end-to-end training content updates driven by a change ledger.

## Workflow
1. Build/refresh lesson manifest from HTML lessons.
2. Build docs change ledger (Jira snapshot or changelog input).
3. Generate update queue from manifest + ledger.
4. Execute one lesson at a time: generate update spec first, then apply minimal edits.

## Commands
- Build manifest:
  - `python tools/build_lesson_manifest.py --config tools/config.json --out artifacts/lesson_manifest.json`
- Jira snapshot pull:
  - `python tools/pull_from_jira.py --jql "project = DOCS" --out inputs/jira_snapshot.json`
- Normalize Jira export (CSV/JSON) to internal snapshot:
  - `python tools/ingest_jira_export.py --in inputs/jira_export.csv --out inputs/jira_snapshot.json`
- Generate changelog from Jira snapshot:
  - `python tools/generate_changelog_from_jira.py --in inputs/jira_snapshot.json --out inputs/changelog_generated.md`
- Jira snapshot to ledger:
  - `python tools/jira_to_change_ledger.py --in inputs/jira_snapshot.json --out artifacts/docs_change_ledger.jsonl`
- Queue generation:
  - `python tools/generate_update_queue.py --manifest artifacts/lesson_manifest.json --ledger artifacts/docs_change_ledger.jsonl --out artifacts/update_queue.json`
- Apply one lesson update:
  - `python tools/apply_update_queue.py --queue artifacts/update_queue.json --manifest artifacts/lesson_manifest.json --ledger artifacts/docs_change_ledger.jsonl --lesson-id <lesson_id>`

## Guardrails
- Never bulk-edit without writing `artifacts/update_specs/<lesson_id>.json` first.
- If evidence is weak, add TODO markers instead of inventing UI details.
- Only flag screenshot likely-stale when tied to specific ledger evidence.
