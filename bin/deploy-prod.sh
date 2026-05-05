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
ENV_FILE="${ENV_FILE:-/etc/fme-train/env}"

log() { printf '\n[deploy] %s\n' "$*"; }

# `systemctl --user` needs the running user's bus path. Direct ssh logins
# get this from PAM, but `sudo -u fmetrain bash deploy-prod.sh` does not.
# Set it here unconditionally — harmless if already correct.
export XDG_RUNTIME_DIR="/run/user/$(id -u)"

# Production DATABASE_URL lives in the root-owned env file. The real
# alembic upgrade below needs to read it. setup-ec2.sh writes the file
# with chmod 0600 / root-only by default — for this script to work, the
# file must be readable by the deploy user. Recommended pattern:
#     sudo chgrp fmetrain /etc/fme-train/env
#     sudo chmod 0640 /etc/fme-train/env
# So root + fmetrain (and only those) can read it.
if [[ -r "${ENV_FILE}" ]]; then
  # shellcheck disable=SC1090
  set -a; source "${ENV_FILE}"; set +a
else
  echo "[deploy] Cannot read ${ENV_FILE} as $(whoami)." >&2
  echo "[deploy] Fix with: sudo chgrp $(whoami) ${ENV_FILE} && sudo chmod 0640 ${ENV_FILE}" >&2
  exit 2
fi

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "[deploy] DATABASE_URL is not set in ${ENV_FILE}." >&2
  exit 2
fi

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
# DATABASE_URL is exported above from ${ENV_FILE}; alembic uses it via
# the env-driven URL set in alembic.ini at runtime.
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
