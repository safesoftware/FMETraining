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

case "${MODE}" in
    web)
        # uvicorn defaults are fine for a small internal app. --proxy-headers
        # so X-Forwarded-* from App Runner / ALB is honored once we deploy.
        exec uvicorn app.main:app \
            --host 0.0.0.0 \
            --port "${PORT:-8000}" \
            --proxy-headers \
            --forwarded-allow-ips='*'
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
