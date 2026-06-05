#!/usr/bin/env bash
# docker/entrypoint.sh — dual-mode container entrypoint.
#
# ENTRYPOINT_MODE=web     -> launch FastAPI via uvicorn (KNOW-2258 owns app/main.py)
# ENTRYPOINT_MODE=worker  -> run the pipeline worker once and exit
#
# Owned by KNOW-2263.

set -euo pipefail

MODE="${ENTRYPOINT_MODE:-web}"

# Surface basic identity in startup logs so we can confirm which image / mode
# is running. GIT_SHA is baked at build time; fall back to "unknown".
echo "[entrypoint] mode=${MODE} git_sha=${GIT_SHA:-unknown} python=$(python --version 2>&1)"

# If an explicit command was passed to the container, run it instead of the
# ENTRYPOINT_MODE default. This is what lets `docker compose run app <cmd>`
# (i.e. `make migrate` / `make test` / `make lint` / `make format`) actually
# execute <cmd>. The `app` and `worker-runner` services pass no command and so
# fall through to the mode dispatch below.
if [ "$#" -gt 0 ]; then
    exec "$@"
fi

case "${MODE}" in
    web)
        # uvicorn defaults are fine for a small internal app. --proxy-headers
        # so X-Forwarded-* from App Runner / ALB is honored once we deploy.
        #
        # FORWARDED_ALLOW_IPS is the set of upstream IPs we trust to set
        # X-Forwarded-* headers. Defaults to loopback only — production
        # deploys MUST set this to the actual proxy CIDR (e.g. the App
        # Runner / ALB private subnet) via env var or Secrets Manager.
        # Local dev with Compose can set it to "*" in .env.compose since
        # there is no real proxy in front of the container.
        exec uvicorn app.main:app \
            --host 0.0.0.0 \
            --port "${PORT:-8000}" \
            --proxy-headers \
            --forwarded-allow-ips="${FORWARDED_ALLOW_IPS:-127.0.0.1}"
        ;;
    worker)
        # The Fargate worker reads RUN_ID / RESUME / MAX_RUN_USD from env
        # (see plan section 3). `python -m worker` is the entrypoint that
        # KNOW-2261 will own; until then this command will fail loudly,
        # which is the desired behaviour.
        exec python -m worker
        ;;
    *)
        echo "[entrypoint] ERROR: unknown ENTRYPOINT_MODE='${MODE}' (expected: web|worker)" >&2
        exit 64
        ;;
esac
