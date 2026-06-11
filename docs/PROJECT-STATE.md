# Project state — single source of truth

> **Last updated:** 2026-06-11 (KNOW-2342 merged as #33 — redeploy pending; EC2 IT asks reorganized — KNOW-2309 → SSM-only, split out KNOW-2341 backups + KNOW-2343 cert; `dnf-automatic` patching confirmed enabled on the box).
> **What this is:** the always-current snapshot of *what is actually deployed, what is in
> flight, and what is next*. Read this **before starting any work** (see the reconcile ritual
> in `AGENTS.md`). It sits above the individual plan docs in `docs/plans/` — those describe
> *how*; this says *where we are*. Refresh it at every milestone (merge, deploy, ticket
> transition).

## Deployment state

| System | Branch / SHA | State | Notes |
|---|---|---|---|
| **EC2 production (the box)** | `601ff82f` (deployed 2026-06-11) | **LIVE on the full app** | Box `i-0389b1e00a2661746`, `fme-train.base.safe.com` (EIP `44.241.192.143`), us-west-2. Auth + TLS + DB + nightly backup up; OpenAI/Jira secrets in `/etc/fme-train/env`. **Real pipeline jobs ran on prod** → KNOW-2334/2335 verified live. **KNOW-2340 deployed + verified** (report `/artifacts` mount, launch-UI width, `setup-ec2.sh` artifacts dir, `deploy-prod.sh` scratch-DB validation) — `bin/deploy-prod.sh` now runs clean end-to-end (also proves the KNOW-2296 fix). ⚠️ **KNOW-2342** (Lesson-Edits dropdown empty: drafts-fetch coupling + `APP_BASE_URL`=localhost; + default step 6 on) merged (#33) — **redeploy to apply**; reports already on disk need regeneration. |
| **`main` (code)** | `c52687b6` | **Full launch-capable app** | KNOW-2334 + 2335 + 2340 + **2342 (#33)** merged. Box still runs `601ff82f` — **redeploy to apply 2342**. |
| Local dev | Compose (`make up`) | Full app: FastAPI + Postgres 16 + minio + worker | `InProcessTaskDispatcher`; `LocalFolderSource` for content; minio = S3. This is where the agent runs functional QA. |

## Active work (ticket ↔ branch ↔ PR ↔ status ↔ plan ↔ next)

| Ticket | Branch | PR | Status | Plan | Next action |
|---|---|---|---|---|---|
| **KNOW-2334** real pipeline in worker | — (merged) | #26/#27/#28 merged | **Ready for QA** | build plan Part 2 | **All 6 steps real** + RunCostMeter + `/report/{run_id}`; `_stub_step_body` gone; `make test` green; launch→execute verified live (steps 1–2; 3/6 mocked-tested). QA: a real-OpenAI run (small scope). Follow-ups: `artifact_keys_json` (KNOW-2339), Postgres test harness (KNOW-2265). |
| **KNOW-2335** run-launch UI + endpoint | — (merged) | #29 merged | **Ready for QA** | build plan Part 2 | Merged. `POST /api/runs` + `GET /api/runs/*` + `/api/versions` + `/api/content-tree` + launch UI (signed-out sign-in link / signed-in form). Verified live: authed `POST /api/runs` → real run executed. QA: browser/UX pass. |
| **KNOW-2340** post-first-deploy fixes | — (merged) | #32 merged | **Ready for QA** (deployed) | — | Merged + **deployed to box 2026-06-11**; the redeploy ran clean end-to-end (proves the KNOW-2296 scratch-DB fix). QA: launch page full-width + Report opens on the box. |
| **KNOW-2342** Lesson-Edits tab empty + step 6 default | — (merged) | #33 merged | Ready for QA (redeploy pending) | — | Root-caused live on run `20260610T204941-3fe8`: report edit-plans load coupled (via `Promise.all`) to a hung drafts fetch (`APP_BASE`=localhost). Fix: decouple load + drafts `AbortController` timeout + `APP_BASE_URL` default `""` (same-origin) + step 6 on by default. `make test` green (467). **Redeploy** → **fresh run** to verify dropdown populates + drafts autosave (same-origin PUT). Existing reports need regeneration. |
| **KNOW-2337** PROJECT-STATE + AGENTS ritual | — (merged) | #25 merged | Ready for QA | build plan Part 1 | Done/merged; awaiting close. |
| **KNOW-2333** `bin/setup-ec2.sh` fixes (exec bit, pg_hba) | — | — | In Backlog | cutover tracker | Fix in repo; bites next provision. |
| **KNOW-2330** give agent SSM box access | — | — | In Backlog (**blocked by 2309**) | — | Dev-side only now: install `aws` CLI + `session-manager-plugin`, verify SSM session. IT/IAM provisioning split to KNOW-2309. |
| **KNOW-2309** SSM Session Manager access | — | — | In Backlog (**IT-blocked**) | — | Rewritten as the IT ask: instance role (`AmazonSSMManagedInstanceCore`) + scoped `ssm:StartSession` on **kept** `fmetraining` (no dedicated principal / no scope-down — old premise was wrong). |
| **KNOW-2341** EBS-snapshot schedule + off-box `pg_dump`→S3 | — | — | In Backlog (**IT-blocked**) | — | Split from 2309. `aws dlm create-default-role` + S3 bucket/perms. Manual snapshot baseline taken; nightly dump is on-box only until this lands. |
| **KNOW-2343** renew `*.base.safe.com` TLS cert | — | — | In Backlog (**IT, due Aug 5**) | — | Wildcard cert expires **2026-08-19**; no certbot → manual IT re-issue. |
| **KNOW-2293** GH Actions deploy workflow | code on `main` | #17 closed-superseded | Ready for QA — **E2E blocked** | cutover tracker (B8) | Rework to SSM/self-hosted runner; runner can't reach office-IP box. |

## Recent merges

| PR | → | Date | Carried |
|---|---|---|---|
| #24 `migrate/ec2-prod-prep` | `main` (`e05f3e83`) | 2026-06-09 | Cutover Stages 1–6: full app + setup/deploy scripts + deploy workflow + host/TLS reconciliation + XSS fix |
| #6 `…KNOW-2275` | `main` (`8b2cc09d`) | 2026-06-08 | WYSIWYG lists |
| — (direct) | `main` (`ae7f8282`→`9a9d6e91`) | 2026-06-09/10 | Cutover progress tracker; stale deployment-comment fixes (salvaged from #15) |

**Closed without merge (superseded by the cutover on `main`):** PR #15 (KNOW-2295), #17 (KNOW-2293), #18 (KNOW-2296).

## Open blockers

- **IT/IAM + cert (batch of 3 — file together):**
  - **KNOW-2309** — SSM instance role + scoped `ssm:StartSession` on `fmetraining` (agent box access; also unblocks the GH-Actions deploy E2E, KNOW-2293). Decision: **keep `fmetraining`** — no dedicated principal, no scope-down. Outbound 443 already works (box calls GitHub/OpenAI/Jira/Skilljar/S3), so no egress change needed.
  - **KNOW-2341** — DLM role for scheduled EBS snapshots + S3 bucket/perms for off-box `pg_dump` (manual snapshot baseline taken; dumps on-box only until this lands).
  - **KNOW-2343** — re-issue `*.base.safe.com` wildcard TLS cert before **2026-08-19** (no certbot; due-dated Aug 5).
- **App (KNOW-2342 redeploy):** the box runs the full app and real runs execute end-to-end (KNOW-2334/2335/2340 deployed + verified at `601ff82f`). **KNOW-2342** (Lesson-Edits dropdown/drafts fix + step-6 default-on) is now **merged (#33)** but **not yet redeployed** — redeploy `bin/deploy-prod.sh`, then a fresh run; existing reports need regeneration. Tracked in the deployment table above.
- **Cutover leftovers (low):** uptime/health monitor cron not yet set on the box (`dnf-automatic` patching ✅ confirmed enabled 2026-06-11); housekeeping ticket transitions (see below).

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
