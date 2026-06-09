"""One-shot migration scripts.

Each module under this package converts one piece of legacy on-disk state
into the rows + scratch files that the Postgres-backed deployment expects.
The scripts are idempotent: running the same script twice on the same
source leaves the database in the same state. See KNOW-2271 + the deploy
runbook in ``docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md``.
"""
