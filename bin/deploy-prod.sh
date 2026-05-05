#!/usr/bin/env bash
# bin/deploy-prod.sh — apply a new revision to the running EC2 instance.
#
# Run this from inside an SSH session on the production box, as the
# application user (`fmetrain`). The script:
#
#   1. Records the current git SHA (so you can rollback in one command).
#   2. Pulls the requested ref (default: main) and updates dependencies.
#   3. Validates the migration on a scratch Postgres database before
#      touching the real one. Migration breakage is the one failure mode
#      that doesn't roll back cleanly, so this guard is the cheapest
#      safety net.
#   4. Applies the migration to production and restarts the web service.
#
# Reference: docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md
#
# Usage:
#   ./bin/deploy-prod.sh [<git-ref>]      # default ref is main
#
# Env overrides:
#   APP_DIR    — install location (default: /opt/fme-train)
#   PG_DB      — main DB name      (default: fme_train)
#   PG_USER    — DB role           (default: fmetrain)
#   SCRATCH_DB — name of scratch DB used for the migration check
#                (default: fme_train_migration_check)

set -euo pipefail

REF="${1:-main}"
APP_DIR="${APP_DIR:-/opt/fme-train}"
PG_DB="${PG_DB:-fme_train}"
PG_USER="${PG_USER:-fmetrain}"
SCRATCH_DB="${SCRATCH_DB:-fme_train_migration_check}"

log() { printf '\n[deploy] %s\n' "$*"; }

cd "${APP_DIR}"

# --------------------------------------------------------------------------
# Capture pre-deploy state
# --------------------------------------------------------------------------
PREV_SHA="$(git rev-parse HEAD)"
log "Current revision: ${PREV_SHA}"

# --------------------------------------------------------------------------
# Pull + install
# --------------------------------------------------------------------------
log "Fetching origin/${REF}…"
git fetch origin
git reset --hard "origin/${REF}"
NEW_SHA="$(git rev-parse HEAD)"

log "Installing dependencies…"
"${APP_DIR}/.venv/bin/pip" install -q --upgrade pip
"${APP_DIR}/.venv/bin/pip" install -q -r requirements.txt

# --------------------------------------------------------------------------
# Migration safety check
#
# Spin up a clean copy of the prod DB into a scratch DB, run alembic
# upgrade against it, drop it. If this fails, prod is untouched.
# --------------------------------------------------------------------------
log "Validating migration against scratch DB (${SCRATCH_DB})…"
# Build a scratch DB by dumping prod's structure (no data) into it.
dropdb --if-exists -U "${PG_USER}" "${SCRATCH_DB}"
createdb -U "${PG_USER}" "${SCRATCH_DB}"
pg_dump -U "${PG_USER}" -s "${PG_DB}" | psql -U "${PG_USER}" -q "${SCRATCH_DB}" >/dev/null

SCRATCH_URL="postgresql+asyncpg://${PG_USER}@127.0.0.1:5432/${SCRATCH_DB}"
DATABASE_URL="${SCRATCH_URL}" "${APP_DIR}/.venv/bin/alembic" upgrade head

log "Migration validated cleanly. Cleaning up scratch DB…"
dropdb -U "${PG_USER}" "${SCRATCH_DB}"

# --------------------------------------------------------------------------
# Apply for real
# --------------------------------------------------------------------------
log "Applying migration to ${PG_DB}…"
"${APP_DIR}/.venv/bin/alembic" upgrade head

log "Restarting web service…"
systemctl --user restart fme-train-web.service

# --------------------------------------------------------------------------
# Verify
# --------------------------------------------------------------------------
sleep 2
log "Health check…"
HTTP_STATUS="$(curl -s -o /dev/null -w '%{http_code}' http://127.0.0.1:8000/health)"
if [[ "${HTTP_STATUS}" != "200" ]]; then
  echo "[deploy] /health returned ${HTTP_STATUS}; check journalctl --user -u fme-train-web -n 100" >&2
  echo "[deploy] To rollback:" >&2
  echo "  cd ${APP_DIR} && git reset --hard ${PREV_SHA} && systemctl --user restart fme-train-web" >&2
  exit 1
fi

log "Deploy complete: ${PREV_SHA} → ${NEW_SHA}"
log "If anything goes wrong in the next few minutes, rollback with:"
log "  cd ${APP_DIR} && git reset --hard ${PREV_SHA} && systemctl --user restart fme-train-web"
