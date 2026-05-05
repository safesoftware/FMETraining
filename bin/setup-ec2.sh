#!/usr/bin/env bash
# bin/setup-ec2.sh — idempotent provisioner for the single-EC2 deployment.
#
# Run this once on a fresh Amazon Linux 2023 instance. It installs Postgres,
# Nginx, Python, the application code, and wires up the systemd units that
# run the FastAPI app + per-run pipeline workers as the unprivileged
# `fmetrain` user. Re-running it on an already-provisioned box is a no-op
# (idempotent).
#
# Reference: docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md
#
# Usage (run as root or via sudo):
#   sudo bin/setup-ec2.sh
#
# Inputs (override via env):
#   APP_USER       — user that owns the application (default: fmetrain)
#   APP_DIR        — install location (default: /opt/fme-train)
#   ENV_FILE       — secrets file (default: /etc/fme-train/env)
#   APP_REPO_URL   — git URL to clone from (default: read from origin of cwd)
#   APP_REF        — git ref to check out (default: main)
#   PG_DB          — Postgres database name (default: fme_train)
#   PG_USER        — Postgres role (default: fmetrain)

set -euo pipefail

APP_USER="${APP_USER:-fmetrain}"
APP_DIR="${APP_DIR:-/opt/fme-train}"
ENV_FILE="${ENV_FILE:-/etc/fme-train/env}"
APP_REF="${APP_REF:-main}"
PG_DB="${PG_DB:-fme_train}"
PG_USER="${PG_USER:-fmetrain}"
APP_REPO_URL="${APP_REPO_URL:-}"
# Nginx server_name. certbot --nginx pattern-matches against this when
# inserting the TLS redirect, so it must match the public DNS name —
# `_` (catch-all) confuses certbot.
SERVER_NAME="${SERVER_NAME:-fme-train.safe.com}"

log() { printf '\n[setup] %s\n' "$*"; }

if [[ $EUID -ne 0 ]]; then
  echo "setup-ec2.sh must be run as root (try: sudo $0)" >&2
  exit 1
fi

# --------------------------------------------------------------------------
# 1. OS packages
# --------------------------------------------------------------------------
log "Installing system packages…"
dnf install -y --allowerasing \
  git \
  python3.11 python3.11-pip \
  postgresql16-server postgresql16 postgresql16-contrib \
  nginx \
  certbot python3-certbot-nginx \
  jq curl

# --------------------------------------------------------------------------
# 2. Postgres
# --------------------------------------------------------------------------
log "Initialising Postgres if not yet initialised…"
if [[ ! -d /var/lib/pgsql/data/base ]]; then
  /usr/bin/postgresql-setup --initdb
fi
systemctl enable --now postgresql

# Ensure the env-file directory exists *before* we try to drop the
# generated DATABASE_URL into it (.new sidecar).
install -d -o root -g root -m 0755 "$(dirname "${ENV_FILE}")"

log "Ensuring Postgres role + database exist…"
sudo -iu postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='${PG_USER}'" | grep -q 1 || {
  PG_PASS="$(openssl rand -hex 24)"
  sudo -iu postgres psql -c "CREATE ROLE ${PG_USER} LOGIN PASSWORD '${PG_PASS}'"
  # Write the candidate URL to a sidecar file with the same lock-down as
  # the real env file. Default umask would leave this 0644 — readable by
  # every user on the box. Force 0600 + root ownership before the
  # password is ever written into it.
  install -m 0600 -o root -g root /dev/null "${ENV_FILE}.new"
  printf '\n# Postgres password set during setup-ec2.sh — regenerate with `ALTER ROLE %s WITH PASSWORD ...` if rotated.\nDATABASE_URL=postgresql+asyncpg://%s:%s@127.0.0.1:5432/%s\n' \
    "${PG_USER}" "${PG_USER}" "${PG_PASS}" "${PG_DB}" >> "${ENV_FILE}.new"
}
sudo -iu postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='${PG_DB}'" | grep -q 1 || \
  sudo -iu postgres createdb -O "${PG_USER}" "${PG_DB}"

# --------------------------------------------------------------------------
# 3. App user + directory
# --------------------------------------------------------------------------
log "Ensuring application user '${APP_USER}' exists…"
id -u "${APP_USER}" &>/dev/null || \
  useradd --system --create-home --home-dir "/home/${APP_USER}" --shell /bin/bash "${APP_USER}"

# Allow the app user's systemd manager to keep running after logout.
loginctl enable-linger "${APP_USER}"

log "Ensuring ${APP_DIR} exists and is owned by ${APP_USER}…"
install -d -o "${APP_USER}" -g "${APP_USER}" -m 0755 "${APP_DIR}"

# --------------------------------------------------------------------------
# 4. Application source + venv
# --------------------------------------------------------------------------
if [[ -z "${APP_REPO_URL}" ]]; then
  if git -C "$(dirname "$0")/.." remote get-url origin &>/dev/null; then
    APP_REPO_URL="$(git -C "$(dirname "$0")/.." remote get-url origin)"
  else
    echo "APP_REPO_URL is not set and could not be inferred from git origin." >&2
    exit 2
  fi
fi

log "Cloning / updating application from ${APP_REPO_URL} (ref=${APP_REF})…"
if [[ ! -d "${APP_DIR}/.git" ]]; then
  sudo -u "${APP_USER}" git clone "${APP_REPO_URL}" "${APP_DIR}"
fi
sudo -u "${APP_USER}" git -C "${APP_DIR}" fetch origin
sudo -u "${APP_USER}" git -C "${APP_DIR}" reset --hard "origin/${APP_REF}"

log "Creating Python venv at ${APP_DIR}/.venv…"
sudo -u "${APP_USER}" python3.11 -m venv "${APP_DIR}/.venv"
sudo -u "${APP_USER}" "${APP_DIR}/.venv/bin/pip" install --upgrade pip
sudo -u "${APP_USER}" "${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt"

# --------------------------------------------------------------------------
# 5. Secrets file
#
# Directory was already created in section 2 (so the .new sidecar from
# the role-creation step had a place to land). Re-running install -d is
# a no-op when the dir already exists.
# --------------------------------------------------------------------------
install -d -o root -g root -m 0755 "$(dirname "${ENV_FILE}")"
if [[ ! -f "${ENV_FILE}" ]]; then
  log "Creating ${ENV_FILE} with placeholders. EDIT THIS BEFORE STARTING THE APP."
  cat > "${ENV_FILE}" <<'EOF'
# /etc/fme-train/env — EnvironmentFile for the systemd units.
# This file holds the only copy of production secrets on the box.
# chmod 600 is enforced; only root reads it directly. Systemd loads it.

# --- DB ---
# DATABASE_URL=postgresql+asyncpg://fmetrain:<password>@127.0.0.1:5432/fme_train
# (setup-ec2.sh wrote a candidate to /etc/fme-train/env.new — review and merge.)

# --- App identity / version ---
APP_VERSION=dev
ENVIRONMENT=production

# --- Auth ---
SESSION_SIGNING_KEY=
GOOGLE_OAUTH_CLIENT_ID=
GOOGLE_OAUTH_CLIENT_SECRET=

# --- External services ---
OPENAI_API_KEY=
JIRA_BASE_URL=
JIRA_USER=
JIRA_API_KEY=
JIRA_FILTER_ID=
SKILLJAR_API_KEY=
SKILLJAR_DOMAIN=

# --- AWS (image upload only) ---
AWS_ACCESS_KEY_ID=
AWS_SECRET_ACCESS_KEY=
AWS_S3_BUCKET=
AWS_S3_REGION=us-east-1

# --- Run guards ---
MAX_RUN_USD=50
RUN_CONCURRENCY=2
TASK_DISPATCHER=systemd
EOF
fi
# Permissions: root owns the file. The app user's group can read it so
# both systemd (root) and bin/deploy-prod.sh (running as fmetrain) can
# source it. World has no access.
chown "root:${APP_USER}" "${ENV_FILE}"
chmod 0640 "${ENV_FILE}"
# Same for the .new sidecar from the role-creation step, if it exists.
if [[ -f "${ENV_FILE}.new" ]]; then
  chown "root:${APP_USER}" "${ENV_FILE}.new"
  chmod 0640 "${ENV_FILE}.new"
fi

# --------------------------------------------------------------------------
# 6. systemd units — installed under the app user's user-mode systemd.
# --------------------------------------------------------------------------
USER_SYSTEMD_DIR="/home/${APP_USER}/.config/systemd/user"
install -d -o "${APP_USER}" -g "${APP_USER}" -m 0755 "${USER_SYSTEMD_DIR}"

log "Writing fme-train-web.service…"
cat > "${USER_SYSTEMD_DIR}/fme-train-web.service" <<EOF
[Unit]
Description=FME Training Automation web app (FastAPI)
After=network-online.target

[Service]
Type=simple
WorkingDirectory=${APP_DIR}
EnvironmentFile=${ENV_FILE}
ExecStartPre=${APP_DIR}/.venv/bin/alembic upgrade head
ExecStart=${APP_DIR}/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2
Restart=on-failure
RestartSec=5

[Install]
WantedBy=default.target
EOF
chown "${APP_USER}:${APP_USER}" "${USER_SYSTEMD_DIR}/fme-train-web.service"

log "Writing fme-train-worker@.service template…"
cat > "${USER_SYSTEMD_DIR}/fme-train-worker@.service" <<EOF
[Unit]
Description=FME Training Automation worker for run %i
After=network-online.target

[Service]
Type=oneshot
WorkingDirectory=${APP_DIR}
EnvironmentFile=${ENV_FILE}
Environment=RUN_ID=%i
ExecStart=${APP_DIR}/.venv/bin/python -m worker
StandardOutput=journal
StandardError=journal
EOF
chown "${APP_USER}:${APP_USER}" "${USER_SYSTEMD_DIR}/fme-train-worker@.service"

log "Reloading user systemd manager and enabling fme-train-web…"
sudo -u "${APP_USER}" XDG_RUNTIME_DIR=/run/user/$(id -u "${APP_USER}") \
  systemctl --user daemon-reload
sudo -u "${APP_USER}" XDG_RUNTIME_DIR=/run/user/$(id -u "${APP_USER}") \
  systemctl --user enable fme-train-web.service

# --------------------------------------------------------------------------
# 7. Nginx
# --------------------------------------------------------------------------
log "Writing nginx config (server_name=${SERVER_NAME})…"
# certbot --nginx looks for a server block whose server_name already
# contains the requested hostname so it can insert the TLS redirect +
# HTTPS block. A catch-all `_` confuses it. Use the real hostname.
cat > /etc/nginx/conf.d/fme-train.conf <<EOF
server {
  listen 80;
  listen [::]:80;
  server_name ${SERVER_NAME};

  # certbot --nginx will append the redirect + TLS block here.
  location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_set_header Host              \$host;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header X-Forwarded-For   \$remote_addr;
    proxy_read_timeout 300s;
    proxy_buffering off;  # SSE log streaming wants flushed writes
  }
}
EOF
nginx -t
systemctl enable --now nginx
systemctl reload nginx

# --------------------------------------------------------------------------
# Done
# --------------------------------------------------------------------------
log "Setup complete. Next steps:"
cat <<EOF

  1. Edit ${ENV_FILE} and fill in the empty values (a candidate
     DATABASE_URL was written to ${ENV_FILE}.new if Postgres was just set up).
  2. Start the web service:
       sudo -u ${APP_USER} XDG_RUNTIME_DIR=/run/user/\$(id -u ${APP_USER}) \\
         systemctl --user start fme-train-web
  3. Confirm /health responds locally:
       curl http://127.0.0.1:8000/health
  4. Once DNS for fme-train.<your-domain> points at this box, get a TLS cert:
       certbot --nginx -d fme-train.<your-domain>
  5. Deploy updates with bin/deploy-prod.sh.

EOF
