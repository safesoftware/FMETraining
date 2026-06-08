#!/usr/bin/env bash
# tests/test_deploy_script.sh — dry-run smoke test for bin/deploy-prod.sh.
#
# Sets up a throwaway git fixture, runs the deploy script with
# DEPLOY_DRY_RUN=1, and asserts that the expected log markers appear and
# the script exits 0.
#
# Runnable two ways:
#   1. Standalone: `bash tests/test_deploy_script.sh` from the repo root.
#   2. Via pytest: `python -m pytest tests/unit/test_deploy_script_smoke.py`
#      (the wrapper subprocess.run()s this script).
#
# Reference: KNOW-2296.

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT="${REPO_ROOT}/bin/deploy-prod.sh"

if [[ ! -x "${SCRIPT}" ]]; then
  echo "FAIL: ${SCRIPT} is not executable" >&2
  exit 1
fi

SMOKE_DIR="$(mktemp -d)"
trap 'rm -rf "${SMOKE_DIR}"' EXIT

# Build a fixture git repo. The deploy script does `git fetch origin && git
# reset --hard origin/<ref>`, so origin must be a reachable remote with the
# requested ref. Easiest: make the fixture its own origin.
APP_FIXTURE="${SMOKE_DIR}/app"
git init -q -b main "${APP_FIXTURE}"
(
  cd "${APP_FIXTURE}"
  git config user.email smoke@example.test
  git config user.name "smoke test"
  echo 'fastapi==0.111.0' > requirements.txt
  echo 'placeholder' > README.md
  git add . >/dev/null
  git commit -q -m "fixture initial commit"
  # Self-remote so `git fetch origin` resolves locally.
  git remote add origin "${APP_FIXTURE}"
  git fetch -q origin
)

STATE_FIXTURE="${SMOKE_DIR}/state"
mkdir -p "${STATE_FIXTURE}"
LOG="${SMOKE_DIR}/out.log"

# Run the script under dry-run with the fixture pinned via env.
set +e
DEPLOY_DRY_RUN=1 \
APP_DIR="${APP_FIXTURE}" \
STATE_DIR="${STATE_FIXTURE}" \
ENV_FILE="${SMOKE_DIR}/no-such-env" \
HEALTH_URL="http://127.0.0.1:9/health" \
"${SCRIPT}" main >"${LOG}" 2>&1
rc=$?
set -e

if (( rc != 0 )); then
  echo "FAIL: deploy-prod.sh exited ${rc} under DEPLOY_DRY_RUN=1" >&2
  echo "----- captured log -----" >&2
  cat "${LOG}" >&2
  exit 1
fi

# Required log markers — each one represents a meaningful step that must
# appear in journalctl on a real deploy. If any of these go missing, the
# operator will be debugging blind.
required=(
  '\[deploy\] starting forward deploy of ref=main'
  '\[deploy\] pre-deploy health check'
  '\[deploy\] pre-deploy health check OK'
  '\[deploy\] fetching origin'
  '\[deploy\] validating ref origin/main'
  '\[deploy\] atomic checkout to origin/main'
  '\[deploy\] DRY-RUN: would validate alembic upgrade head against scratch DB'
  '\[deploy\] DRY-RUN: would run: alembic upgrade head against'
  '\[deploy\] restarting fme-train-web.service'
  '\[deploy\] DRY-RUN: would run: systemctl --user restart fme-train-web.service'
  '\[deploy\] fme-train-scheduler.service not present, skipping'
  '\[deploy\] polling /health for up to'
  '\[deploy\] DRY-RUN: would write '"'"'.\+'"'"' to '"${STATE_FIXTURE}"'/last-good-sha'
  '\[deploy\] deploy complete:'
)

failed=0
for pattern in "${required[@]}"; do
  if ! grep -q -- "${pattern}" "${LOG}"; then
    echo "FAIL: missing log marker: ${pattern}" >&2
    failed=1
  fi
done

# Conditional pip install marker — on a fresh fixture (no requirements.sha256
# yet), it should run the install branch, NOT the skip branch.
if grep -q 'requirements.txt unchanged' "${LOG}"; then
  echo "FAIL: first-run smoke incorrectly hit the unchanged-requirements branch" >&2
  failed=1
fi
if ! grep -q 'requirements.txt changed; installing' "${LOG}"; then
  echo "FAIL: missing 'requirements.txt changed' marker" >&2
  failed=1
fi

# --rollback path: stash a fake last-good-sha, run with --rollback, expect
# exit 0 and rollback markers.
echo 'deadbeef1234567890abcdef1234567890abcdef' > "${STATE_FIXTURE}/last-good-sha"
ROLLBACK_LOG="${SMOKE_DIR}/rollback.log"
set +e
DEPLOY_DRY_RUN=1 \
APP_DIR="${APP_FIXTURE}" \
STATE_DIR="${STATE_FIXTURE}" \
ENV_FILE="${SMOKE_DIR}/no-such-env" \
HEALTH_URL="http://127.0.0.1:9/health" \
"${SCRIPT}" --rollback >"${ROLLBACK_LOG}" 2>&1
rb_rc=$?
set -e

if (( rb_rc != 0 )); then
  echo "FAIL: --rollback exited ${rb_rc}" >&2
  cat "${ROLLBACK_LOG}" >&2
  exit 1
fi

rollback_required=(
  '\[deploy\] rollback path: reading'
  '\[deploy\] rolling back to'
  '\[deploy\] DRY-RUN: would run: systemctl --user restart fme-train-web.service'
  '\[deploy\] rollback complete:'
)
for pattern in "${rollback_required[@]}"; do
  if ! grep -q -- "${pattern}" "${ROLLBACK_LOG}"; then
    echo "FAIL: missing rollback marker: ${pattern}" >&2
    failed=1
  fi
done

# Rollback must NOT write last-good-sha (the file we seeded must be untouched).
if grep -q "would write .* to ${STATE_FIXTURE}/last-good-sha" "${ROLLBACK_LOG}"; then
  echo "FAIL: rollback path attempted to update last-good-sha (it must not)" >&2
  failed=1
fi

if (( failed )); then
  echo "----- forward log -----" >&2
  cat "${LOG}" >&2
  echo "----- rollback log -----" >&2
  cat "${ROLLBACK_LOG}" >&2
  exit 1
fi

echo "deploy-prod.sh smoke test OK"
