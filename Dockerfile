# syntax=docker/dockerfile:1.7
# ---------------------------------------------------------------------------
# Multi-stage Dockerfile for the FME Training Automation web app + worker.
# Owned by KNOW-2263 (Phase 0). Single image, dual-mode (web | worker)
# selected at runtime by ENTRYPOINT_MODE.
#
# Stage 1 (builder): install build deps, create a self-contained venv with
#                    requirements.txt resolved.
# Stage 2 (runtime): minimal slim image, copy venv + app source, drop privs
#                    to non-root appuser (UID 10001), HEALTHCHECK on /health.
# ---------------------------------------------------------------------------

# Pinned to a specific patch + Debian release so two builds a month apart
# can't silently pull a different Python or Debian package set. Bump this
# manually (or via Renovate / Dependabot) when a new patch ships. To pin
# more strictly you can replace this with a digest, e.g.
#   FROM python@sha256:<digest> AS builder
ARG PYTHON_VERSION=3.11.13-slim-bookworm

# ============================================================================
# Stage 1 — builder
# ============================================================================
FROM python:${PYTHON_VERSION} AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Build deps for any wheels that need to compile from source (lxml, pandas,
# etc.). gcc/g++/libxml2/libxslt cover the current requirements.txt set.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        build-essential \
        gcc \
        g++ \
        libxml2-dev \
        libxslt1-dev \
        libffi-dev \
        zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

# Self-contained venv at /opt/venv so the runtime stage can copy a single
# directory and not need pip at all.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Install dependencies in a separate layer for caching. requirements.txt is
# owned by KNOW-2258 / KNOW-2260; we only consume it.
COPY requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip \
 && pip install -r /tmp/requirements.txt

# ============================================================================
# Stage 2 — runtime
# ============================================================================
FROM python:${PYTHON_VERSION} AS runtime

ARG GIT_SHA=unknown
ARG BUILD_DATE=unknown

LABEL org.opencontainers.image.title="fme-training-automation" \
      org.opencontainers.image.description="FastAPI web + Fargate worker for the FME Training Automation pipeline" \
      org.opencontainers.image.source="https://github.com/safesoftware/fme-training-automation" \
      org.opencontainers.image.revision="${GIT_SHA}" \
      org.opencontainers.image.created="${BUILD_DATE}" \
      org.opencontainers.image.licenses="Proprietary"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PATH="/opt/venv/bin:${PATH}" \
    GIT_SHA="${GIT_SHA}" \
    ENTRYPOINT_MODE=web \
    PORT=8000

# Runtime libs only — no compilers. curl is used by HEALTHCHECK and lets ops
# poke at the service from inside the container; tini gives us PID 1
# signal-handling so cancellation works cleanly.
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        curl \
        tini \
        libxml2 \
        libxslt1.1 \
        ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Non-root user. UID 10001 is well above any host system UIDs and matches
# the convention in the multi-user web app plan.
RUN groupadd --system --gid 10001 appuser \
 && useradd  --system --uid 10001 --gid appuser --home /app --shell /usr/sbin/nologin appuser

# Copy the resolved venv from the builder stage.
COPY --from=builder /opt/venv /opt/venv

WORKDIR /app

# Copy app source. .dockerignore strips out the lesson content trees,
# artifacts/, data/, tests/, infra/, and other agents' build noise.
# We use --chown so the runtime user owns its own working tree.
COPY --chown=appuser:appuser . /app

# Entrypoint script. Copied separately so we can chmod +x without churning
# the (much larger) source-copy layer above.
COPY --chown=appuser:appuser docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 0755 /usr/local/bin/entrypoint.sh

# Pre-create a writable cache dir owned by the runtime user. At runtime the
# Compose bind-mounts leave the /app dir node root-owned, so appuser cannot
# create /app/.cache itself. The Jira API cache (pipeline/config.py
# JIRA_CACHE_PATH = REPO_ROOT/.cache/...) lives here and step 2 (changelog)
# crashes with PermissionError without it. See KNOW-2352.
RUN mkdir -p /app/.cache && chown appuser:appuser /app/.cache

USER appuser

EXPOSE 8000

# /health is provided by the FastAPI app (KNOW-2258). Until that ticket
# lands the healthcheck will return curl exit 22 (404). docker-compose's
# start_period gives 2258 room to come up; in production we expect 200.
HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD curl --fail --silent --show-error \
        "http://127.0.0.1:${PORT:-8000}/health" || exit 1

# tini forwards signals from docker stop / ECS task stop into the python
# process, which is what we need for graceful cancellation in worker mode.
ENTRYPOINT ["/usr/bin/tini", "--", "/usr/local/bin/entrypoint.sh"]
