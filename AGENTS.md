# Agent Working Rules for FMETraining

## Scope
These rules apply to the entire repository.

## Style and coding rules
- Prefer Python standard library over third-party dependencies.
- Keep scripts deterministic: sorted inputs, stable output ordering, and explicit UTF-8 file handling.
- Keep functions small and testable; avoid hidden global state.
- Do not wrap imports in try/catch blocks.

## Step formatting and update artifacts
- Exercise steps should be extracted as ordered records with step number, heading, and supporting text.
- Change-ledger records must be small-grained (one user-visible change per record).
- Queue tasks must identify one target lesson per task with a confidence score and explicit update types.

## Screenshot conventions
- Never claim a screenshot is updated unless a new image artifact is present.
- Mark screenshots as `likely_stale` only when evidence exists (e.g., label rename/workflow change touching that lesson).

## Definition of done
- Schemas exist for manifest, change-ledger record, queue, and update spec.
- Scripts support dry-run where relevant and fail with clear errors on invalid input.
- Demo pipeline can run from the provided sample Jira snapshot without live Jira access.
- Output artifacts are written under `artifacts/` or `inputs/` as documented.
