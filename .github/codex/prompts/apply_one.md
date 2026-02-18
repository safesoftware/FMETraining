# Apply One Lesson Update Task

Given one queue item:
1. Read the queue task, matching lesson manifest entry, and matching change ledger record.
2. Produce `artifacts/update_specs/<lesson_id>.json` first (must conform to `.codex/schemas/update_spec.schema.json`).
3. Apply only the edits in the spec to the lesson HTML file.
4. Keep diffs minimal and reviewable.
5. If evidence is insufficient, add a TODO marker and cite missing evidence.
6. Never bulk-edit multiple lessons in a single pass without per-lesson specs.
