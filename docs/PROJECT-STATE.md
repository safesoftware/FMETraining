# Project state — single source of truth

> **Last updated:** 2026-06-16 (**App now sources ALL content from the public S3 mirror — KNOW-2307 (re-scoped), PR #55 (`feature/s3-content-source`).** A `/goal` run (foundation + parallel worktree agents) built a config-switched content resolver (`pipeline/content_source.py`: LocalFolderSource + `S3MirrorSource`, `CONTENT_SOURCE`/`CONTENT_S3_BASE_URL`) and routed **every** source read through it (pipeline + app); release detection is now a **filesystem listing of the writable saved store** (no git). **Editing + publishing proven entirely from the live S3 mirror with the local corpus unreachable**; `make test` 630 / `make smoke` green / ruff clean / boots. **This resolves the box-readiness gate: KNOW-2362** (git) **and KNOW-2359** (corpus-on-box) — the box needs no corpus/git, just `CONTENT_SOURCE=s3mirror` + publish creds. **✅ Since shipped: KNOW-2364 done** (corpus removed, 7882 files, PR #56) **and the box is LIVE on S3** (`fme-train` deployed `main` + `CONTENT_SOURCE=s3mirror`; editing + publishing validated on the box, incl. a pasted-image rehost). Only remaining: **KNOW-2361** (local-dev image creds — box unaffected). — *Earlier 2026-06-16:* **Publish-in-app MVP MERGED — PR #53 → `main` `b4e0df57`.** Live local QA this session validated the whole chain: **Save-to-Version against real S3** ✅, the **`release` (live-course)** path ✅, and the **`push_only` (draft)** path ✅ — incl. a real push to a Skilljar draft. QA found + fixed **3 real bugs** (all in #53, each with a regression test): image-copy `copytree`→`copyfile` EPERM on bind mounts; the `leSave()` "download + use serve.py" legacy fallback → clean error; and `link_draft_course` title matching (`Exercise_` folder vs `Exercise:` title) → alphanumeric normalize. **Publishing does NOT work on the box yet** — filed the blockers: **KNOW-2362** (app image has no `git`; `scan_saved_lessons` silently returns empty), **KNOW-2359** (box has no on-disk content corpus / git tree), **KNOW-2361** (S3 image creds pinned to minio locally) + a draft-first safety AC on **KNOW-2323**. **→ Box-readiness is now the top backlog item** (order below). Suite 562/18, ruff clean, `make smoke` green. — *Prior, 2026-06-15:* **Publishing-in-app release sprint — MVP built, PR #53** — one `/goal` run with 6 parallel worktree agents landed the full edit→Save→push MVP **plus** the Releases UI on `feature/publish-in-app`: **KNOW-2357** (WS-A `POST /api/save-lesson` + WS-F report Save button) and **KNOW-2358** (WS-B1 pipeline cleanup w/ 2321 idempotency + `["archived"]` labels + Step-4 deletion; WS-B2 release service; WS-C `/api/release-*` router; WS-D `/release` page). Folds in/closes **KNOW-2321/2322** + the Step-4 slice of **KNOW-2323**. Hermetic-green (**560/18** direct, **559/19** `make test`, ruff clean, `make smoke` green, 39 routes boot) — **NOT yet live-Skilljar QA'd**; box QA checklist + risks in the sprint section below. WS-E (locks/history) deferred. The earlier staging (tickets + handoff section + backlog order) shipped in #52. — *Prior, 2026-06-12:* **Closed KNOW-2334/2335/2340/2342/2347** — QA'd this session; KNOW-2340 launch page now full-width #37; KNOW-2347 lesson-image 404 fix #36; the KNOW-2278 *disable-Save stopgap* shipped #34 but its full Phase-2 port stays In Backlog; AGENTS epic-parenting #35; filed KNOW-2348 + KNOW-2350; **dev-backlog batch merged #38–#41** (KNOW-2348 Regen-Report; 2169/2170 suggestion accuracy; 2287/2288/2289 drafts hardening; 2350/2320 flake fix + ruff clean) — all 8 now **Ready for QA**, integrated suite 501 passed / ruff clean. **Then a local-Docker full-run QA pass surfaced a path/permission seam** (the pipeline layer was blind to the container's split `/app` vs `/content` layout) → fixed as one coordinated arc: **KNOW-2352** (`/app/.cache`, #44), **KNOW-2353** (lesson content-root, #45), **KNOW-2348** Regen-UX rework (#46), and **KNOW-2354** Docker runtime hardening (#47: single content/cache root + writable-root model + `make smoke` regression guard) — all Ready for QA; integrated suite 511 / ruff clean / `make smoke` green. Legacy `serve.py` launcher deprecated (#43; full retire = **KNOW-2351**). Audit + verdict in `docs/analysis/`. Box redeploy of `main` pending for hygiene.)
> **What this is:** the always-current snapshot of *what is actually deployed, what is in
> flight, and what is next*. Read this **before starting any work** (see the reconcile ritual
> in `AGENTS.md`). It sits above the individual plan docs in `docs/plans/` — those describe
> *how*; this says *where we are*. Refresh it at every milestone (merge, deploy, ticket
> transition).

## Deployment state

| System | Branch / SHA | State | Notes |
|---|---|---|---|
| **EC2 production (the box)** | KNOW-2340-fullwidth code (`06bbbfc3` equiv) — redeploy `main` pending (hygiene) | **LIVE on the full app** | Box `i-0389b1e00a2661746`, `fme-train.base.safe.com` (EIP `44.241.192.143`), us-west-2. Auth + TLS + DB + nightly backup up; OpenAI/Jira secrets in `/etc/fme-train/env`. **Real pipeline jobs ran on prod** → KNOW-2334/2335 verified live. **KNOW-2340 deployed + verified** (report `/artifacts` mount, launch-UI width, `setup-ec2.sh` artifacts dir, `deploy-prod.sh` scratch-DB validation) — `bin/deploy-prod.sh` now runs clean end-to-end (also proves the KNOW-2296 fix). **KNOW-2342 / 2278-stopgap / 2347 all deployed + verified live 2026-06-12**: Lesson-Edits dropdown + drafts ✅, Save-to-Version disabled ✅, lesson images served via `/lesson-content` ✅, launch page full-width ✅. Box is on the KNOW-2340-launch-full-width branch ref — `bash bin/deploy-prod.sh` (no ref) resets HEAD/last-good-SHA to `main` (`e8dfecb9`). **Note:** `main` now carries the Ready-for-QA dev batch (#38–#41) + the Docker fixes (#44/#45/#46/#47). The pipeline content/cache-root changes are env-gated (default `REPO_ROOT`) and KNOW-2354's compose changes are **dev-override only** (base/prod compose untouched), so prod is unaffected — but QA the dev batch before treating a `main` redeploy as a no-op. |
| **`main` (code)** | `e8dfecb9` | **Full launch-capable app** | …#33–#37… + **dev batch 2348/2169-70/2287-89/2350-20 (#38–#41)** + **launcher-deprecation docs (#43)** + **Docker fixes: 2352 .cache (#44), 2353 content-root (#45), 2348 Regen-UX rework (#46), 2354 hardening (#47)** merged. |
| Local dev | Compose (`make up`) | Full app: FastAPI + Postgres 16 + minio + worker | `InProcessTaskDispatcher`; `LocalFolderSource` for content; minio = S3. This is where the agent runs functional QA. |

## Active work (ticket ↔ branch ↔ PR ↔ status ↔ plan ↔ next)

| Ticket | Branch | PR | Status | Plan | Next action |
|---|---|---|---|---|---|
| **KNOW-2334** real pipeline in worker | — (merged) | #26/#27/#28 merged | **Closed** ✅ (QA'd this session) | build plan Part 2 | **All 6 steps real** + RunCostMeter + `/report/{run_id}`; `_stub_step_body` gone; `make test` green; launch→execute verified live (steps 1–2; 3/6 mocked-tested). QA: a real-OpenAI run (small scope). Follow-ups: `artifact_keys_json` (KNOW-2339), Postgres test harness (KNOW-2265). |
| **KNOW-2335** run-launch UI + endpoint | — (merged) | #29 merged | **Closed** ✅ (QA'd this session) | build plan Part 2 | Merged. `POST /api/runs` + `GET /api/runs/*` + `/api/versions` + `/api/content-tree` + launch UI (signed-out sign-in link / signed-in form). Verified live: authed `POST /api/runs` → real run executed. QA: browser/UX pass. |
| **KNOW-2340** post-first-deploy fixes | — (merged) | #32 + #37 | **Closed** ✅ (QA'd this session) | — | Report-mount + scratch-DB validation + launch-UI width. Report opens ✅; launch page now **full-width** (1200px cap → `max-width:none`, follow-up #37) ✅; deploy clean E2E ✅. |
| **KNOW-2342** Lesson-Edits tab empty + step 6 default | — (merged) | #33 merged | **Closed** ✅ (QA'd this session) | — | Decoupled edit-plans load + drafts `AbortController` + `APP_BASE_URL`="" (same-origin) + step 6 default-on. **Deployed + verified live 2026-06-12**: dropdown populates, drafts autosave 200 same-origin. |
| **KNOW-2278** [Phase 2] port report.py → Jinja templates | — | — (stopgap #34) | **In Backlog** | — | Large refactor: Jinja report + split inline JS. **Not started.** Only the *disable-Save-to-Version stopgap* shipped under this number (#34, verified live 2026-06-12). **Note:** the `/api/save-lesson` port is **carved out to KNOW-2357** (release sprint) — 2278 is now just the Jinja/JS refactor. |
| **KNOW-2347** lesson images 404 in report | — (merged) | #36 merged | **Closed** ✅ (QA'd this session) | — | Report used relative `../{lesson_dir}/` → 404 vs the `/artifacts` mount. Fix: new `/lesson-content/{rel}` route + `resolve_content_path` (serves `lesson_content_root`); report repointed; centralized `leImgRelTail`/`leNormalizeImages`, autosave stores relative, legacy drafts auto-heal. Verified live (direct URL + fresh report + edit→reload). See [[project_lesson_image_paths]]. |
| **KNOW-2337** PROJECT-STATE + AGENTS ritual | — (merged) | #25 merged | Ready for QA | build plan Part 1 | Done/merged; awaiting close. |
| **KNOW-2333** `bin/setup-ec2.sh` fixes (exec bit, pg_hba) | — | — | In Backlog | cutover tracker | Fix in repo; bites next provision. |
| **KNOW-2330** give agent SSM box access | — | — | In Backlog (**blocked by 2309**) | — | Dev-side only now: install `aws` CLI + `session-manager-plugin`, verify SSM session. IT/IAM provisioning split to KNOW-2309. |
| **KNOW-2309** SSM Session Manager access | — | — | In Backlog (**IT-blocked**) | — | Rewritten as the IT ask: instance role (`AmazonSSMManagedInstanceCore`) + scoped `ssm:StartSession` on **kept** `fmetraining` (no dedicated principal / no scope-down — old premise was wrong). |
| **KNOW-2341** EBS-snapshot schedule + off-box `pg_dump`→S3 | — | — | In Backlog (**IT-blocked**) | — | Split from 2309. `aws dlm create-default-role` + S3 bucket/perms. Manual snapshot baseline taken; nightly dump is on-box only until this lands. |
| **KNOW-2343** renew `*.base.safe.com` TLS cert | — | — | In Backlog (**IT, due Aug 5**) | — | Wildcard cert expires **2026-08-19**; no certbot → manual IT re-issue. |
| **KNOW-2293** GH Actions deploy workflow | code on `main` | #17 closed-superseded | Ready for QA — **E2E blocked** | cutover tracker (B8) | Rework to SSM/self-hosted runner; runner can't reach office-IP box. |
| **KNOW-2348** Regen-Report (web app) + UX rework | — (merged) | #38 + #46 | **Ready for QA** | — | `POST /api/runs/{id}/regenerate-report` + button (#38); **UX reworked per QA (#46)**: regen-only (no auto-open), streams regen logs via the existing SSE, new **Updated** column (`report_regenerated_at`, migration 0004). |
| **KNOW-2352** local Docker `/app/.cache` 503 | — (merged) | #44 merged | **Ready for QA** | — | appuser couldn't create `/app/.cache` (root-owned `/app`) → step-2 crash. Interim Dockerfile mkdir; superseded by KNOW-2354's writable-root model. |
| **KNOW-2353** pipeline content-root (`/content`) | — (merged) | #45 merged | **Ready for QA** | — | Pipeline read lesson HTML at `/app` not `LESSON_CONTENT_ROOT` → step 5/6 skipped all lessons (empty Lesson Edits). Plumbed `LESSON_CONTENT_ROOT` into pipeline reads. |
| **KNOW-2354** Docker runtime hardening | — (merged) | #47 merged | **Ready for QA** | — | Single content/cache root + writable-root model (drafts/cache off `/app`) + `./alembic` mount + **`make smoke`** guard (catches the 2352/2353 class). Dev-override only; prod unaffected. See `docs/analysis/`. |
| **KNOW-2351** retire legacy `serve.py` launcher | — | — | In Backlog (**blocked by the release sprint**) | — | Delete launcher once the publish/release flow (**KNOW-2358**) + save-lesson (**KNOW-2357**) reach parity in the app — see the release-sprint section. Docs repointed + `:8080` banner shipped (#43). |
| **KNOW-2350** flaky test (steps 5/6 dispatch) | — (merged) | #41 merged | **Ready for QA** | — | Root cause: in-memory SQLite shared one connection across the worker + log-flush coroutines → commit race. Fixed with per-test file-backed SQLite (own connection, matches prod pool). 50/50 loop pass. |
| **KNOW-2320** clear ruff lint debt (make lint green) | — (merged) | #41 merged | **Ready for QA** | — | Cleared all 13 ruff errors (8 F401, 4 F841, 1 E741), test-files only, behaviour-preserving. `ruff check .` clean. |
| **KNOW-2169** drop unmatched edit suggestions | — (merged) | #39 merged | **Ready for QA** | — | Drop suggestions the renderer can't apply; check mirrors renderer's real apply-time matching (attribute-aware + normalized text). |
| **KNOW-2170** empty-heading version suggestions | — (merged) | #39 merged | **Ready for QA** | — | `_ensure_version_changes()` fallback chain (nearest h2/h3 → first heading → "Introduction") guarantees a non-empty heading. |
| **KNOW-2287** bound list_runs_with_drafts (SQL) | — (merged) | #40 merged | **Ready for QA** | — | SQL-layer bound (DISTINCT run-id window + LIMIT) + dead branch removed; output unchanged. |
| **KNOW-2288** asserts in mark_run_draft_saved | — (merged) | #40 merged | **Ready for QA** | — | Asserts already gone on `main` (`9847873b`); added the missing regression test + verified `app/routes/` assert-free. |
| **KNOW-2289** draft saved-status stickiness | — (merged) | #40 merged | **Ready for QA** | — | Post-save edits now show `saved_edited` (Option C, Sam-confirmed) — keeps "saved to &lt;path&gt;" while flagging unpersisted changes; zero template/CSS change. |
| **KNOW-2357** port Save-to-Version (`/api/save-lesson`) + re-enable report Save (WS-A+F) | — (merged) | **PR #53** (`b4e0df57`) | **MERGED — validated live** | `as-far-as-i-golden-wave.md` | WS-A `lesson_writer.py` + `POST /api/save-lesson`; WS-F report Save re-enabled. **Live-QA'd: save → real S3 image rehost → version folder → `/drafts` badge** ✅. Fixed the `copytree` EPERM bug in QA. Awaiting close. |
| **KNOW-2358** port Skilljar publish/release flow into the app (WS-B/C/D) | — (merged) | **PR #53** (`b4e0df57`) | **MERGED — validated live (local)** | `as-far-as-i-golden-wave.md` | WS-B1/B2/C/D. **Live-QA'd both paths in dry-run + a real `push_only` push to a Skilljar draft** ✅. Folds in **KNOW-2321/2322 + the Step-4 slice of 2323** (close those). WS-E deferred. **Does NOT run on the box yet** → blockers KNOW-2362/2359/2361. Awaiting close. |
| **KNOW-2307** source content from the public S3 mirror (re-scoped) | `feature/s3-content-source` | **PR #55** | **In Review** (hermetic-green) | — | `pipeline/content_source.py`: LocalFolderSource + S3MirrorSource (env-switched); all source reads routed through it; Save→`SAVED_VERSIONS_ROOT`; release detection = filesystem listing (no git). **Editing + publishing proven entirely from S3 with the corpus unreachable.** `make test` 630 / `make smoke` green. |
| **KNOW-2362** release detection needed `git` | — | — | **✅ Resolved (PR #55)** | — | `scan_saved_lessons` is now a filesystem listing of `SAVED_VERSIONS_ROOT` — no git binary or work tree. |
| **KNOW-2359** in-app publishing needs a content corpus on the box | — | — | **✅ Resolved (PR #55)** | — | Decided + built: source from the **S3 mirror** → the box needs **no corpus, no git**. Box just sets `CONTENT_SOURCE=s3mirror` (+ publish creds). |
| **KNOW-2364** remove the 7830-file git corpus + default dev to S3 | — (merged) | **PR #56** (`4983aaa5`) | **✅ Done** | — | Removed 7882 corpus files; dev defaults to `s3mirror`; `make test`/`smoke` pinned `local`; `.dockerignore` cleaned. Box clone updated via `deploy-prod.sh main`. |
| **KNOW-2361** local dev can't rehost images (minio creds + no S3 endpoint) | — | — | **In Backlog** | — | Compose pins `minioadmin`; box side = real `AWS_*` (R2). Still relevant for the image-rehost/publish side. |

## Publishing-in-app release sprint (handoff — START HERE for publishing work)

> **Status as of 2026-06-16:** **MERGED to `main` (PR #53 / `b4e0df57`) + validated live (local).**
> The full edit→Save→release MVP (WS-A+F+B+C) **plus** the WS-D Releases UI shipped via one `/goal` run, then was QA'd
> live this session: Save → **real S3** image rehost → version folder → `/drafts` badge; the `release` and `push_only`
> paths in dry-run; and a **real `push_only` push to a Skilljar draft**. Three QA-found bugs fixed in #53 (copytree-EPERM,
> leSave download/`serve.py` fallback, draft-link title matcher), each with a regression test. **It does NOT yet run on
> the shared box** — blocked by **KNOW-2362** (no `git` in the app image → silent empty release list), **KNOW-2359** (no
> on-disk content corpus / git tree on the box), **KNOW-2361** (S3 image creds). WS-E (locks/history) deferred.
> **→ Next: box-readiness** (those three) — see the reprioritized order below.
> Approved plan: `~/.claude/plans/as-far-as-i-golden-wave.md`. Tickets: **KNOW-2357**, **KNOW-2358** (+ box-readiness **2362/2359/2361**).

### Goal
Make **edit → Save to Version → push a course to Skilljar** work **inside the FastAPI app** (port 8000),
hermetically tested locally first, then deployed to the box for human QA against real Skilljar.
**Why now:** the editing half already works and is "good enough" for the team to use for edit-suggestions
while Sam is away; the publish half was *never ported* into the new app — `Save to Version` is disabled
(KNOW-2278 stopgap) and the whole Skilljar push/release/archive flow lives only in the legacy `serve.py`
launcher (`:8080`) + `pipeline/skilljar_release.py`. Publishing is per-team-member, so it must be in-app.

### Locked architecture decisions (design around these — do not relitigate)
1. **Port the proven v1 logic; do NOT migrate to Skilljar API v2 / MCP now.** Reuse `pipeline/skilljar_release.py`
   + `pipeline/skilljar_push.py` + `pipeline/lesson_image_upload.py` largely verbatim, wrapped in an app service.
   (KNOW-2307 v2/MCP is explicitly deferred.)
2. **Operate on the on-disk version-folder tree.** Save-to-Version writes `index.html` + copies `images/` under
   `Settings.lesson_content_root`; the release flow's `scan_saved_lessons` reads that same tree; the saved badge
   uses the already-wired `report_lesson_drafts.mark_saved`. **Leave `lesson_drafts` / `drafts_root` untouched**
   (different path taxonomy — reconciling it is deferred v2 work). ← single most important seam (Risk R6).
3. **Fold in the bug fixes:** KNOW-2321 (archive idempotency guard + archive labels `["archived"]` only) and
   KNOW-2322/2323 (**delete Step 4 — the published-course tag-swap — entirely**; tags are dashboard-managed).
4. Keep `data/skilljar-mapping.json` as the mapping store (no DB migration now).
5. **Deferred (team continues / post-vacation):** v2/MCP (KNOW-2307); rest of the KNOW-2323 UX rework
   (inventory-dropdown draft-linking, auto-publish); `lesson_drafts` reconciliation; mapping→DB;
   `release_locks`/`release_history` if time runs short; KNOW-2313 (report XSS); retiring the legacy launcher (KNOW-2351).

### Work-streams (live status — update as each lands)
| WS | Scope | Ticket | Status | Branch / PR |
|---|---|---|---|---|
| **A** | `POST /api/save-lesson` — write accepted HTML to version folder + copy images + sanitize track-changes chrome (`app/services/lesson_writer.py`, `app/routes/save_lesson.py`) | KNOW-2357 | ✅ **Done** (hermetic-green) | PR #53 |
| **F** | Re-enable report Save button (`pipeline/report.py` ~371) + remove `leSave()` early-`return` guard | KNOW-2357 | ✅ **Done** (hermetic-green) | PR #53 |
| **B1** | Pipeline cleanup `pipeline/skilljar_release.py`: 2321 archive idempotency guard + `["archived"]`-only labels; **deleted Step 4** tag-swap + dead tag helpers (kept `_VERSION_SUFFIX_RE`); step logs renumbered `/4` | KNOW-2358 | ✅ **Done** (hermetic-green) | PR #53 |
| **B2** | App release service `app/services/skilljar_release_service.py` — implements the frozen contract reusing pipeline primitives verbatim; in-process release-log registry; creds/roots from `Settings` | KNOW-2358 | ✅ **Done** (hermetic-green) | PR #53 |
| **C** | Release endpoints — NEW router `app/routes/skilljar_release.py`: `GET /api/release-status\|release-plan\|release-log`, `POST /api/release-execute\|link-draft-course`; lazy service singleton; 400/503/404 guards; errors `{detail}` | KNOW-2358 | ✅ **Done** (hermetic-green) | PR #53 |
| **D** | Release page UI (`app/templates/release.html` + `/release` route + nav link) — no tag UI; explicit "publish manually in Skilljar" note | KNOW-2358 | ✅ **Done** (hermetic-green) | PR #53 |
| **E** | `release_locks`/`release_history` wiring (POLISH; tables already in `0001_baseline`) | KNOW-2358 | ⏸ **Deferred** (post-vacation; not needed for MVP) | — |

### Parallelization / dependency graph (for the `/goal` fan-out)
- **Start concurrently at t=0 (disjoint files):** WS-A, WS-B, WS-D template skeleton (against documented API shapes), WS-F.
- **Barrier B1:** freeze `skilljar_release_service` public signatures first (stub the module in the first hour) so WS-C codes against them.
- **Barrier C1:** freeze the `/api/release-*` JSON shapes (copy `serve.py`'s exactly, lines 540-655) so WS-D builds against them.
- **Collision mitigations:** WS-C creates a **NEW** router (never touches `app/routes/skilljar.py`, the existing sync route); **only WS-B** edits `pipeline/skilljar_release.py` (WS-C imports the *service*, never the pipeline module); the integrator owns final `app/main.py` `include_router` wiring; `base.html` nav link is a trivial 1-liner.
- **Critical path to "edit→save→push one course E2E":** WS-A + WS-F (save) and WS-B → WS-C (push). WS-D is convenience — the endpoints are curl/dry-run-driveable for the first QA.

### MVP cut line
**MVP (end-to-end, testable): WS-A + WS-F + WS-B + WS-C.** A human can: run pipeline → open report → accept edits →
Save to Version → `POST /api/release-execute` (dry-run, then live) → lesson HTML lands in the Skilljar draft.
The bug fixes (2321 idempotency/labels, Step-4 deletion) ship as part of WS-B.
**Polish / team-continues (clean seams, no MVP dependency):** WS-D (Releases UI — the obvious first pickup); WS-E (locks/history);
RunLogger-backed SSE for release logs (MVP uses an in-process dict + poll). Then the deferred backlog below.

### How to QA this — step by step

**Where to QA: locally.** The publish flow operates on an on-disk, git-tracked version-content tree. The repo checkout **is** that tree (folders `2021.0/ … 2024.x/`), so a local checkout is the correct (and historically the only) place to run publishing — same as the legacy `serve.py` flow. The prod box is **not** set up for it yet (see **C** below). Everything except a live Skilljar push can be validated with no external calls.

#### A. Hermetic checks (already green; for devs/CI)
```bash
make test     # full pytest in-container (SQLite, faked Skilljar) — 559 passed / 19 skipped
make lint     # ruff check . — clean
make smoke    # hermetic Docker guard (appuser, no OpenAI/DB) — PASSED
```

#### B. Local functional QA — in a browser (this is the real QA)
**1 — Boot the branch with WRITABLE content.** Save writes *into* the content tree, but the local override mounts it read-only; flip it just for QA (reverted in step 6):
```bash
git fetch origin && git checkout feature/publish-in-app
sed -i 's#- .:/content:ro#- .:/content#' docker-compose.override.yml   # content read-WRITE for Save
make down 2>/dev/null; make up                                         # recreate so the mount change takes
```
Wait ~20s, then open **http://localhost:8000** (port **8000** — not the legacy `:8080`) and sign in as usual.

**2 — Get a report that has a Lesson Edits tab.** Cheapest: reuse a completed run. Recent Runs → pick one with Lesson Edits → click **Regenerate Report** (free, no OpenAI). *Regenerating is required to get the re-enabled Save button* — the report is a static file, so reports built before this branch still show the old disabled button. (No suitable run? Launch a small one from the home page: one course, leave step 6 on.)

**3 — Save-to-Version (WS-A + WS-F).** Open that run's report → **Lesson Edits** tab → accept an edit → click **Save to Version Folder**:
- Expect a green **"✓ Saved to: `<version>/<lp>/<course> <version>/<lesson>/index.html`"**.
- Verify the file was actually written (on the host, in the repo working tree):
  ```bash
  git status --porcelain | grep index.html
  ```
- Open **http://localhost:8000/drafts** → that lesson now shows a **saved** badge.
- Click Save again → it should prompt **"File already exists … Overwrite?"** (the 409 path) → confirm → succeeds.

**4 — Release page (WS-B/C/D).** Open **http://localhost:8000/release**:
- Type the version you just saved into (e.g. `2026.1`) → **Check status** → the saved lesson appears under saved/mapped.
- **Preview plan** → renders the course/lesson plan + warnings.
- **Execute** with **Dry run ON** → the log streams to `done`; dry-run changes nothing. First confirm Skilljar creds are present (prints SET/MISSING, never the value):
  ```bash
  docker compose exec app printenv SKILLJAR_API_KEY >/dev/null && echo "skilljar key: SET" || echo "skilljar key: MISSING → execute returns 503 (guard working)"
  ```

**5 — (Optional) Live Skilljar push, one low-stakes course.** With creds SET: **Execute with Dry run OFF**. Then in the Skilljar dashboard confirm: the draft received your HTML; an **archive** course exists labelled **`archived` only**; the course was renamed; images load; **no tags were touched**. **Re-run → no duplicate archive** (proves the KNOW-2321 idempotency fix). Then **publish the draft manually in Skilljar** (the app deliberately does not auto-publish). *Known gap (R3): the local `data/skilljar-mapping.json` may not update because `/app/data` is read-only in the container — the Skilljar push still succeeds; only the local record lags. The release log shows the outcome.*

**6 — Clean up.**
```bash
git checkout docker-compose.override.yml     # restore the :ro content mount
git status                                   # find the test version folder you created in step 3
rm -rf "<version>/<lp>/<course> <version>"   # delete just that folder (e.g. "2026.1/fme-form-basic/…")
make down
```

#### C. The prod box — NOT publish-ready yet (finding, KNOW-2359)
On the box `LESSON_CONTENT_ROOT` is unset, so it defaults to `.` = `/opt/fme-train` (the app install), which **excludes the version-content corpus** (prod sources content from Skilljar, not disk) and is not a writable git content tree. Consequence: Save has no source lessons, and release-status (`git status`-based) finds nothing — **publishing cannot run on the box as configured.** Confirm on the box (EIC terminal):
```bash
grep -E 'LESSON_CONTENT_ROOT|SKILLJAR_|AWS_' /etc/fme-train/env | sed 's/=.*/=<set>/'   # presence only
cd /opt/fme-train && ls -d 20*.* 2>/dev/null | head ; git rev-parse --is-inside-work-tree 2>/dev/null
```
If that shows no version folders / not a work tree, QA locally (**B**). Provisioning a writable, git-tracked corpus at `LESSON_CONTENT_ROOT` on the box (or deciding publishing stays a local-checkout workflow) is tracked in **KNOW-2359**.

### Reprioritized backlog order (no Jira rank tool via MCP — order recorded here)
**✅ DONE (merged in PR #53):** KNOW-2357 (Save-to-Version, WS-A+F) + KNOW-2358 (release service/endpoints/UI, WS-B/C/D). Both validated live (local).

**✅ DONE (PR #55, `feature/s3-content-source`) — S3-mirror content sourcing (KNOW-2307, re-scoped):** the app sources ALL content from the public S3 mirror; editing + publishing proven entirely from S3 with the corpus unreachable (`make test` 630 / `make smoke` green). This **resolved the box-readiness gate**:
- **KNOW-2362** ✅ — `scan_saved_lessons` is now a filesystem listing of the writable saved store (no git). *Resolved.*
- **KNOW-2359** ✅ — decided + built: source from the S3 mirror, so the box needs **no corpus and no git** (not a corpus-on-box, not API/MCP). *Resolved by the S3-mirror decision.*

**✅ DONE — box-readiness / S3 publishing is LIVE:**
- PR #55 (S3 sourcing) + **PR #56 (KNOW-2364 — corpus removed, 7882 files)** merged to `main`. Local dev defaults to `s3mirror`; `make test`/`make smoke` pinned `local`.
- **Box deployed + validated 2026-06-16:** `fme-train` runs `main` with `CONTENT_SOURCE=s3mirror` + publish creds in `/etc/fme-train/env`; Sam ran editing **and** publishing on the box (incl. a pasted image rehosted to S3 on publish); corpus removed from the box's clone too. KNOW-2307/2362/2359/2364 resolved.

**▶ NOW — next:**
1. **KNOW-2361** — local-dev S3 image-upload creds (the box uses real `AWS_*` and works; locally the compose pins `minioadmin` + the upload path ignores `S3_ENDPOINT_URL`, so local image-rehost can't run without a manual cred override). Decide: stop pinning `minioadmin` (let `.env` real creds flow → real bucket, matches the box) vs. thread the minio endpoint. *Dev-convenience; box is unaffected.*

**Then:** KNOW-2358 WS-E (locks/history); the KNOW-2323 Releases-UX redesign (draft-first + warn-on-live safety AC); `lesson_drafts` reconciliation; mapping→DB / R3 (`data/` writability); KNOW-2313 (report XSS); retire the legacy launcher (KNOW-2351 — now largely unblocked: the publish flow + box are live; only `serve.py`'s single-lesson push remains legacy).

### Risks (flag R2/R3/R5 to Sam before box QA)
- **R5 (content-root writable):** Save writes under `lesson_content_root` (`/content`). KNOW-2354 made `/app` read-only — confirm `/content` is mounted **read-write** or saves fail.
- **R3 (mapping writable + concurrency):** `execute_release`/`link_draft_course` read-modify-write `data/skilljar-mapping.json` (~307 KB). If `data/` is read-only, the push still works but the local mapping record won't persist (known MVP gap) — relocate to a writable mount or accept the gap.
- **R2 (secrets on box):** the service threads `Settings.skilljar_api_key`/`aws_*` into the `pipeline.*` calls; ensure `/etc/fme-train/env` carries `SKILLJAR_API_KEY` + `AWS_*` for the app process.
- **R6 (draft-taxonomy):** Save MUST route through the on-disk tree + `report_lesson_drafts.mark_saved`, **NOT** `lesson_drafts`/`POST /api/drafts` — else `scan_saved_lessons` won't see the save and the push finds nothing.
- **R4 (S3/region):** `app/config` defaults region `us-west-2`, `pipeline/config` `us-east-1` — thread `Settings.aws_s3_region` through; live-QA a real pasted image.
- **R1 (static report):** the Save-button re-enable only affects regenerated/new reports — use regenerate-report in QA; don't promise historical reports.
- **R7 (log streaming):** MVP = in-process `action_key` dict + poll (port `serve.py`'s `_active_runs`); RunLogger/SSE is polish.

## Recent merges

| PR | → | Date | Carried |
|---|---|---|---|
| #47 `…KNOW-2354` | `main` (`e8dfecb9`) | 2026-06-12 | Docker runtime hardening: unify content/cache roots + writable-root model + `./alembic` mount + `make smoke` |
| #46 `…KNOW-2348-regen-ux` | `main` (`8f2f19ab`) | 2026-06-12 | Regen UX rework: regen-only, surface logs via SSE, Updated column (`report_regenerated_at` / 0004) |
| #45 `…KNOW-2353` | `main` (`64b78bfb`) | 2026-06-12 | Pipeline reads lesson content under `LESSON_CONTENT_ROOT` |
| #44 `…KNOW-2352` | `main` (`5f556067`) | 2026-06-12 | Pre-create writable `/app/.cache` (interim; superseded by #47) |
| #43 `chore/deprecate-legacy-launcher` | `main` (`2501389d`) | 2026-06-12 | Deprecate `serve.py` launcher in docs + `:8080` banner |
| #42 `docs/…dev-batch` | `main` (`cc6e069a`) | 2026-06-12 | PROJECT-STATE: dev-backlog batch reconcile |
| #41 `…KNOW-2350-2320` | `main` (`82ee26c4`) | 2026-06-12 | Fix flaky steps-5/6 dispatch test (per-test file SQLite) + clear 13 ruff errors |
| #40 `…KNOW-2287-2289` | `main` (`214c0247`) | 2026-06-12 | Drafts backend: SQL-bound list_runs_with_drafts, assert→error test, `saved_edited` status |
| #39 `…KNOW-2169-2170` | `main` (`3c119413`) | 2026-06-12 | Drop renderer-unapplyable + empty-heading edit suggestions |
| #38 `…KNOW-2348` | `main` (`3cdfa890`) | 2026-06-12 | Regenerate-Report endpoint + run-history button (in-process) |
| #37 `…KNOW-2340-launch-full-width` | `main` (`06bbbfc3`) | 2026-06-12 | Launch page full-width (drop fixed 1200px cap) |
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
- **App:** ✅ resolved — dev-backlog batch (#38–#41) + the **local-Docker path/permission seam** (KNOW-2352/2353/2354) + Regen-UX rework (#46) all fixed & Ready for QA. Integrated `main` (`e8dfecb9`) green: suite **511 passed**, `ruff check .` clean, **`make smoke` green** (the new guard catches the 2352/2353 class). Remaining is a hygiene `bash bin/deploy-prod.sh` (no ref) to reset the box to `main`; the pipeline root changes are env-gated (default `REPO_ROOT`) and KNOW-2354's compose changes are dev-only, so prod is unaffected — but QA the dev batch first.
- **Cutover leftovers (low):** uptime/health monitor cron not yet set on the box (`dnf-automatic` patching ✅ confirmed enabled 2026-06-11); housekeeping ticket transitions (see below).

## Plan docs (index)

- `docs/plans/2026-04-29-multi-user-web-app.md` — app architecture (sections 1–5, 7 authoritative; §6 superseded).
- `docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md` — **active deployment architecture** (single EC2).
- `docs/plans/2026-06-08-ec2-migration-qa-and-cutover.md` — cutover runbook (Stages 1–7 / B0–B10).
- `docs/plans/2026-06-09-ec2-cutover-progress.md` — cutover **record**: B0–B7 + nightly-backup done; B8 / EBS-schedule / SSM deferred.
- `docs/analysis/2026-06-12-docker-runtime-audit.md` — inventory of container path/permission/env mismatches (14 findings, 4 actual).
- `docs/analysis/2026-06-12-docker-architecture-assessment.md` — verdict (architecture sound; one seam) + remediation (→ KNOW-2354) + prevention (`make smoke`).
- `docs/plans/2026-06-12-know-2249-image-upload-ideation.md` + `…-know-2307-skilljar-mcp-ideation.md` — **DRAFT** ideation for the two Medium-pri epics (awaiting Sam's decisions; not yet approved).

## Housekeeping (done 2026-06-12)

- ✅ **Local-Docker path/permission seam fixed (one coordinated arc):** a full-run local QA pass exposed a bug class where the pipeline layer (`REPO_ROOT`-centric) was blind to the container's split layout. Fixed **KNOW-2352** (`/app/.cache`, #44), **KNOW-2353** (content-root, #45), and **KNOW-2354** hardening (#47: single content/cache root + writable-root model + `./alembic` mount + **`make smoke`** guard that catches the whole class), plus **KNOW-2348** Regen-UX rework (#46) per QA feedback. Verdict + audit in `docs/analysis/`. Integrated `main` green (511 passed, `make smoke` green). All Ready for QA.
- ✅ **Legacy `serve.py` launcher deprecated** (#43): run-locally docs (AGENTS/README/`docs/running-locally.md`) repointed to the FastAPI app on **:8000**, `:8080` deprecation banner added. Filed during QA when stale docs sent testing to the old launcher. Full retirement tracked **KNOW-2351** (gated on the Skilljar release-flow port, KNOW-2307/2323).
- ✅ **Parallel dev-backlog batch (#38–#41) merged → 8 tickets Ready for QA:** KNOW-2348 (Regen-Report endpoint + button), KNOW-2169/2170 (suggestion-accuracy filters), KNOW-2287/2288/2289 (drafts hardening), KNOW-2350/2320 (flaky-test root-cause fix + ruff clean). Four independent agents in isolated worktrees off `main`; integrated `main` verified green (501 passed, 19 skipped, `ruff check .` clean). Design calls confirmed with Sam: renderer-accurate matching (2169), "Introduction" heading fallback (2170), `saved_edited` status (2289).
- ✅ **Closed KNOW-2334 / 2335 / 2340 / 2342 / 2347** — QA'd live this session (real pipeline E2E, run-launch UI, post-deploy fixes incl. launch full-width, Lesson-Edits dropdown/drafts, lesson images).
- **KNOW-2340** closed after the full-width follow-up (#37): the launch page's fixed 1200px cap → `max-width:none` so it fills the viewport like the header (it read as ~1/3 width on wide monitors before).
- **KNOW-2293** left **Ready for QA** — GH-Actions deploy E2E is IT-blocked (office-IP firewall blocks the runner), can't QA.
- **KNOW-2278** clarified: the ticket is the **Phase-2 Jinja port** (In Backlog); only the disable-Save-to-Version stopgap shipped (#34).

## Housekeeping (done 2026-06-10)

- ✅ **KNOW-2296 Closed** (hardened `deploy-prod.sh` is on `main`). **KNOW-2294** was already Closed.
- ⚠️ **KNOW-2295 and KNOW-2298 kept open** — each has a small *genuine* residual, so closing them would have been dishonest (see ticket comments):
  - KNOW-2295: `app/main.py` CORS TODO still says "App Runner"; `infra/README.md` lacks a "Retired" banner.
  - KNOW-2298: reconcile the `fme-train-scheduler` systemd unit in `bin/setup-ec2.sh` (decision — it runs in-process; documented in the cutover QA plan, not yet noted in the script) — overlaps KNOW-2333.
- ✅ Deleted merged/superseded branches: `feature/multi-user-web-app-ec2-pivot`, `migrate/ec2-prod-prep`, `…-KNOW-2293`, `…-KNOW-2295`, `…-KNOW-2296`.
- Kept `feature/multi-user-web-app` (fully merged into `main`, but the named integration branch — retire once we're confidently building off `main`).
