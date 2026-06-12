# Project state — single source of truth

> **Last updated:** 2026-06-12 (KNOW-2342 + 2278 deployed & verified live; **KNOW-2347** lesson-image 404 fix merged #36 + verified — redeploy `main` for hygiene; AGENTS epic-parenting merged #35; filed KNOW-2348 Regen-Report port + KNOW-2350 flaky test).
> **What this is:** the always-current snapshot of *what is actually deployed, what is in
> flight, and what is next*. Read this **before starting any work** (see the reconcile ritual
> in `AGENTS.md`). It sits above the individual plan docs in `docs/plans/` — those describe
> *how*; this says *where we are*. Refresh it at every milestone (merge, deploy, ticket
> transition).

## Deployment state

| System | Branch / SHA | State | Notes |
|---|---|---|---|
| **EC2 production (the box)** | KNOW-2347 code (`d1359161` equiv) — redeploy `main` pending (hygiene) | **LIVE on the full app** | Box `i-0389b1e00a2661746`, `fme-train.base.safe.com` (EIP `44.241.192.143`), us-west-2. Auth + TLS + DB + nightly backup up; OpenAI/Jira secrets in `/etc/fme-train/env`. **Real pipeline jobs ran on prod** → KNOW-2334/2335 verified live. **KNOW-2340 deployed + verified** (report `/artifacts` mount, launch-UI width, `setup-ec2.sh` artifacts dir, `deploy-prod.sh` scratch-DB validation) — `bin/deploy-prod.sh` now runs clean end-to-end (also proves the KNOW-2296 fix). **KNOW-2342 / 2278 / 2347 all deployed + verified live 2026-06-12**: Lesson-Edits dropdown + drafts ✅, Save-to-Version disabled ✅, lesson images served via `/lesson-content` ✅. Box is on the KNOW-2347 branch ref — `bash bin/deploy-prod.sh` (no ref) resets HEAD/last-good-SHA to `main` (no code change). |
| **`main` (code)** | `d1359161` | **Full launch-capable app** | KNOW-2334 + 2335 + 2340 + 2342 (#33) + **2278 (#34)** + AGENTS epic-parenting (#35) + **2347 (#36)** merged. |
| Local dev | Compose (`make up`) | Full app: FastAPI + Postgres 16 + minio + worker | `InProcessTaskDispatcher`; `LocalFolderSource` for content; minio = S3. This is where the agent runs functional QA. |

## Active work (ticket ↔ branch ↔ PR ↔ status ↔ plan ↔ next)

| Ticket | Branch | PR | Status | Plan | Next action |
|---|---|---|---|---|---|
| **KNOW-2334** real pipeline in worker | — (merged) | #26/#27/#28 merged | **Ready for QA** | build plan Part 2 | **All 6 steps real** + RunCostMeter + `/report/{run_id}`; `_stub_step_body` gone; `make test` green; launch→execute verified live (steps 1–2; 3/6 mocked-tested). QA: a real-OpenAI run (small scope). Follow-ups: `artifact_keys_json` (KNOW-2339), Postgres test harness (KNOW-2265). |
| **KNOW-2335** run-launch UI + endpoint | — (merged) | #29 merged | **Ready for QA** | build plan Part 2 | Merged. `POST /api/runs` + `GET /api/runs/*` + `/api/versions` + `/api/content-tree` + launch UI (signed-out sign-in link / signed-in form). Verified live: authed `POST /api/runs` → real run executed. QA: browser/UX pass. |
| **KNOW-2340** post-first-deploy fixes | — (merged) | #32 merged | **Ready for QA** (deployed) | — | Merged + **deployed to box 2026-06-11**; the redeploy ran clean end-to-end (proves the KNOW-2296 scratch-DB fix). QA: launch page full-width + Report opens on the box. |
| **KNOW-2342** Lesson-Edits tab empty + step 6 default | — (merged) | #33 merged | **Ready for QA** (deployed ✅) | — | Decoupled edit-plans load + drafts `AbortController` + `APP_BASE_URL`="" (same-origin) + step 6 default-on. **Deployed + verified live 2026-06-12**: dropdown populates, drafts autosave 200 same-origin. |
| **KNOW-2278** disable Save-to-Version (stopgap) | — (merged) | #34 merged | **Ready for QA** (deployed ✅) | — | `/api/save-lesson` never ported to FastAPI → button hard-404'd. Stopgap: disable button + guard `leSave()`. Verified live 2026-06-12. Full port still pending. |
| **KNOW-2347** lesson images 404 in report | — (merged) | #36 merged | **Ready for QA** (deployed ✅) | — | Report used relative `../{lesson_dir}/` → 404 vs the `/artifacts` mount. Fix: new `/lesson-content/{rel}` route + `resolve_content_path` (serves `lesson_content_root`); report repointed; centralized `leImgRelTail`/`leNormalizeImages`, autosave stores relative, legacy drafts auto-heal. Verified live (direct URL + fresh report + edit→reload). See [[project_lesson_image_paths]]. |
| **KNOW-2337** PROJECT-STATE + AGENTS ritual | — (merged) | #25 merged | Ready for QA | build plan Part 1 | Done/merged; awaiting close. |
| **KNOW-2333** `bin/setup-ec2.sh` fixes (exec bit, pg_hba) | — | — | In Backlog | cutover tracker | Fix in repo; bites next provision. |
| **KNOW-2330** give agent SSM box access | — | — | In Backlog (**blocked by 2309**) | — | Dev-side only now: install `aws` CLI + `session-manager-plugin`, verify SSM session. IT/IAM provisioning split to KNOW-2309. |
| **KNOW-2309** SSM Session Manager access | — | — | In Backlog (**IT-blocked**) | — | Rewritten as the IT ask: instance role (`AmazonSSMManagedInstanceCore`) + scoped `ssm:StartSession` on **kept** `fmetraining` (no dedicated principal / no scope-down — old premise was wrong). |
| **KNOW-2341** EBS-snapshot schedule + off-box `pg_dump`→S3 | — | — | In Backlog (**IT-blocked**) | — | Split from 2309. `aws dlm create-default-role` + S3 bucket/perms. Manual snapshot baseline taken; nightly dump is on-box only until this lands. |
| **KNOW-2343** renew `*.base.safe.com` TLS cert | — | — | In Backlog (**IT, due Aug 5**) | — | Wildcard cert expires **2026-08-19**; no certbot → manual IT re-issue. |
| **KNOW-2293** GH Actions deploy workflow | code on `main` | #17 closed-superseded | Ready for QA — **E2E blocked** | cutover tracker (B8) | Rework to SSM/self-hosted runner; runner can't reach office-IP box. |
| **KNOW-2348** port Regen-Report to web app | — | — | In Backlog | — | Legacy launcher had it (serve.py `/api/run-action` → `pipeline.py --report-only`); not ported to the FastAPI app. Add run-history button + endpoint. Interim: CLI `pipeline.py --report-only <run> --output-dir /var/lib/fme-train/artifacts/<run>`. |
| **KNOW-2350** flaky test (steps 5/6 dispatch) | — | — | In Backlog | — | `test_make_step_body_dispatches_steps_5_6` ~2/10 fail in isolation (async log-flush race in `run_worker`); pre-existing. Plus 13 pre-existing ruff errors in `make lint`. |

## Recent merges

| PR | → | Date | Carried |
|---|---|---|---|
| #36 `…KNOW-2347` | `main` (`d1359161`) | 2026-06-12 | Lesson images via `/lesson-content` route + draft path hardening |
| #35 `docs/know-epic-parenting` | `main` (`88d90d76`) | 2026-06-11 | AGENTS KNOW epic hierarchy + parenting convention |
| #34 `…KNOW-2278` | `main` (`1da13f7d`) | 2026-06-11 | Disable Save-to-Version button (stopgap) |
| #24 `migrate/ec2-prod-prep` | `main` (`e05f3e83`) | 2026-06-09 | Cutover Stages 1–6: full app + setup/deploy scripts + deploy workflow + host/TLS reconciliation + XSS fix |
| #6 `…KNOW-2275` | `main` (`8b2cc09d`) | 2026-06-08 | WYSIWYG lists |
| — (direct) | `main` (`ae7f8282`→`9a9d6e91`) | 2026-06-09/10 | Cutover progress tracker; stale deployment-comment fixes (salvaged from #15) |

**Closed without merge (superseded by the cutover on `main`):** PR #15 (KNOW-2295), #17 (KNOW-2293), #18 (KNOW-2296).

## Open blockers

- **IT/IAM + cert (batch of 3 — file together):**
  - **KNOW-2309** — SSM instance role + scoped `ssm:StartSession` on `fmetraining` (agent box access; also unblocks the GH-Actions deploy E2E, KNOW-2293). Decision: **keep `fmetraining`** — no dedicated principal, no scope-down. Outbound 443 already works (box calls GitHub/OpenAI/Jira/Skilljar/S3), so no egress change needed.
  - **KNOW-2341** — DLM role for scheduled EBS snapshots + S3 bucket/perms for off-box `pg_dump` (manual snapshot baseline taken; dumps on-box only until this lands).
  - **KNOW-2343** — re-issue `*.base.safe.com` wildcard TLS cert before **2026-08-19** (no certbot; due-dated Aug 5).
- **App:** ✅ resolved — KNOW-2342 / 2278 / 2347 all deployed + verified live on the box (2026-06-12). Remaining is a hygiene `bash bin/deploy-prod.sh` (no ref) to reset the box from the KNOW-2347 branch ref to `main` (`d1359161`) — no code change. Pre-existing test flake (KNOW-2350) + 13 ruff lint errors noted, non-blocking.
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
