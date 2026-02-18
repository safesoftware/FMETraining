# Plan Update Queue

You are generating `artifacts/update_queue.json`.

Inputs:
- `artifacts/lesson_manifest.json`
- `artifacts/docs_change_ledger.jsonl`
- optional scope: `inputs/update_scope.json` (`from_version`, `to_version`, `courses[]`)
- Schema: `.codex/schemas/update_queue.schema.json`

Requirements:
1. Apply scope first (target courses + target version), then map each change ledger record to one or more in-scope lessons with confidence score in [0,1].
2. Set `required_update_types` from:
   - `text edits`
   - `exercise step edits`
   - `screenshot updates`
3. For screenshot tasks, only include `likely_stale_screenshots` when there is direct evidence from change type or label/workflow changes.
4. Output deterministic ordering by descending confidence then task_id.
5. Do not invent UI details.
