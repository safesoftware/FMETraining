# Training Update Automation

This folder documents the repo-local automation pipeline for lesson updates.

## 0) Define update scope (recommended)

To avoid huge cross-version queues, define exactly what this update round should touch:

- `from_version`: archived source context (for operator intent/history)
- `to_version`: only this version's lessons are eligible for edits
- `courses`: course name/path patterns to include

Example:

```bash
cp inputs/update_scope.example.json inputs/update_scope.json
```

## 1) Build the lesson manifest

```bash
python tools/build_lesson_manifest.py --config tools/config.json --out artifacts/lesson_manifest.json
```

Optional scoped manifest build:

```bash
python tools/build_lesson_manifest.py \
  --versions 2024.1,2025.0 \
  --courses "Connect Automations with Job Orchestration" \
  --out artifacts/lesson_manifest_scoped.json
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

Dry-run:

```bash
python tools/pull_from_jira.py --jql "project = DOCS" --release "2026.1" --dry-run
```

## 2a) Normalize Jira export input (CSV or JSON)

```bash
python tools/ingest_jira_export.py --in inputs/jira_export.csv --out inputs/jira_snapshot.json
```

## 3) Generate deterministic docs changelog from Jira snapshot

```bash
python tools/generate_changelog_from_jira.py --in inputs/jira_snapshot.json --out inputs/changelog_generated.md
```

## 4) Build docs Change Ledger

```bash
python tools/jira_to_change_ledger.py --in inputs/jira_snapshot.json --out artifacts/docs_change_ledger.jsonl
```

## 5) Generate update queue (scoped)

Using a scope file:

```bash
python tools/generate_update_queue.py \
  --manifest artifacts/lesson_manifest.json \
  --ledger artifacts/docs_change_ledger.jsonl \
  --scope-file inputs/update_scope.json \
  --out artifacts/update_queue.json
```

Or explicit CLI scope:

```bash
python tools/generate_update_queue.py \
  --manifest artifacts/lesson_manifest.json \
  --ledger artifacts/docs_change_ledger.jsonl \
  --from-version 2024.0 \
  --to-version 2025.0 \
  --courses "*Connect Automations with Job Orchestration 2025.0,*Build Versatile Automations 2025.0" \
  --out artifacts/update_queue.json
```

## 6) Apply updates one lesson at a time

```bash
python tools/apply_update_queue.py \
  --queue artifacts/update_queue.json \
  --manifest artifacts/lesson_manifest.json \
  --ledger artifacts/docs_change_ledger.jsonl \
  --limit 1
```

## 7) Demo mode without Jira access

```bash
python tools/ingest_jira_export.py --in inputs/sample_jira_export.csv --out inputs/jira_snapshot.json
python tools/generate_changelog_from_jira.py --in inputs/jira_snapshot.json --out inputs/changelog_generated.md
python tools/jira_to_change_ledger.py --in inputs/jira_snapshot.json --out artifacts/docs_change_ledger.jsonl
python tools/build_lesson_manifest.py --versions 2024.1 --courses "Connect Automations with Job Orchestration 2024.1" --out artifacts/lesson_manifest_demo.json
python tools/generate_update_queue.py --manifest artifacts/lesson_manifest_demo.json --ledger artifacts/docs_change_ledger.jsonl --from-version 2023.0 --to-version 2024.1 --courses "*Connect Automations with Job Orchestration 2024.1" --out artifacts/update_queue.json
python tools/apply_update_queue.py --manifest artifacts/lesson_manifest_demo.json --queue artifacts/update_queue.json --ledger artifacts/docs_change_ledger.jsonl --limit 1
```

## Privacy and sensitive data handling

- Raw Jira snapshots can contain sensitive details.
- Keep live snapshots in `inputs/` for reproducibility, but sanitize before sharing.
- Prefer default Jira pull fields and only opt-in to comments/attachments when necessary.
