# Handoff — KNOW-2263 live QA (resume after devcontainer rebuild)

**Written:** 2026-06-05 by the prior Claude Code session, for the next session.
**User:** Sam Walker (sam.walker@safe.com). **Branch:** `feature/multi-user-web-app` (integration branch — QA happens here, NOT per-ticket branches).

## Why this file exists
The user rebuilt the devcontainer to enable Docker (docker-in-docker was just added). The rebuild wipes my conversation context but not the repo or `~/.claude` memory. This is the state + plan to continue.

## Context (what we're doing)
QA-ing the multi-user web app epic **KNOW-2257**, in dependency order. Corrected order: **KNOW-2263 (Docker/Compose+Postgres) → KNOW-2260 (models/Alembic) → KNOW-2259 (auth) → 2261/2271/2273 → 2277 → 2275/2279 → 2293/2296.** We are mid-QA on **KNOW-2263**.

## Already done this session (all pushed)
- Commit `48ce0b33` — added `ghcr.io/devcontainers/features/docker-in-docker:2` to `.devcontainer/devcontainer.json`.
- Commit `7633d04a` — KNOW-2263 fixes: (1) mount `./tests:/app/tests:ro` in the `app` service so containerized `make test` can collect tests; (2) renamed `.env.compose` `SESSION_SECRET` → `SESSION_SIGNING_KEY` (app reads the latter; wrong name silently disabled auth).
- Jira: rewrote **KNOW-2260** + **KNOW-2263** descriptions; filed **KNOW-2310** (deferred ephemeral-Postgres CRUD test, linked to 2260); QA comments on KNOW-2263 and KNOW-2259; PR #3 body refreshed.

## Static QA verdict for KNOW-2263
2 defects found + fixed (above). Healthchecks, startup ordering, non-root user, S3 bucket-name match, port 8000 all verified sound. Host test suite: **346 passed / 1 skipped / 1 failed**. The 1 failure is `tests/integration/test_auth.py::test_auth_login_returns_503_when_google_misconfigured` — a **non-hermetic test** (KNOW-2259 issue, NOT a 2263 defect); it passes when Google creds are unset. It will also show up in containerized `make test` because `.env.compose` ships a truthy placeholder `GOOGLE_OAUTH_CLIENT_ID`. Already documented on KNOW-2259.

## RESUME HERE — live run (needs Docker, now available post-rebuild)

First confirm the env, then run the stack:

1. `which docker && docker version` — confirm Docker is now available (it was NOT before the rebuild).
2. `cd /workspaces/fme-training-automation && git log --oneline -3` — expect HEAD at `7633d04a` (or later). `git pull` if needed.
3. `make up` then `make ps` → all services (`app`, `postgres`, `minio`, `minio-init`) healthy within ~30s. If a build is needed it runs automatically; `make logs` to watch.
4. Health check: hit `/health` on **port 8000** (`curl http://localhost:8000/health` → 200). NOTE: 8000 is canonical; if VS Code forwards to 8001 because host 8000 is busy, use whatever the Ports panel shows — 8001 is just a forwarding artifact, never a config value.
5. `make migrate` (`docker compose run --rm app alembic upgrade head`) → migrations apply cleanly. This also covers KNOW-2260's migration acceptance against a real Postgres.
6. `make worker` (`docker compose run --rm worker-runner`) → worker boots, connects to Postgres, exits 0. With no queued run it should find no work and exit cleanly; seed a run for the full path.
7. `make test` (`docker compose run --rm app pytest`) → expect the suite to run and collect tests now (D1 fix). Expect the **same 1 known auth-test failure** noted above — that's the KNOW-2259 non-hermetic test, not a 2263 regression.
8. (Optional) Trivy image scan → not installed in the devcontainer; install or run on a host that has it; treat as non-blocking.

## After the live run
- If steps 3–7 pass (modulo the known auth test), KNOW-2263 can move out of QA. Record results as a comment on KNOW-2263 via the Atlassian MCP.
- Then proceed to **KNOW-2260** live verification (its rewritten steps are in the ticket; `make migrate` from step 5 already exercises most of it), then **KNOW-2259**.

## Conventions / gotchas (from memory)
- Apply Jira edits via the Atlassian MCP directly (don't hand the user a proposed-edits list). Use AskUserQuestion for genuine decisions.
- File a KNOW Backlog **Story** for any deferred scope discovered while splitting work.
- Atlassian MCP edits can hit a Cloudflare WAF block if the body contains raw shell strings like `curl http://...` or `trivy image ...` — phrase commands as prose to avoid it.
- Cloud ID for the Atlassian MCP: `safesoftware.atlassian.net`.
- Do not read `./.env` (deny rule; secrets). `.env.compose` is committed dev defaults and safe to read.

## Delete this file when KNOW-2263 QA is signed off.
