# Project state — single source of truth

> **Last updated:** 2026-06-10 (session post-cutover + PR cleanup; KNOW-2337).
> **What this is:** the always-current snapshot of *what is actually deployed, what is in
> flight, and what is next*. Read this **before starting any work** (see the reconcile ritual
> in `AGENTS.md`). It sits above the individual plan docs in `docs/plans/` — those describe
> *how*; this says *where we are*. Refresh it at every milestone (merge, deploy, ticket
> transition).

## Deployment state

| System | Branch / SHA | State | Notes |
|---|---|---|---|
| **EC2 production** | `main` @`9a9d6e91` | **LIVE but app = scaffold** | Box `i-0389b1e00a2661746`, `fme-train.base.safe.com` (EIP `44.241.192.143`), us-west-2. Auth + TLS + DB + nightly backup all up. **Runs are stubbed** (`_stub_step_body`) and there's **no launch UI** until KNOW-2334/2335 land — do not point real users at it yet. |
| Local dev | Compose (`make up`) | Full app: FastAPI + Postgres 16 + minio + worker | `InProcessTaskDispatcher`; `LocalFolderSource` for content; minio = S3. This is where the agent runs functional QA. |

## Active work (ticket ↔ branch ↔ PR ↔ status ↔ plan ↔ next)

| Ticket | Branch | PR | Status | Plan | Next action |
|---|---|---|---|---|---|
| **KNOW-2334** real pipeline in worker | `know-2334-steps-3-4` | #26 merged; #27 (slice 2) | In Progress | build plan Part 2 | Slices 1–2: steps 1–3 real (manifest, changelog, assessment) + RunCostMeter wired; `make test` green (428 pass; `run_worker` integration tests gated on Postgres — KNOW-2265). Next: step 5 (report serving), step 6, drafts. |
| **KNOW-2335** run-launch UI + endpoint | — | — | In Backlog (blocked by 2334) | build plan Part 2 | After 2334 runs e2e. |
| **KNOW-2337** PROJECT-STATE + AGENTS ritual | `know-2337-project-state` | #25 | Ready for QA (this PR) | build plan Part 1 | Review + merge #25. |
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
- **App not user-ready:** no way to launch a run and the worker is stubbed → KNOW-2334 then KNOW-2335.
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
