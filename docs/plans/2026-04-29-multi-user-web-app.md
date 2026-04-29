# Plan — Multi-User Web App for FME Training Automation

> **Status:** Complete. All sections filled in based on the design Q&A. Pending IT review of Section "IT / Security / Privacy Review" before implementation begins.

---

## Context

**Today.** The tool runs as a single-user local web app: `serve.py` is built on stdlib `http.server` with `ThreadingMixIn`, the UI is hand-rolled HTML/JS in `launcher.html` (~1,500 lines), in-flight runs live in an in-memory dict (`_active_runs` in `serve.py:51-73`), artifacts are written to `artifacts/`, and the Skilljar mapping + current job state are flat JSON files in `data/`. All credentials come from a local `.env`. The pipeline (`pipeline.py` + `pipeline/*.py`) is a 6-step process that calls Jira, OpenAI, Skilljar, and S3.

**Three pain points motivating this change.**
1. **No shared state across users.** Each teammate runs their own copy with their own artifacts; nobody sees what anyone else is doing.
2. **Duplicated API spend.** Steps 3–4 (`gpt-4o-mini`, ~$0.20/run) and Step 6 (`gpt-4o`, ~$3–5/run) reprocess the same `(lesson, issue)` pairs across runs. Two users running overlapping scopes pay twice.
3. **No conflict prevention on Skilljar releases.** `pipeline/skilljar_release.py` PATCHes lesson HTML with last-write-wins. Two team pushes race; admin edits made in Skilljar's UI silently get overwritten; `data/skilljar-mapping.json` has read-modify-write hazards.

**Goal.** Convert the tool into a shared internal web app on AWS for 2–5 Safe Software staff, with Google SSO, durable state, a shared content cache that dedupes OpenAI calls across users, a redesigned Release tab with locks + remote-state hashing, and CI/CD from GitHub through staging → production. Web-only cutover when feature parity ships; the `launch.sh` / local-launcher path is retired at that point.

---

## Decisions locked in (from clarifying Q&A)

| Topic | Decision |
|---|---|
| User base | 2–5 internal Safe staff |
| Auth | Google OIDC sign-in restricted to `@safe.com` via `hd` claim |
| Deploy shape | AWS App Runner (web/API) + Fargate task per run + RDS Postgres + S3 |
| Sharing model | All runs visible to all; owner-tagged; soft locks on Skilljar releases |
| Skilljar conflict guard | Per-lesson advisory locks **and** remote-state hash check before each PATCH |
| Release tab capabilities | Skilljar state browser, per-lesson release history, bulk filters/actions, keep existing pre-release manifest summary |
| Migration strategy | Web-only cutover when ready; GitHub Actions CI/CD with staging → production promotion |
| Secret store | AWS Secrets Manager (KMS-encrypted, ARN-injected into App Runner & Fargate task defs) |
| Frontend stack | FastAPI + Jinja2 SSR + HTMX + Alpine.js (no separate SPA build) |
| Run concurrency | Cap at 2 concurrent runs team-wide |
| Per-run cost ceiling | $50, configurable per env via SSM Parameter Store |
| Cache bypass UX | Per-step "force fresh" toggles in Configure-Run |
| Cache retention | Never auto-evict; S3 lifecycle archives to Glacier Deep Archive after 365 days |
| Hash-mismatch handling | Block + require two-click override + log to `release_history.conflict_warning_json` |
| Phasing | Phase 0 → Phase 1 (cache) → Phase 2 (Release redesign) → optional Phase 3 (polish) |

---

## 1. System Architecture

```
                       Browser (Chrome) — Google SSO, signed cookie
                                   │ HTTPS
                       ┌───────────▼────────────┐
                       │ AWS App Runner         │  FastAPI + HTMX/Alpine
                       │ web + JSON API         │  Jinja2 SSR templates
                       └─┬──────┬──────┬────────┘
              ECS RunTask│      │SSE   │boto3
                         │      │tail  │
                  ┌──────▼─┐ ┌──▼─────┐ ┌▼────────────────┐
                  │Fargate │ │RDS      │ │S3 (private)     │
                  │run     │ │Postgres │ │artifacts/       │
                  │worker  │ │         │ │images/ (CDN)    │
                  └───┬────┘ └─────────┘ │cache/           │
                      │                  └─────────────────┘
                      ▼ OpenAI · Jira · Skilljar · S3
```

- **App Runner** serves UI + JSON API. Always-on, auto-HTTPS, no VPC/ALB management. ~$25/mo idle.
- **Fargate task per run.** API calls `boto3.client("ecs").run_task()` to launch an isolated worker. The worker is the existing `pipeline.py` adapted to read inputs from RDS/S3 and write outputs back. Pay only while running.
- **RDS Postgres** (`db.t4g.micro`, ~$15/mo). Durable state: users, runs, locks, release history, cache index, Skilljar inventory snapshot, mapping.
- **S3 (private, KMS-encrypted)** for artifacts + cache blobs + uploaded images. Pre-signed URLs for download. One small public-via-CloudFront prefix for lesson images that Skilljar embeds.
- **Lesson content tree** (`2025.0/`, `2026.1/`, …) is baked into the Fargate container image. Updating the corpus = new image + redeploy.
- **Live log streaming.** The Fargate worker appends rows to a `run_logs` table; the API streams to the browser via SSE by tailing the table. Survives App Runner restarts; no Kinesis/CloudWatch parsing required.

---

## 2. Identity & Data Model

### Identity (Google SSO)
- FastAPI uses `authlib` for OIDC. `GET /auth/login` → Google consent → callback → verify ID token signature → assert `email_verified=true` AND `hd == "safe.com"` → upsert `users` row → set signed session cookie.
- Cookie: `itsdangerous`-signed, `HttpOnly`, `Secure`, `SameSite=Lax`, 14-day rolling expiry. Signing key from Secrets Manager.
- `users.is_active` allowlist + `users.session_epoch` (bump to force sign-out).
- v1 has flat membership (no admin/member RBAC enforced). Schema reserves `users.role` for later.

### Postgres schema (v1)

```sql
-- Identity
users(id, email, name, picture_url, role, is_active, session_epoch,
      created_at, last_seen_at)

-- Run lifecycle (replaces artifacts/runs.json)
runs(id PK = run_id, created_by FK→users, to_version, scope_json,
     options_json, status, started_at, finished_at,
     fargate_task_arn, error_text, parent_run_id NULLABLE)
run_steps(run_id, step_num, status, started_at, finished_at,
          token_usage_json, artifact_keys_json)
run_logs(id PK, run_id, ts, level, message)        -- append-only

-- Job state (replaces data/update-job.json)
jobs(id, owner FK→users, to_version, scope_json, updated_at)

-- Skilljar coordination
skilljar_mapping(local_path PK, skilljar_lesson_id, skilljar_course_id,
                 last_synced_at, _meta_json)
skilljar_inventory(skilljar_lesson_id PK, course_id, title,
                   content_html_hash, last_modified_remote, fetched_at)
release_locks(skilljar_lesson_id PK, locked_by FK→users, locked_at,
              expires_at, run_id, intent)           -- TTL ~10 min
release_history(id PK, skilljar_lesson_id, run_id, user_id, started_at,
                finished_at, before_hash, after_hash, status,
                conflict_warning_json NULLABLE)

-- Shared content cache
content_cache(fingerprint PK = sha256, kind, model, prompt_version,
              s3_key, payload_summary_json, created_at, last_hit_at,
              hit_count, created_by_run_id)
              -- kinds: assessment_pair, edit_plan_lesson,
              -- manifest_lesson, changelog_filter, image_upload
s3_image_cache(content_sha256 PK, s3_url, content_type, byte_size,
               first_uploaded_at, hit_count)
jira_cache(filter_id PK, fetched_at, payload_s3_key, issue_count)
```

### S3 layout

```
s3://fme-train-prod/
  artifacts/{run_id}/{manifest|changelog|recommendations|edit-plans}.json
  reports/{run_id}.html
  cache/assessment_pair/{fingerprint}.json
  cache/edit_plan_lesson/{fingerprint}.json
  cache/jira_filter/{filter_id}/{fetched_at}.json
  images/{sha256}/{filename}            -- public via CloudFront, embedded in Skilljar
  lesson-content-uploads/{run_id}/...   -- transient
```

### Migration of existing data
- `artifacts/runs.json` → seed `runs` + `run_steps` (one-shot script).
- `artifacts/*.json` and `report-*.html` → upload to `s3://…/artifacts/{run_id}/…`, write keys back to `run_steps.artifact_keys_json`.
- `data/skilljar-mapping.json` → bulk insert into `skilljar_mapping`.
- `inputs/jira_api_cache.json` → upload to S3, insert `jira_cache` row.
- `data/update-job.json` → starter `jobs` row owned by `sam.walker@safe.com`.

---

## 3. Run Execution & Live Logs

```
POST /api/runs                          ┌──────────────────────────────┐
   │ validates + persists `runs` row    │ Run scheduler (in App Runner)│
   ▼ status=queued                      │ - team-wide cap = 2          │
┌──────────────────────────────┐  poll  │ - on slot free: dispatch     │
│ runs (RDS)                   ◄────────┤   ECS run_task               │
│ status, fargate_task_arn     │        │ - apply $50/run cost ceiling │
└──────────────────────────────┘        └────────────┬─────────────────┘
                                                     ▼
                                  ┌──────────────────────────────────┐
                                  │ Fargate task                     │
                                  │  ENV: RUN_ID, RESUME, MAX_RUN_USD│
                                  │  cmd: python -m worker           │
                                  └──────────────────────────────────┘

GET /api/runs/{id}/logs/stream  (SSE; tails run_logs WHERE id > last_seen)
```

- **Dual-mode container.** Same image runs as web (`ENTRYPOINT_MODE=web`) or worker (`ENTRYPOINT_MODE=worker`). Worker reads `RUN_ID` from env, looks up the `runs` row, executes pipeline steps 1–6, writes artifacts to S3, appends rows to `run_logs`.
- **Concurrency = 2 team-wide.** `app/services/run_scheduler.py` polls `runs` and dispatches the oldest queued run when `count(status IN ('queued','running')) < 2`. Queued runs surface in the UI with "X ahead of you."
- **Cost ceiling = $50/run.** A `RunCostMeter` accumulates `prompt_tokens` + `completion_tokens` (already tracked at `pipeline/assessment.py:281-282`), prices them via a model→$/M-token table, aborts before the next OpenAI call if projected total > ceiling. Status `aborted_cost_ceiling`. Configurable per env via SSM Parameter Store.
- **Cancellation.** `POST /api/runs/{id}/cancel` sets `runs.status = 'cancel_requested'`. Worker polls at every step boundary and per-lesson loop iteration; on cancel, status → `cancelled`, partial artifacts retained.
- **Resume.** `POST /api/runs/{id}/resume` enqueues the same `run_id` with `RESUME=true`. Worker reads `run_steps`, skips completed steps — mirrors today's `--resume` (`pipeline.py:165-175`). `pipeline/utils.py:get_completed_steps` is rewired to read from `run_steps` instead of `runs.json`.
- **Live logs are durable.** A small `RunLogger` batches inserts to `run_logs` every 200ms or on flush. Browser SSE reconnects via `Last-Event-ID` to resume mid-stream. No more lost-tail-on-server-restart.
- **Worker IAM.** Fargate task role has scoped permission: read its own `runs` row, write to its own `run_logs` / `run_steps` / `release_history` rows (row-level filter via `run_id` injected from env), read/write its run's S3 prefix.

**Files that move/change:**
- `serve.py` → retired. Replaced by `app/main.py` (FastAPI), `app/routes/runs.py`, `app/services/run_scheduler.py`, `app/services/sse.py`, `app/services/run_cost_meter.py`.
- `pipeline.py` → keeps its CLI for local dev; new `worker.py` thin wrapper drives it from env vars + RDS instead of `data/update-job.json`.
- `pipeline/assessment.py:281-282` and `pipeline/edit_suggestions.py` token tracking is rewired into the shared `RunCostMeter`.
- `pipeline/utils.py:get_completed_steps` (~line 231) reads from `run_steps`.

---

## 4. Shared Content Cache

The cache turns repeated OpenAI calls into S3 reads. Index lives in Postgres (`content_cache`); blobs live in S3 under `cache/<kind>/<fingerprint>.json`.

**Fingerprint formula:**
```
fingerprint = sha256(
    kind,                   # "assessment_pair" | "edit_plan_lesson" | "manifest_lesson" | …
    model_name,             # "gpt-4o" / "gpt-4o-mini"
    prompt_template_sha,    # hash of the prompt file (so prompt edits invalidate)
    input_payload_sha,      # hash of the actual input bytes
    extra_dims,             # to_version, vision_enabled, etc.
)
```

**Wrap-points in code:**
| Module | Wrap site | Cache kind | Per-call cost saved |
|---|---|---|---|
| `pipeline/assessment.py` | inner `_assess_pair()` call | `assessment_pair` | ~$0.0002 (gpt-4o-mini) |
| `pipeline/edit_suggestions.py` | per-lesson OpenAI call | `edit_plan_lesson` | ~$0.03 (gpt-4o) |
| `pipeline/manifest.py` | per-lesson HTML parse | `manifest_lesson` | trivial $$, big speed |
| `pipeline/jira_api.py` | filter fetch (already cached locally) | `changelog_filter` | API quota |
| `pipeline/skilljar_release.py:127` (`_s3_put`) | image upload | `s3_image_cache` (separate table) | S3 PUT + dedup |

**Prompt versioning.** Every prompt template file under `prompts/` carries a `# version: <semver>` header; the cache key includes the SHA of the file (header + body). Editing a prompt automatically invalidates that prompt's cache slice with no manual flush.

**Per-step force-fresh toggles.** Configure-Run gains three independent checkboxes: "Force fresh manifest", "Force fresh assessments", "Force fresh edit plans". Toggling any one writes a flag on the run; the cache wrappers check the flag per-step before lookup. The cost ceiling still applies — force-fresh doesn't disable the $50 abort.

**Retention.** Cache entries are never auto-evicted. S3 lifecycle rule transitions `cache/*` to Glacier Deep Archive after 365 days of no access (`last_hit_at`-driven). Index row stays in Postgres for visibility (`hit_count`, `last_hit_at`). Restoring a Glaciered entry costs ~$0.01 + a few hours wait — almost always cheaper than re-running OpenAI.

**Cross-run reuse rules:**
1. User A runs scope = {L1, L2, L3} against Jira filter F. Worker computes fingerprints, populates cache for all (lesson, issue) pairs and per-lesson edit plans.
2. User B later runs scope = {L2, L3, L4} against same filter F. L2/L3 hit cache (zero OpenAI cost for those). L4 is a miss; worker calls OpenAI, populates cache. Total OpenAI spend ≈ ⅓ of user A's run.
3. Lesson HTML changes (rebuilt container image with new `2026.1/.../index.html`) → input_payload_sha changes → automatic miss, fresh compute.

---

## 5. Release Tab Redesign

**Page layout:**

```
┌─ Release ─────────────────────────────────────────────────────────────┐
│  [Target version: 2026.1 ▾]  [Filter: course ▾] [LP ▾] [Status ▾]     │
│  [Sync from Skilljar] (last synced 4 min ago by Sam)                  │
│                                                                        │
│  ☐ ▸ fme-form-basic / Connect To Data 2026.1                          │
│      ┌────────────────────────────────────────────────────────────┐   │
│      │ Lesson           │Local│Skilljar│Last push│Conflict│Lock   │   │
│      │ Connect & View   │ ✓   │  ✓     │ Tara    │  ─     │ ─     │   │
│      │ Filter Features  │ ✓   │  ✓     │ Sam 2d  │  ⚠     │ ─     │   │
│      │ Transformer Hub  │ ✓   │  ✓     │ Sam 1h  │  ─     │🔒 Tara │   │
│      └────────────────────────────────────────────────────────────┘   │
│  Selected: 2 lessons    [Build Release Plan]                          │
└────────────────────────────────────────────────────────────────────────┘
```

### Inventory browser
- `POST /api/skilljar-inventory/sync` paginates `GET /lessons` and `GET /courses`, hashes each `content_html`, upserts `skilljar_inventory`. Throttled to one team-wide sync per minute.
- Each row joins `skilljar_inventory` with `skilljar_mapping` and the latest `release_history` row to show: title, mapping status, draft/published, remote `last_modified`, last-pushed-by, conflict indicator (`current_remote_hash != after_hash`), lock status.
- "Sync from Skilljar" timestamp + last-syncer always visible so users know their data freshness.

### Per-lesson history drawer
- `GET /api/skilljar-lessons/{id}/history` returns the last 10 `release_history` rows joined to `users` and `runs`: who pushed, when, from which run, success/failure, conflict warnings.
- Each row links back to the producing run page; one-line diff summary shows lines added/removed.

### Conflict-guard pipeline (every push, every lesson)

```
For each lesson the user wants to release:
  1. acquire row in release_locks (skilljar_lesson_id)
       - locked_by = current user, expires_at = now + 10 min
       - if held by another user: show "Tara is releasing this lesson
         (lock expires in 4 min)" — proceed disabled
  2. fetch live lesson HTML from Skilljar (NOT from cache)
  3. compute current_remote_hash
  4. compare to release_history.after_hash for this lesson's last push
       - match    → proceed
       - mismatch → block; show diff modal; require two-click override:
                    [I've reviewed the diff] then [Overwrite anyway].
                    Override recorded in release_history.conflict_warning_json
  5. PATCH lesson via existing skilljar_release._patch_lesson_html
  6. fetch lesson back, compute after_hash
  7. INSERT into release_history (user, run, before/after hash, status,
     conflict_warning_json if any)
  8. UPDATE skilljar_inventory.content_html_hash
  9. release lock
```

### Locks UX
- TTL 10 min from acquisition. Browser heartbeat every 60s while user is in the release flow refreshes TTL.
- Auto-released on push success/failure/cancel.
- "Force-take lock" button visible when lock is held by another user AND `lock_age > 5 min` (assume the holder walked away). Recorded in an `admin_audit` table even though full RBAC isn't in v1.
- HTMX SSE subscription on the Release page propagates lock changes to other open browsers in near-real-time.

### Bulk actions + filters + manifest summary
- Filters: course, learning path, version, mapping status, conflict status, lock status, last-pushed-by.
- Bulk select via checkbox tree; "Build Release Plan" runs the existing `build_release_plan()` (`pipeline/skilljar_release.py:scan_saved_lessons`) against the multi-selection.
- Manifest summary panel preserved from today's UX: "X lessons will be patched, Y new lessons will be created, Z courses archived, A images uploaded." Dry-run preview before final confirm.

### Migration from `data/skilljar-mapping.json` → RDS
- One-shot script reads JSON, inserts into `skilljar_mapping`, validates row count.
- All read sites in `pipeline/skilljar_push.py:515-565` switch to a `SkilljarMappingRepo` class with row-level updates (eliminates the read-modify-write race in `pipeline/skilljar_release.py:686-690`).
- The legacy JSON file becomes export-only (a download endpoint emits the current mapping if anyone needs it).

### Image dedup
- Before `_s3_put` in `pipeline/skilljar_release.py:127`, compute SHA-256 of file bytes, look up `s3_image_cache`.
- Hit → reuse existing S3 URL, no upload.
- Miss → upload, insert row with `(content_sha256, s3_url, content_type, byte_size)`.

---

## 6. Deployment, CI/CD, IaC

**Infrastructure as code:** AWS CDK in Python. One stack per environment, both in the same AWS account, separated by stack-name prefix + tags. (Two accounts is overkill for 2–5 users.)

```
infra/
  app.py                    # CDK app entrypoint
  stacks/
    network.py              # VPC, subnets, security groups
    data.py                 # RDS, S3 buckets, Secrets Manager refs
    compute.py              # App Runner service, ECR repo, Fargate task def
    observability.py        # CloudWatch alarms, log groups, dashboards
  config/
    staging.py              # smaller RDS, shorter backup retention
    production.py           # larger RDS, 7-day backups
```

**Container:** multi-stage Dockerfile, non-root user, tagged with git SHA. Single image; mode selected by `ENTRYPOINT_MODE=web|worker`. Trivy scan in CI fails the build on HIGH/CRITICAL CVEs that have a fix.

**GitHub Actions workflows:**

```
.github/workflows/
  pr.yml          on: pull_request → ruff + mypy + pytest + container
                  build + container smoke test + Trivy scan. ~5-min wall.

  main.yml        on: push to main → all of the above + push image to ECR
                  with git SHA tag → cdk deploy staging → alembic upgrade
                  staging → Playwright smoke tests against staging URL.

  deploy-prod.yml on: workflow_dispatch (manual) AND tag push v* →
                  GitHub Environment "production" requires manual approval
                  → cdk deploy production → migrations → smoke tests.
```

**Test suite to build (project currently has none).** Necessary to make CI/CD meaningful — without tests, "passes all tests" is empty.

| Layer | Tooling | What it covers |
|---|---|---|
| Unit | `pytest`, `pytest-asyncio` | scope resolution, prompt rendering, cache fingerprint determinism, cost meter math |
| Integration | `pytest` + `moto` (S3, ECS) + `respx` (HTTP) + ephemeral Postgres | one-lesson end-to-end pipeline run; release happy-path + hash-mismatch override path |
| Smoke | `playwright` against staging URL | sign-in, kick off run, watch SSE, view release tab, force-fresh toggle |

**Database migrations:** Alembic. CI runs `alembic upgrade head` against staging on every main deploy. Production migrations run after manual approval, before App Runner service swap.

**Secrets workflow:**
- Secret values populated manually in each env's Secrets Manager once at setup (or rotated). Not in CDK code.
- CDK references the secret ARN; App Runner / Fargate task definitions inject the secret as an env var at container start.
- Local dev keeps `.env` working — only production reads from Secrets Manager.

**Cost guardrails:**
- AWS Budget alarm at $150/mo (email).
- Fargate task `shutdown_at` env enforces a 60-minute wall-clock guard, independent of the OpenAI cost ceiling.
- CloudWatch alarm on `RunCostMeter` exceeded events.

---

## 7. Phasing / MVP Slicing

Sequential rollout: Phase 0 → Phase 1 → Phase 2 → optional Phase 3.

### Phase 0 — Foundation *(~3–4 weeks, blocks everything else)*
*Feature parity in the new architecture. No new user-facing features.*
- FastAPI rewrite, Google SSO, Postgres schema + Alembic, S3 artifact storage, Fargate worker mode, SSE log streaming.
- Run scheduler with concurrency cap (2 team-wide) + cost ceiling ($50/run).
- Migration scripts: `runs.json`, `artifacts/*`, `skilljar-mapping.json`, `update-job.json`, `jira_api_cache.json`.
- CDK stacks for staging + production. GitHub Actions PR + main + manual prod-deploy workflows.
- Initial pytest suite covering pipeline modules.
- **Cutover gate:** dry-run staging for ~1 week, run a real release against staging-mapped Skilljar lessons, then point team at production. Local launcher retired.

### Phase 1 — Shared cache *(~2 weeks)*
- `content_cache` + `s3_image_cache` tables, S3 cache layout under `cache/<kind>/<fingerprint>.json`.
- Wrap-points in `pipeline/assessment.py`, `pipeline/edit_suggestions.py`, `pipeline/manifest.py`, `pipeline/skilljar_release.py` image upload.
- Per-step force-fresh toggles in Configure-Run UI.
- Cache hit/miss + dollar-saved telemetry visible per run.

### Phase 2 — Release tab redesign *(~3 weeks)*
- `skilljar_inventory` + sync endpoint, `release_locks`, `release_history` tables.
- Remote-hash conflict guard with two-click override flow (block-by-default; logged in `release_history.conflict_warning_json`).
- Bulk filters + selection UI, lesson drawer with per-lesson history, manifest summary panel preserved.
- HTMX SSE for live lock-state propagation.

### Phase 3 — Polish *(~1–2 weeks, optional)*
- Cost alarms wired to Slack, SLO dashboards.
- Email notifications on run complete / error / cost-ceiling abort.
- Audit log UI.
- Admin role enforcement (basis for force-take-lock authorization).

**Total:** ~9–11 weeks for one developer working steadily.

---

## ⚠️ IT / Security / Privacy Review

> **For Safe Software's IT team to review before implementation begins.** This section flags every external-facing decision the plan makes so IT, security, and finance can sign off (or push back) up front rather than mid-build. Each subsection lists what we plan to do and the specific questions IT needs to answer.

### A. Google OAuth setup

**What we plan to do:**
- Use Google's standard OpenID Connect "Sign in with Google" — *not* a SAML federation to Safe's IdP and *not* a Workspace Marketplace listing.
- Restrict logins to `@safe.com` by verifying the `hd` (hosted domain) claim in the Google ID token. The `hd` claim is signed by Google itself.
- Request only `openid email profile` scopes. No Drive, Gmail, Calendar, Directory, or Admin SDK access.
- Just-in-time user creation (first sign-in upserts a row in our `users` table). No SCIM provisioning.

**Questions for IT:**
1. Does Safe's Google Workspace have **App Access Control** enabled, requiring IT to allowlist OAuth client IDs before users can grant consent?
2. Can we get an OAuth client created inside **Safe's Google Cloud organization**, with consent screen marked **Internal** (Workspace-tenant-restricted)? This is the recommended path — Google itself blocks non-`@safe.com` users at the consent screen, the app shows up under Safe's GCP for centralized revocation, and we don't need OAuth app verification later.
3. If #2 is slow: is the fallback (an "External" OAuth client in a separate GCP project, with `hd`-check enforced in our code) acceptable as a stopgap?
4. Is there an existing Google Cloud project for internal training tooling we should use, or should we provision a new one?
5. When a Safe employee leaves, what's IT's expectation for offboarding from this app? v1 is manual (`users.is_active = false` + `session_epoch` bump). SCIM is a v2 candidate if needed.

### B. Storing Jira data

**What we plan to do:**
- Keep using the existing Jira REST API integration (`pipeline/jira_api.py`, filter ID configured per-environment).
- Replace `inputs/jira_api_cache.json` with:
  - **S3 (private, KMS-encrypted)** — full issue payloads (title, description, comments, links, custom fields).
  - **RDS Postgres `jira_cache` table** — metadata only (filter_id, fetched_at, S3 key, issue_count).
- Issue *summaries* (key + title + truncated description) are also embedded inside `content_cache` entries used as inputs to OpenAI prompts.
- Read access: only authenticated `@safe.com` users via the API. Raw S3/RDS access requires AWS IAM on the App Runner / Fargate task roles.

**Questions for IT / Security:**
1. **Classification.** Are Jira issues from project `KNOW` (training backlog) considered Public, Internal, Confidential, or Restricted? The plan currently assumes *Internal*.
2. **Retention.** Acceptable retention for the Jira cache? Default proposal: refresh on demand, auto-purge S3 blobs older than 90 days, retain cache index in Postgres for audit.
3. **Field exclusions.** Should we strip any fields before caching or before sending to OpenAI? Candidates: reporter email, comment authors, internal-only comments, attachment URLs.
4. **OpenAI exposure.** Sending Jira issue summaries + descriptions to OpenAI as part of LLM prompts — acceptable? (See section C.)
5. **Ticket linkage.** The `content_cache` and `release_history` tables reference Jira issue keys (e.g., `KNOW-2247`) in their fingerprints / audit log. These keys flow through CloudWatch logs in error paths. Acceptable?

### C. OpenAI API usage

**What we plan to do:**
- Continue using OpenAI's API for two cost centers:
  - **Steps 3–4** — `gpt-4o-mini`, one call per `(lesson, issue)` pair, ~$0.20/run. Prompt contains lesson HTML excerpt + Jira issue title/description.
  - **Step 6** — `gpt-4o`, one call per lesson with medium/high impact, ~$3–5/run. Prompt contains full lesson HTML + aggregated relevant issues + target version.
  - Optional: vision review of lesson screenshots if `ENABLE_VISION_SCREENSHOT_REVIEW=true`.
- **Data sent to OpenAI:** lesson HTML (already publicly hosted at `safeskilljar.s3.amazonaws.com`), Jira issue summaries/descriptions from project KNOW, prompt templates we control.
- **OpenAI's data policy** (current): API inputs/outputs are **not** used to train OpenAI models (default since March 2023). They're retained up to 30 days for abuse monitoring, then deleted. Zero-retention is available via OpenAI's Enterprise tier on request.

**Cost controls baked into the plan:**
- Shared `content_cache` deduplicates calls across users for identical `(lesson, issue, model, prompt_version)` tuples.
- Per-run dollar ceiling (`MAX_RUN_USD`, default $20). The Fargate worker tracks live token spend and aborts if projected total exceeds the ceiling.
- AWS CloudWatch alarms on the OpenAI cost-tracking metric we publish per run.
- Daily/monthly budget alerts on the OpenAI account itself.

**Questions for IT / Security / Finance:**
1. **Account ownership.** Is the OpenAI API key on a Safe corporate account, or a personal/team account? Recommend: corporate OpenAI organization with sub-keys per environment (staging vs production) so usage is auditable.
2. **AI usage policy.** Does Safe have an internal policy governing what data can be sent to third-party LLMs? Does sending lesson HTML + Jira issue descriptions fall within it?
3. **DPA / contractual.** Do we need a Data Processing Agreement signed with OpenAI? Standard API ToS may suffice; the Enterprise tier offers a signed DPA + zero-retention if required.
4. **Budget.** Acceptable monthly cap on OpenAI spend? Plan currently assumes ~$50–150/month at typical run cadence; cache should bring this down meaningfully after a few overlapping runs.
5. **Model allowlist.** Should we restrict to specific OpenAI models, or is the team allowed to swap in newer models as they ship? v1 reads model name from config so swapping is config-only.
6. **Vision scope.** OK to send screenshots (PNGs of FME UI taken from lesson HTML) to OpenAI's vision endpoint when `ENABLE_VISION_SCREENSHOT_REVIEW=true`?
7. **Region.** OpenAI processes requests in US datacenters. Any Safe-internal data-residency requirement that conflicts?

### D. AWS infrastructure

**What we plan to do:**
- New AWS resources: App Runner, Fargate cluster, RDS Postgres, S3 buckets, Secrets Manager, KMS keys, ECR for container images, CloudWatch logs/alarms, IAM roles, optional CloudFront distribution for image hosting.
- Estimated steady-state cost: **~$60–120/month**. Breakdown: App Runner $25, RDS db.t4g.micro $15, S3 + CloudFront $5, Secrets Manager $5, NAT/data $5, plus Fargate run-time variable ($5–30/mo depending on run frequency).
- Region recommendation: **us-west-2** (matches existing `safeskilljar` S3 bucket).
- Networking: small VPC with two private subnets for RDS, App Runner connects via VPC connector. Fargate tasks run in the same private subnets with NAT egress for OpenAI/Jira/Skilljar calls.

**Questions for IT:**
1. **Account.** Which AWS account/org should this live in? Existing internal-tools account, a new sub-account in a Control Tower org, or a brand-new standalone account?
2. **Region.** us-west-2 OK, or is there a corporate preference?
3. **Console access.** Should AWS console access for this account integrate with corporate SSO (AWS Identity Center / SAML)?
4. **Compliance baseline.** Any required hardening (CIS AWS Benchmark, NIST, internal Safe policy)? Current plan implements: encryption at rest (KMS) + in transit (TLS), no public S3 except the image-hosting prefix, IAM least-privilege per task role, CloudTrail enabled.
5. **Network egress.** App calls public OpenAI, Jira, Skilljar, and Skilljar's S3. Any egress allowlist or proxy requirement?
6. **VPC/peering.** Need to peer with any existing Safe AWS resources, or is this fully standalone?
7. **Backup retention.** RDS automated backups default to 7 days. Acceptable, or a longer retention window required?

### E. Data classification & retention summary

| Data | Where | Classification (assumed) | Retention |
|---|---|---|---|
| Lesson HTML (training corpus) | Container image (RO) | Public | Tied to repo / image |
| Jira issue cache | S3 + RDS | Internal | 90 days proposed |
| OpenAI prompt + response logs | RDS `run_logs` | Internal | 90 days proposed |
| Run artifacts (manifest/changelog/recommendations/edit-plans/report) | S3 | Internal | Indefinite (auditable trail of past runs) |
| User identity (name, email, profile picture URL) | RDS `users` | Internal/PII-light | Until offboarded |
| Session cookies | Browser only | — | 14-day rolling |
| Skilljar lesson content + IDs | RDS `skilljar_inventory` | Internal | Refreshed on demand |
| Release history (who pushed what when) | RDS `release_history` | Internal | Indefinite (audit) |

### F. Audit & access controls

- **Skilljar release audit:** every push appends to `release_history` (user, timestamps, before/after content hashes, conflict warnings) — append-only.
- **Authentication:** every successful sign-in updates `users.last_seen_at`. CloudTrail logs IAM/Secrets access.
- **App admin actions** (force-release-over-lock, lock-override) — logged to a dedicated audit table in v2 if those features ship.
- **Infrastructure:** AWS CloudTrail enabled (default). RDS query audit via CloudWatch slow-query log.

### G. Things explicitly NOT in v1 (so IT can flag if any are blockers)

- No SCIM / auto-deprovisioning from Workspace.
- No SAML federation (OIDC sign-in only).
- No app-enforced MFA (relies on Google Workspace MFA settings).
- No per-user OpenAI / Jira / Skilljar credentials (shared service-account keys in Secrets Manager).
- No SOC 2 / ISO 27001 certification of this app.
- No formal DPA with OpenAI (default API ToS).
- No data-residency guarantee beyond the chosen AWS region.
- No PII redaction layer before sending data to OpenAI (lesson HTML and Jira summaries pass through unmodified).

---

## Verification plan

### Phase 0 cutover gate (blocks production cutover)
1. **Sign-in path.** Sign in with @safe.com Google account → user row created → cookie issued. Sign in with non-@safe.com account → rejected at consent screen (Internal app) or by `hd` check (External fallback).
2. **End-to-end run on staging.** From a fresh browser, configure a 1-lesson scope, start a run, watch SSE logs to completion, open the report. Verify `runs`, `run_steps`, `run_logs`, and S3 artifact keys are all populated correctly.
3. **Concurrency cap.** Start 3 runs in quick succession. Confirm 2 dispatch immediately and the 3rd shows "1 ahead of you" until a slot frees.
4. **Cost ceiling.** Set `MAX_RUN_USD=0.10` in staging, start a run that would exceed it. Confirm worker aborts cleanly with status `aborted_cost_ceiling`, partial artifacts retained, error message visible in UI.
5. **Cancellation.** Start a long run; click Cancel; confirm worker exits within ~30s with status `cancelled`.
6. **Resume.** Cancel a run mid-Step-6; click Resume; confirm only the unfinished lesson set is processed and final artifacts are complete.
7. **Real Skilljar release on staging.** Pick one staging-mapped lesson; run the full Release flow (lock → hash check → PATCH → history row). Confirm Skilljar reflects the change, `release_history` has the new row, and the lock is released.
8. **Migration script idempotency.** Run it twice on a copy of production data; confirm second run is a no-op and no rows are duplicated.

### Phase 1 verification
- Run the same 1-lesson scope twice. First run: cache misses + OpenAI calls + populates `content_cache`. Second run: cache hits, zero OpenAI calls, cost meter ≈ $0.
- Toggle "Force fresh assessments" on the second run; confirm only that step pays OpenAI again, others stay cached.
- Edit a prompt template's `# version:` header; confirm fingerprint changes and the cache is bypassed for that prompt.

### Phase 2 verification
- Two browsers, two users. Both open the Release tab and try to release the same lesson. First gets the lock; second sees "User X is releasing this lesson", proceed disabled.
- Manually edit a lesson's HTML in the Skilljar UI to simulate an admin change. Run release on it. Confirm the conflict modal appears with a real diff; confirm both clicks are required; confirm `release_history.conflict_warning_json` captures the mismatched hashes.
- Bulk-select 5 lessons across 2 courses; confirm the manifest summary panel correctly counts patches/creates/archives/images.

### CI/CD verification
- Open a PR. Confirm `pr.yml` runs and gates merge.
- Merge to main. Confirm `main.yml` builds image, deploys to staging, runs migrations, runs Playwright smoke tests, all green.
- Manually trigger `deploy-prod.yml`. Confirm the GitHub Environment approval gate appears and blocks until approved.
