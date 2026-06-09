#!/usr/bin/env bash
# bin/deploy-prod.sh — apply a new revision to the running EC2 instance.
#
# Designed to run unattended from GitHub Actions (KNOW-2293). Hardened with
# pre/post health gates, atomic checkout, conditional pip install, scratch-DB
# migration validation, last-good-SHA tracking, and automatic rollback on a
# failed post-deploy health check.
#
# Reference:
#   docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md
#   KNOW-2296 (this script)
#   KNOW-2293 (GH Actions workflow that invokes this script over SSH)
#
# Usage:
#   ./bin/deploy-prod.sh [<git-ref>]   # default ref is main
#   ./bin/deploy-prod.sh --rollback    # explicit rollback to last-good SHA
#   ./bin/deploy-prod.sh -h | --help
#
# Env overrides (all have defaults):
#   APP_DIR              install location              (default: /opt/fme-train)
#   ENV_FILE             secrets file                  (default: /etc/fme-train/env)
#   STATE_DIR            persistent state              (default: /var/lib/fme-train,
#                                                       falls back to ~/.local/state/fme-train
#                                                       if not writable)
#   HEALTH_URL           health endpoint               (default: http://127.0.0.1:8000/health)
#   POST_DEPLOY_TIMEOUT  seconds to wait post-restart  (default: 20)
#   PG_DB                main DB name                  (default: fme_train)
#   PG_USER              DB role                       (default: fmetrain)
#   SCRATCH_DB           name of scratch DB            (default: fme_train_migration_check)
#   DEPLOY_DRY_RUN       1 = swap systemctl/curl for   (default: 0)
#                            echo, skip state writes,
#                            don't require the env file
#
# Logging: every meaningful step prints a single `[deploy] …` line so journalctl
# is easy to follow. Errors go to stderr with a `[deploy] ERROR:` prefix.

set -euo pipefail

# --------------------------------------------------------------------------
# Argument parsing
# --------------------------------------------------------------------------
ROLLBACK=0
REF="main"

case "${1:-}" in
  -h|--help)
    sed -n '1,40p' "$0" | sed 's/^# \{0,1\}//'
    exit 0
    ;;
  --rollback)
    ROLLBACK=1
    ;;
  "")
    REF="main"
    ;;
  *)
    REF="$1"
    ;;
esac

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
APP_DIR="${APP_DIR:-/opt/fme-train}"
ENV_FILE="${ENV_FILE:-/etc/fme-train/env}"
STATE_DIR="${STATE_DIR:-/var/lib/fme-train}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8000/health}"
POST_DEPLOY_TIMEOUT="${POST_DEPLOY_TIMEOUT:-20}"
PG_DB="${PG_DB:-fme_train}"
PG_USER="${PG_USER:-fmetrain}"
SCRATCH_DB="${SCRATCH_DB:-fme_train_migration_check}"
DEPLOY_DRY_RUN="${DEPLOY_DRY_RUN:-0}"

log()  { printf '[deploy] %s\n' "$*"; }
warn() { printf '[deploy] WARN: %s\n' "$*" >&2; }
die()  { printf '[deploy] ERROR: %s\n' "$*" >&2; exit 1; }

# --------------------------------------------------------------------------
# Wrappers — substituted in dry-run so the script can be smoke-tested locally
# without a real systemd, running app, or /var/lib/ access.
# --------------------------------------------------------------------------
run_systemctl() {
  if [[ "${DEPLOY_DRY_RUN}" == "1" ]]; then
    log "DRY-RUN: would run: systemctl --user $*"
    return 0
  fi
  systemctl --user "$@"
}

# Returns 0 on healthy, non-zero otherwise. In dry-run, always healthy.
run_curl_health() {
  if [[ "${DEPLOY_DRY_RUN}" == "1" ]]; then
    log "DRY-RUN: would curl ${HEALTH_URL}"
    return 0
  fi
  curl -sf -o /dev/null "${HEALTH_URL}"
}

# write_state <filename> <content>
write_state() {
  local name="$1"
  local content="$2"
  if [[ "${DEPLOY_DRY_RUN}" == "1" ]]; then
    log "DRY-RUN: would write '${content}' to ${STATE_DIR}/${name}"
    return 0
  fi
  printf '%s\n' "${content}" > "${STATE_DIR}/${name}"
}

# Detect whether a user-mode systemd unit exists. Returns 0 if it does.
unit_exists() {
  local unit="$1"
  if [[ "${DEPLOY_DRY_RUN}" == "1" ]]; then
    # In dry-run, pretend the web unit exists, scheduler does not — exercises
    # both branches of the restart helper in the smoke test.
    [[ "${unit}" == "fme-train-web.service" ]]
    return $?
  fi
  systemctl --user list-unit-files --no-legend --no-pager "${unit}" \
    2>/dev/null | grep -q "^${unit}"
}

# Restart fme-train-web (always, must exist) and fme-train-scheduler (if
# present; KNOW-2296 carries this forward-compatible no-op until the
# scheduler unit is added in a follow-up). Worker units are explicitly
# NOT touched — in-flight pipeline runs continue on old code.
restart_services() {
  log "restarting fme-train-web.service"
  run_systemctl restart fme-train-web.service

  if unit_exists fme-train-scheduler.service; then
    log "restarting fme-train-scheduler.service"
    run_systemctl restart fme-train-scheduler.service
  else
    log "fme-train-scheduler.service not present, skipping (worker units left alone by design)"
  fi
}

# Poll /health until 200 OK or timeout. Returns 0 on healthy, 1 on timeout.
wait_for_health() {
  local timeout="$1"
  local elapsed=0
  while (( elapsed < timeout )); do
    if run_curl_health; then
      log "post-deploy health check OK after ${elapsed}s"
      return 0
    fi
    sleep 1
    elapsed=$(( elapsed + 1 ))
  done
  return 1
}

# --------------------------------------------------------------------------
# Environment + working directory
# --------------------------------------------------------------------------
load_env_file() {
  if [[ -r "${ENV_FILE}" ]]; then
    set -a
    # shellcheck disable=SC1090
    source "${ENV_FILE}"
    set +a
    log "loaded env from ${ENV_FILE}"
  elif [[ "${DEPLOY_DRY_RUN}" == "1" ]]; then
    log "DRY-RUN: ${ENV_FILE} not readable, continuing without env (smoke test)"
  else
    echo "[deploy] ERROR: cannot read ${ENV_FILE} as $(whoami)." >&2
    echo "[deploy] Fix with: sudo chgrp $(whoami) ${ENV_FILE} && sudo chmod 0640 ${ENV_FILE}" >&2
    exit 2
  fi

  if [[ -z "${DATABASE_URL:-}" && "${DEPLOY_DRY_RUN}" != "1" ]]; then
    die "DATABASE_URL is not set in ${ENV_FILE}"
  fi
}

ensure_state_dir() {
  if [[ "${DEPLOY_DRY_RUN}" == "1" ]]; then
    log "DRY-RUN: skipping STATE_DIR provisioning (would have used ${STATE_DIR})"
    return 0
  fi
  if mkdir -p "${STATE_DIR}" 2>/dev/null && [[ -w "${STATE_DIR}" ]]; then
    log "state dir: ${STATE_DIR}"
    return 0
  fi
  warn "${STATE_DIR} is not writable; falling back to ~/.local/state/fme-train"
  warn "follow-up: extend setup-ec2.sh to provision ${STATE_DIR} (KNOW-2296 deferred)"
  STATE_DIR="${HOME}/.local/state/fme-train"
  mkdir -p "${STATE_DIR}"
  log "state dir: ${STATE_DIR} (fallback)"
}

# `systemctl --user` needs the running user's bus path. Direct ssh logins get
# this from PAM, but `sudo -u fmetrain bash deploy-prod.sh` does not. Set it
# unconditionally — harmless if already correct. Skipped under dry-run.
if [[ "${DEPLOY_DRY_RUN}" != "1" ]]; then
  XDG_RUNTIME_DIR="/run/user/$(id -u)"
  export XDG_RUNTIME_DIR
fi

load_env_file

if [[ "${DEPLOY_DRY_RUN}" == "1" && ! -d "${APP_DIR}" ]]; then
  die "DEPLOY_DRY_RUN=1 but APP_DIR=${APP_DIR} does not exist; smoke test must point APP_DIR at a fixture"
fi
cd "${APP_DIR}"

ensure_state_dir

# --------------------------------------------------------------------------
# Forward deploy (default) and rollback (--rollback) share most steps.
# Pull them out into functions so the rollback path can be reused by the
# auto-rollback at the end of the forward path.
# --------------------------------------------------------------------------
install_requirements_if_changed() {
  local req_file="${APP_DIR}/requirements.txt"
  local hash_file="${STATE_DIR}/requirements.sha256"
  local current_hash stored_hash=""

  if [[ ! -f "${req_file}" ]]; then
    warn "no requirements.txt at ${req_file}; skipping pip"
    return 0
  fi

  current_hash="$(sha256sum "${req_file}" | awk '{print $1}')"
  if [[ -f "${hash_file}" ]]; then
    stored_hash="$(cat "${hash_file}")"
  fi

  if [[ "${current_hash}" == "${stored_hash}" ]]; then
    log "requirements.txt unchanged (sha256=${current_hash:0:12}…), skipping pip install"
    return 0
  fi

  log "requirements.txt changed; installing"
  if [[ "${DEPLOY_DRY_RUN}" == "1" ]]; then
    log "DRY-RUN: would run: ${APP_DIR}/.venv/bin/pip install -q -r ${req_file}"
  else
    "${APP_DIR}/.venv/bin/pip" install -q --upgrade pip
    "${APP_DIR}/.venv/bin/pip" install -q -r "${req_file}"
  fi
  write_state requirements.sha256 "${current_hash}"
  log "pip install complete; recorded hash"
}

# Validate the migration on a scratch DB before touching prod. If this fails,
# prod is untouched and the script exits non-zero before any service restart.
# Skipped in dry-run (no Postgres on the smoke-test box).
validate_migration_against_scratch_db() {
  if [[ "${DEPLOY_DRY_RUN}" == "1" ]]; then
    log "DRY-RUN: would validate alembic upgrade head against scratch DB ${SCRATCH_DB}"
    return 0
  fi

  log "validating migration against scratch DB ${SCRATCH_DB}"
  dropdb --if-exists -U "${PG_USER}" "${SCRATCH_DB}"
  createdb -U "${PG_USER}" "${SCRATCH_DB}"
  pg_dump -U "${PG_USER}" -s "${PG_DB}" | psql -U "${PG_USER}" -q "${SCRATCH_DB}" >/dev/null

  # Derive scratch URL from prod DATABASE_URL so it inherits the password.
  local scratch_url="${DATABASE_URL%/*}/${SCRATCH_DB}"
  if ! DATABASE_URL="${scratch_url}" "${APP_DIR}/.venv/bin/alembic" upgrade head; then
    dropdb --if-exists -U "${PG_USER}" "${SCRATCH_DB}" || true
    die "scratch-DB alembic upgrade failed; prod untouched, services NOT restarted"
  fi

  log "scratch-DB migration validated"
  dropdb -U "${PG_USER}" "${SCRATCH_DB}"
}

apply_migration_to_prod() {
  if [[ "${DEPLOY_DRY_RUN}" == "1" ]]; then
    log "DRY-RUN: would run: alembic upgrade head against ${PG_DB}"
    return 0
  fi
  log "applying migration to ${PG_DB}"
  if ! "${APP_DIR}/.venv/bin/alembic" upgrade head; then
    die "alembic upgrade head FAILED on prod DB; services NOT restarted"
  fi
  log "migration applied"
}

do_rollback() {
  log "rollback path: reading ${STATE_DIR}/last-good-sha"
  local last_good=""
  if [[ "${DEPLOY_DRY_RUN}" == "1" ]]; then
    last_good="dryrunshadeadbeefdeadbeefdeadbeefdeadbeef"
    log "DRY-RUN: pretending last-good SHA is ${last_good}"
  else
    if [[ ! -s "${STATE_DIR}/last-good-sha" ]]; then
      die "no last-good-sha recorded at ${STATE_DIR}/last-good-sha; cannot auto-rollback"
    fi
    last_good="$(cat "${STATE_DIR}/last-good-sha")"
  fi

  log "rolling back to ${last_good}"
  if [[ "${DEPLOY_DRY_RUN}" != "1" ]]; then
    git fetch origin
    if ! git rev-parse --verify --quiet "${last_good}^{commit}" >/dev/null; then
      die "last-good SHA ${last_good} not present in local repo after fetch"
    fi
    git reset --hard "${last_good}"
  fi

  warn "alembic does not auto-detect non-reversible migrations; manual DB cleanup may be needed if the rollback target's schema differs"
  apply_migration_to_prod
  restart_services

  log "rollback post-restart health check (5s)"
  if wait_for_health 5; then
    log "rollback complete: services healthy on ${last_good}"
  else
    warn "rollback restarted services but /health still not 200 — page an operator"
  fi
  # Intentionally NOT updating last-good-sha — rollback target is by definition
  # the previously-known-good SHA.
}

do_forward_deploy() {
  log "starting forward deploy of ref=${REF} (DEPLOY_DRY_RUN=${DEPLOY_DRY_RUN})"

  log "pre-deploy health check"
  if ! run_curl_health; then
    die "pre-deploy /health did not return 200; refusing to proceed"
  fi
  log "pre-deploy health check OK"

  local prev_sha
  prev_sha="$(git rev-parse HEAD)"
  log "current revision: ${prev_sha}"

  log "fetching origin"
  git fetch origin

  log "validating ref origin/${REF}"
  if ! git rev-parse --verify --quiet "origin/${REF}" >/dev/null; then
    die "origin/${REF} does not exist after fetch"
  fi

  log "atomic checkout to origin/${REF}"
  git reset --hard "origin/${REF}"
  local new_sha
  new_sha="$(git rev-parse HEAD)"
  log "new revision: ${new_sha}"

  install_requirements_if_changed

  validate_migration_against_scratch_db
  apply_migration_to_prod

  restart_services

  log "polling /health for up to ${POST_DEPLOY_TIMEOUT}s"
  if ! wait_for_health "${POST_DEPLOY_TIMEOUT}"; then
    warn "post-deploy /health never returned 200 within ${POST_DEPLOY_TIMEOUT}s — auto-rolling back"
    do_rollback || warn "rollback also failed — manual intervention required"
    die "post-deploy health check failed; rollback attempted; deploy considered FAILED"
  fi

  write_state last-good-sha "${new_sha}"
  log "deploy complete: ${prev_sha} -> ${new_sha} (wall: ${SECONDS}s)"
}

# --------------------------------------------------------------------------
# Entrypoint
# --------------------------------------------------------------------------
if (( ROLLBACK )); then
  do_rollback
  exit 0
fi

do_forward_deploy
