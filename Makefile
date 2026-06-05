# Makefile — thin wrappers around docker compose for the local dev stack.
# Owned by KNOW-2263. Run `make help` to see what's available.

# Make sure `make` lints/tests inside the venv-backed containers, not the
# host. Each target is intentionally 1-3 lines.

SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

# Stamp every build with the current git SHA so images are traceable.
GIT_SHA  ?= $(shell git rev-parse --short HEAD 2>/dev/null || echo local)
BUILD_DATE ?= $(shell date -u +%Y-%m-%dT%H:%M:%SZ)
COMPOSE := GIT_SHA=$(GIT_SHA) BUILD_DATE=$(BUILD_DATE) docker compose

.PHONY: help build up up-mail down logs ps shell migrate test lint format clean nuke

help: ## Show this help.
	@awk 'BEGIN { FS = ":.*##"; printf "Targets:\n" } \
		/^[a-zA-Z_-]+:.*?##/ { printf "  \033[36m%-12s\033[0m %s\n", $$1, $$2 }' \
		$(MAKEFILE_LIST)

build: ## Build the app image (tagged with git SHA via build args).
	$(COMPOSE) build

up: ## Start the full stack (app + postgres + minio).
	$(COMPOSE) up -d
	@echo "App:        http://localhost:8000"
	@echo "MinIO API:  http://localhost:9000  (minioadmin/minioadmin)"
	@echo "MinIO UI:   http://localhost:9001"

up-mail: ## Start the full stack including the mailhog SMTP catcher.
	$(COMPOSE) --profile mail up -d

down: ## Stop the stack but keep volumes.
	$(COMPOSE) down

logs: ## Tail logs from every service.
	$(COMPOSE) logs -f

ps: ## Show service status.
	$(COMPOSE) ps

shell: ## Open a bash shell inside the running app container.
	$(COMPOSE) exec app /bin/bash

migrate: ## Run alembic migrations against the local postgres.
	$(COMPOSE) run --rm app alembic upgrade head

test: ## Run pytest inside the app container.
	$(COMPOSE) run --rm app pytest

# RUFF_CACHE_DIR points at a writable tmp path: the non-root app user can't
# write the default /app/.ruff_cache (WORKDIR is owned by appuser but the
# mounted source tree is owned by the host user).
lint: ## Run ruff inside the app container.
	$(COMPOSE) run --rm -e RUFF_CACHE_DIR=/tmp/ruff-cache app ruff check .

format: ## Run ruff format inside the app container.
	$(COMPOSE) run --rm -e RUFF_CACHE_DIR=/tmp/ruff-cache app ruff format .

worker: ## Run a one-shot worker (`docker compose run worker-runner`).
	$(COMPOSE) run --rm worker-runner

clean: ## Stop the stack and remove containers (keeps volumes).
	$(COMPOSE) down --remove-orphans

nuke: ## Stop the stack and remove containers AND volumes (data loss!).
	$(COMPOSE) down -v --remove-orphans
