# Training Update Automation

This folder documents the repo-local automation pipeline for lesson updates.

## 1) Build the lesson manifest

```bash
python tools/build_lesson_manifest.py --config tools/config.json --out artifacts/lesson_manifest.json
```

Optional subset run for fast demos:

```bash
python tools/build_lesson_manifest.py --config tools/config.json --limit 3 --out artifacts/lesson_manifest_demo.json
```

## 2) Pull from Jira (live)

Set environment variables (see `.env.example`):

- `JIRA_BASE_URL`
- `JIRA_USER_EMAIL` (or username)
- `JIRA_API_TOKEN` (or `JIRA_PAT`)
- `JIRA_API_VERSION` (`auto`, `2`, or `3`)

Example with JQL:

```bash
python tools/pull_from_jira.py \
  --jql "project = DOCS AND labels = academy AND statusCategory = Done" \
  --since "2026-01-01" \
  --release "2026.1" \
  --max-issues 200 \
  --out inputs/jira_snapshot.json
```

Dry-run (resolves JQL without fetching):

```bash
python tools/pull_from_jira.py --jql "project = DOCS" --release "2026.1" --dry-run
```

## 2a) Normalize Jira export input (CSV or JSON)

If your team provides a Jira CSV export instead of API access, normalize it into the internal snapshot format first:

```bash
python tools/ingest_jira_export.py --in inputs/jira_export.csv --out inputs/jira_snapshot.json
```

You can also normalize an existing JSON export/snapshot:

```bash
python tools/ingest_jira_export.py --in inputs/jira_snapshot.json --out inputs/jira_snapshot.json
```

The field mapping used for CSV ingestion is configurable in `tools/jira_field_map.json`.

## 3) Generate deterministic docs changelog from Jira snapshot

```bash
python tools/generate_changelog_from_jira.py --in inputs/jira_snapshot.json --out inputs/changelog_generated.md
```

## 4) Build docs Change Ledger

From Jira snapshot (small-grained records):

```bash
python tools/jira_to_change_ledger.py --in inputs/jira_snapshot.json --out artifacts/docs_change_ledger.jsonl
```

Generic loader (markdown or Jira CSV/JSON exports):

```bash
python tools/load_change_ledger.py --type markdown --in inputs/changelog_generated.md --out artifacts/docs_change_ledger.jsonl
```

## 5) Generate update queue

```bash
python tools/generate_update_queue.py \
  --manifest artifacts/lesson_manifest.json \
  --ledger artifacts/docs_change_ledger.jsonl \
  --out artifacts/update_queue.json
```

Codex prompt-driven option:

```bash
codex exec .github/codex/prompts/plan_queue.md
```

## 6) Apply updates one lesson at a time

Single lesson/task batch (writes per-lesson spec first):

```bash
python tools/apply_update_queue.py \
  --queue artifacts/update_queue.json \
  --manifest artifacts/lesson_manifest.json \
  --ledger artifacts/docs_change_ledger.jsonl \
  --limit 1
```

Dry-run:

```bash
python tools/apply_update_queue.py --dry-run --limit 1
```

Codex prompt-driven option:

```bash
codex exec .github/codex/prompts/apply_one.md
```

## 7) Demo mode without Jira access

Use the sanitized sample snapshot:

```bash
python tools/ingest_jira_export.py --in inputs/sample_jira_export.csv --out inputs/jira_snapshot.json
python tools/generate_changelog_from_jira.py --in inputs/jira_snapshot.json --out inputs/changelog_generated.md
python tools/jira_to_change_ledger.py --in inputs/jira_snapshot.json --out artifacts/docs_change_ledger.jsonl
python tools/build_lesson_manifest.py --limit 3 --out artifacts/lesson_manifest_demo.json
python tools/generate_update_queue.py --manifest artifacts/lesson_manifest_demo.json --ledger artifacts/docs_change_ledger.jsonl --out artifacts/update_queue.json
python tools/apply_update_queue.py --manifest artifacts/lesson_manifest_demo.json --queue artifacts/update_queue.json --ledger artifacts/docs_change_ledger.jsonl --limit 1
```

## Privacy and sensitive data handling

- Raw Jira snapshots can contain sensitive details.
- Keep live snapshots in `inputs/` for reproducibility, but sanitize before sharing.
- Prefer default Jira pull fields and only opt-in to comments/attachments when necessary.
