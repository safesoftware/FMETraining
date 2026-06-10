# Project state — single source of truth

> **Last updated:** 2026-06-10 (KNOW-2335 launch UI implemented; PR #29 draft).
> **What this is:** the always-current snapshot of *what is actually deployed, what is in
> flight, and what is next*. Read this **before starting any work** (see the reconcile ritual
> in `AGENTS.md`). It sits above the individual plan docs in `docs/plans/` — those describe
> *how*; this says *where we are*. Refresh it at every milestone (merge, deploy, ticket
> transition).

## Deployment state

| System | Branch / SHA | State | Notes |
|---|---|---|---|
| **EC2 production (the box)** | `b03710f8` (deployed 2026-06-10) | **LIVE on the full app** | Box `i-0389b1e00a2661746`, `fme-train.base.safe.com` (EIP `44.241.192.143`), us-west-2. Auth + TLS + DB + nightly backup up; OpenAI/Jira secrets loaded in `/etc/fme-train/env`. **A real pipeline job ran successfully on prod** → KNOW-2334/2335 verified live end-to-end. Post-deploy fixes (report `/artifacts` mount, launch-UI width, `setup-ec2.sh` artifacts dir, `deploy-prod.sh` scratch-DB validation) **fixed in code under KNOW-2340** — ⚠️ **redeploy `bin/deploy-prod.sh` to apply them on the box** (the box still runs `b03710f8` pre-fix). |
| **`main` (code)** | `b03710f8` | **Full launch-capable app, deployed** | KNOW-2334 (all 6 real pipeline steps + cost meter) and KNOW-2335 (launch UI + `POST /api/runs`) merged and **running on the box** — a signed-in `@safe.com` user launched a real run and the pipeline executed. |
| Local dev | Compose (`make up`) | Full app: FastAPI + Postgres 16 + minio + worker | `InProcessTaskDispatcher`; `LocalFolderSource` for content; minio = S3. This is where the agent runs functional QA. |

## Active work (ticket ↔ branch ↔ PR ↔ status ↔ plan ↔ next)

| Ticket | Branch | PR | Status | Plan | Next action |
|---|---|---|---|---|---|
| **KNOW-2334** real pipeline in worker | — (merged) | #26/#27/#28 merged | **Ready for QA** | build plan Part 2 | **All 6 steps real** + RunCostMeter + `/report/{run_id}`; `_stub_step_body` gone; `make test` green; launch→execute verified live (steps 1–2; 3/6 mocked-tested). QA: a real-OpenAI run (small scope). Follow-ups: `artifact_keys_json` (KNOW-2339), Postgres test harness (KNOW-2265). |
| **KNOW-2335** run-launch UI + endpoint | — (merged) | #29 merged | **Ready for QA** | build plan Part 2 | Merged. `POST /api/runs` + `GET /api/runs/*` + `/api/versions` + `/api/content-tree` + launch UI (signed-out sign-in link / signed-in form). Verified live: authed `POST /api/runs` → real run executed. QA: browser/UX pass. |
| **KNOW-2340** post-first-deploy fixes | `know-2340-post-deploy-fixes` | open | In Progress | — | Report `/artifacts` mount mkdir, launch-UI width (`.site-main` 1200px), `setup-ec2.sh` `/var/lib/fme-train/artifacts` + role `CREATEDB`, `deploy-prod.sh` scratch-DB `alembic_version` carry-over. `make test` green. Merge → redeploy. |
| **KNOW-2337** PROJECT-STATE + AGENTS ritual | — (merged) | #25 merged | Ready for QA | build plan Part 1 | Done/merged; awaiting close. |
| **KNOW-2333** `bin/setup-ec2.sh` fixes (exec bit, pg_hba) | — | — | In Backlog | cutover tracker | Fix in repo; bites next provision. |
| **KNOW-2330** give agent SSM box access | — | — | In Backlog (**IT/IAM-blocked**) | — | Folded into KNOW-2309 IAM ask. |
| **KNOW-2309** dedicated IAM + SSM | — | — | In Backlog (**IT-blocked**) | — | IT to create roles (DLM + SSM + app IAM). |
| **KNOW-2293** GH Actions deploy workflow | code on `main` | #17 closed-superseded | Ready for QA — **E2E blocked** | cutover tracker (B8) | Rework to SSM/self-hosted runner; runner can't reach office-IP box. |

## Recent merges

| PR | → | Date | Carried |
|---|---|---|---|
| #24 `migrate/ec2-prod-prep` | `main` (`e05f3e83`) | 2026-06-09 | Cutover Stages 1–6: full app + setup/deploy scripts + deploy workflow + host/TLS reconciliation + XSS fix |
| #6 `…KNOW-2275` | `main` (`8b2cc09d`) | 2026-06-08 | WYSIWYG lists |
| — (direct) | `main` (`ae7f8282`→`9a9d6e91`) | 2026-06-09/10 | Cutover progress tracker; stale deployment-comment fixes (salvaged from #15) |

**Closed without merge (superseded by the cutover on `main`):** PR #15 (KNOW-2295), #17 (KNOW-2293), #18 (KNOW-2296).

## Open blockers

- **IT/IAM (KNOW-2309 / KNOW-2330):** EBS snapshot *schedule* (manual baseline taken), off-box S3 `pg_dump`, SSM box access for the agent, and the GH-Actions deploy E2E (KNOW-2293) all wait on IT creating IAM roles.
- **App is now launch-capable on `main`** (KNOW-2334 + 2335 merged) but **not yet deployed to the box** — run `bin/deploy-prod.sh` and add OpenAI/Jira creds to `/etc/fme-train/env`, then do a real-OpenAI smoke run to close 2334/2335.
- **Cutover leftovers (low):** uptime/health monitor cron and `dnf-automatic` patching not yet set on the box; housekeeping ticket transitions (see below).

## Plan docs (index)

- `docs/plans/2026-04-29-multi-user-web-app.md` — app architecture (sections 1–5, 7 authoritative; §6 superseded).
- `docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md` — **active deployment architecture** (single EC2).
- `docs/plans/2026-06-08-ec2-migration-qa-and-cutover.md` — cutover runbook (Stages 1–7 / B0–B10).
- `docs/plans/2026-06-09-ec2-cutover-progress.md` — cutover **record**: B0–B7 + nightly-backup done; B8 / EBS-schedule / SSM deferred.

## Housekeeping (done 2026-06-10)

- ✅ **KNOW-2296 Closed** (hardened `deploy-prod.sh` is on `main`). **KNOW-2294** was already Closed.
- ⚠️ **KNOW-2295 and KNOW-2298 kept open** — each has a small *genuine* residual, so closing them would have been dishonest (see ticket comments):
  - KNOW-2295: `app/main.py` CORS TODO still says "App Runner"; `infra/README.md` lacks a "Retired" banner.
  - KNOW-2298: reconcile the `fme-train-scheduler` systemd unit in `bin/setup-ec2.sh` (decision — it runs in-process; documented in the cutover QA plan, not yet noted in the script) — overlaps KNOW-2333.
- ✅ Deleted merged/superseded branches: `feature/multi-user-web-app-ec2-pivot`, `migrate/ec2-prod-prep`, `…-KNOW-2293`, `…-KNOW-2295`, `…-KNOW-2296`.
- Kept `feature/multi-user-web-app` (fully merged into `main`, but the named integration branch — retire once we're confidently building off `main`).
