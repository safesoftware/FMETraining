# EC2 migration — QA plan & cutover runbook

> **Status:** Active, created 2026-06-08. Companion to
> `2026-05-05-multi-user-web-app-ec2-alternative.md` (the architecture +
> first-time-deploy runbook). That doc says *what* we deploy; this doc says
> *what to QA, in what order, before we cut over*, then how to cut over.
>
> **Audience:** Sam (operator + QA). Steps marked **[human]** need a person
> clicking/looking; steps marked **[auto]** are commands with expected output.

---

## 0. Where the code is (verified 2026-06-08)

| Branch | Carries | Merged to `main`? |
|---|---|---|
| `feature/multi-user-web-app` (**integration**) | Full app, auth, DB, worker, `SystemdTaskDispatcher`, `bin/setup-ec2.sh`, **basic** `bin/deploy-prod.sh`, `docs/deployment.md`, latest Phase-0 QA fixes | **No** (12 behind / 74 ahead of main) |
| `feature/multi-user-web-app-KNOW-2296` | **Hardened** `deploy-prod.sh` (`--rollback`, `DEPLOY_DRY_RUN`, last-good-sha, auto-rollback) | No (16 behind integration) |
| `feature/multi-user-web-app-KNOW-2293` | `.github/workflows/deploy-prod.yml` (one-button deploy) | No (16 behind integration) |
| `feature/multi-user-web-app-ec2-pivot` | *Redundant* — fully merged ancestor of integration | n/a (delete after cutover) |

**Consequence:** `bin/deploy-prod.sh` does `git reset --hard origin/main`, and
`setup-ec2.sh` is not on `main`. **The integration branch (with 2293/2296
folded in) must land on `main` before the box can provision/deploy.** That
merge is the *last* QA stage, not the first.

## IT decisions now locked (IS-20384, Michael Steele)

- **Hostname:** `fme-train.base.safe.com` → `44.241.192.143` (A record being created).
- **Access model:** **office IP `72.2.40.92` only** on 22/80/443 — *not* VPN-wide. Obscure name + IP allowlist is the security posture.
- **TLS:** IT-issued **`*.base.safe.com` wildcard cert** (Drive folder on the ticket). **No certbot / Let's Encrypt.**
- Patch regularly (`dnf-automatic`) or SSM Patch Manager.

> Code still says `fme-train.safe.com` + certbot in `setup-ec2.sh` and
> `docs/deployment.md`. Fixing that is **Stage 4** below (KNOW-2295 / 2298).

---

## QA order (dependency-driven)

```
Stage 1  Baseline: integration branch boots, suite green, lint clean
            │
Stage 2  KNOW-2274  pushed-lesson image URL re-hosting (Ready for QA)
            │
Stage 3  KNOW-2296  hardened deploy-prod.sh   (Ready for QA) ─┐
Stage 4  KNOW-2293  GitHub Actions deploy     (Ready for QA) ─┤ fold into integration
Stage 5  KNOW-2295 + KNOW-2298  pivot/host/TLS cleanup + setup-ec2 provisioning ─┘
            │
Stage 6  Merge integration → main (resolve 3 conflicts), full suite green on result
            │
Stage 7  CUTOVER (Phase B of the EC2 plan) — provision box, TLS, OAuth, smoke
```

Rationale: each later stage depends on the earlier one being green. The two
Ready-for-QA deploy tickets (2296, 2293) and the cleanup (2295/2298) all need
to be on integration *before* Stage 6, because Stage 6 is what publishes a
self-consistent `main` for the box to pull.

---

## Stage 1 — Baseline of the integration branch

This is the merge candidate. Confirm it's healthy before stacking anything.

1. **[auto]** Check out and sync:
   ```bash
   git fetch origin -q
   git checkout feature/multi-user-web-app && git pull --ff-only
   ```
2. **[auto]** Full suite in the container stack:
   ```bash
   make up            # app + postgres + minio
   make test          # pytest inside the app container
   ```
   Expect: all of `tests/unit`, `tests/integration`, `tests/mocked_llm`,
   `tests/browser` pass; no errors. Note any `xfail`/skips and confirm they're
   intentional.
3. **[auto]** Lint/format clean:
   ```bash
   make lint
   ```
   Expect: ruff reports no issues.
4. **[human]** Smoke the running app at `http://localhost:8000`:
   - `/health` returns `{"status":"ok",...}`.
   - Google sign-in redirects; a non-`@safe.com` identity is rejected; a
     `@safe.com` identity lands on the dashboard.
   - `curl -i http://localhost:8000/api/runs` while logged out → **401**.
5. **[human]** Launch one small pipeline run from the UI; watch the SSE log
   stream; confirm it reaches a terminal state and a draft is saved.

**Gate:** suite green + lint clean + the 5 smoke checks pass. ❌ any failure → stop, fix on the branch, re-run Stage 1.

## Stage 2 — KNOW-2274 (pushed lessons: `localhost:8080` image URLs)

*Ticket verification (from KNOW-2274):* a contenteditable edit must not leave
absolute `http://localhost:8080/.../images/...` URLs in saved/pushed HTML;
they must be re-hosted to S3 by filename match.

1. **[auto]** Locate the fix and confirm it's in the merge path:
   ```bash
   git grep -n "location.origin" pipeline/report.py          # leGetCleanHtml strip step
   grep -rn "def upload_lesson_images" pipeline/lesson_image_upload.py
   pytest tests/unit -k "image_upload or clean_html or sanitize" -q
   ```
2. **[human]** In the Lesson Edits tab, open a lesson, toggle a block format
   (e.g. heading↔paragraph) on a paragraph that contains a relative
   `images/safe_note.png`, then **Save to Version Folder**.
3. **[human]** Inspect the written `index.html`:
   ```bash
   grep -n "localhost:8080" "<lesson>/index.html"   # expect: no matches
   grep -n "img src" "<lesson>/index.html"          # srcs are S3 or relative images/
   ```
4. **[human]** Push to Skilljar (a test lesson), wait, reload the live lesson →
   all images render (no 403/unreachable).

**Gate:** no `localhost:8080` survives a save **or** a push; images resolve live.

## Stage 3 — KNOW-2296 (hardened `bin/deploy-prod.sh`)

*Ticket verification:* pre/post `/health` gates, atomic checkout, conditional
deps, migrations fail-loud, last-good-sha, auto-rollback, standalone
`--rollback`, shellcheck-clean, dry-run swaps `systemctl` for `echo`.

1. **[auto]** From `feature/multi-user-web-app-KNOW-2296`:
   ```bash
   shellcheck bin/deploy-prod.sh           # expect: clean
   bash -n bin/deploy-prod.sh              # syntax ok
   grep -nE "set -euo pipefail|DEPLOY_DRY_RUN|last-good-sha|--rollback" bin/deploy-prod.sh
   ```
2. **[auto]** Dry-run against the Compose stack (no real systemctl):
   ```bash
   make up
   DEPLOY_DRY_RUN=1 APP_DIR=$(pwd) bash bin/deploy-prod.sh
   ```
   Expect: every `[deploy]` step logs; restart steps print an `echo`/skip
   line, not a real `systemctl`; exits 0.
3. **[human]** Simulate a broken post-deploy `/health` (start the app with a
   forced exception in startup, or point the health check at a dead port) and
   run the script → confirm it **auto-rolls back** to the last-good SHA and
   exits non-zero with the rollback one-liner printed.
4. **[human]** Run the standalone rollback path and confirm idempotence:
   ```bash
   bash bin/deploy-prod.sh --rollback     # returns to last-good SHA, services healthy
   ```

**Gate:** shellcheck clean; dry-run makes no real state change; auto-rollback
fires on health failure; `--rollback` is idempotent. Then **merge 2296 →
integration** and transition KNOW-2296 to Done.

## Stage 4 — KNOW-2293 (GitHub Actions deploy workflow)

*Ticket verification:* graceful no-op when `DEPLOY_HOST` unset; SHA-pinned
actions; concurrency group; once secrets+box exist, end-to-end < 90 s with
auto-rollback on health failure.

1. **[auto]** From `feature/multi-user-web-app-KNOW-2293`, lint the workflow:
   ```bash
   git show :.github/workflows/deploy-prod.yml | grep -nE "uses:.*@[0-9a-f]{40}"   # SHA-pinned, not tags
   grep -nE "workflow_dispatch|concurrency|DEPLOY_HOST" .github/workflows/deploy-prod.yml
   ```
   (Optionally `actionlint .github/workflows/deploy-prod.yml`.)
2. **[human]** With **no** `DEPLOY_HOST` secret set, trigger the workflow via
   the Actions tab (`Run workflow` on `main`) → it prints
   `DEPLOY_HOST not set; skipping deploy` and the run is **green** (exit 0).
3. Full end-to-end (push→deploy, broken-health→rollback, dispatch-specific-SHA)
   is **deferred to Stage 7** — it needs the live box + the three GH secrets
   (`DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`).

**Gate:** actions SHA-pinned + concurrency set + graceful skip verified. Then
**merge 2293 → integration** and transition KNOW-2293 (note: its E2E
acceptance completes in Stage 7).

## Stage 5 — KNOW-2295 + KNOW-2298 (host/TLS cleanup + setup-ec2 provisioning)

These reconcile the code with the locked IT decisions. **Being implemented in
Phase A of this migration** (see the cutover plan). QA after implementation:

1. **[auto]** Hostname + TLS reconciled (no stale references, no certbot):
   ```bash
   git grep -n "fme-train\.safe\.com" -- bin/ docs/ app/      # expect: none (all base.safe.com)
   git grep -n "certbot" -- bin/setup-ec2.sh                  # expect: none
   grep -nE "ssl_certificate|listen 443|72\.2\.40\.92|base\.safe\.com" bin/setup-ec2.sh
   ```
2. **[auto]** `setup-ec2.sh` provisions state dirs (KNOW-2298):
   ```bash
   grep -nE "/var/lib/fme-train" bin/setup-ec2.sh             # created, owned by fmetrain
   ```
   Confirm the scheduler-unit story is documented (in-process vs separate unit).
3. **[auto]** Plan/docs consistency:
   ```bash
   ls docs/plans/                                             # stale plan archived under archive/
   sed -n '1,30p' docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md   # Status & prerequisites block present
   pytest -q                                                  # no functional regressions
   ```
4. **[human]** Read `docs/deployment.md` end-to-end as a non-developer: every
   hostname is `fme-train.base.safe.com`; the TLS section describes the
   wildcard cert (not certbot); access model mentions the office IP.

**Gate:** all greps return the expected (empty where noted); suite green.

## Stage 6 — Merge integration → `main`

1. **[auto]** Merge `origin/main` into integration, resolving the 3 known
   conflicts:
   - `AGENTS.md` — keep the **superset** (main's expanded conventions + the
     branch's QA-steps-belong-on-the-ticket rule + the `docs/deployment.md`
     listing line).
   - `docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md` — take the
     reconciled Stage-5 version (base.safe.com + wildcard TLS + Status block).
   - `pipeline/report.py` — combine the WYSIWYG work from main (KNOW-2275/2279
     lists, image insert/replace) with the integration-branch report changes.
     **Resolve carefully; this is the only code conflict.**
2. **[auto]** After resolving:
   ```bash
   make test && make lint          # green on the merged result
   git grep -n "<<<<<<<\|>>>>>>>"  # expect: no conflict markers
   ```
3. **[human]** Re-run the Stage-1 app smoke checks on the merged result
   (sign-in, a run, a lesson edit incl. lists + image insert) — the report UI
   is what the conflict touched, so exercise it directly.
4. Open `integration → main` PR; `/security-review` on the diff (deploy/setup
   scripts, auth, secrets handling); merge after review.

**Gate:** merged `main` is suite-green, lint-clean, marker-free, and the report
UI smoke passes. `main` now carries `setup-ec2.sh` + a deploy-ready tree.

## Stage 7 — Cutover (Phase B of the EC2 plan)

Driven by Sam over SSH/AWS; I guide each step. Summary (full detail in the
EC2-alternative runbook, adjusted for the locked IT decisions):

- **B0** SG `sg-0e5a5a8774ee07f9d`: 22/80/443 from `72.2.40.92` only; revoke `from anywhere`.
- **B1** Stage secrets (OpenAI, Jira, Skilljar, Google OAuth id+secret, `SESSION_SIGNING_KEY=$(openssl rand -hex 32)`, S3 creds).
- **B2** SSH in → clone to `/opt/fme-train` → `sudo bin/setup-ec2.sh` (clones `origin/main`).
- **B3** Install the `*.base.safe.com` wildcard cert: download from IT's Drive folder, scp `fullchain.pem`+`privkey.pem` to `/etc/ssl/fme-train/`, `nginx -t && systemctl reload nginx`.
- **B4** Fill `/etc/fme-train/env` (DB URL from the `.new` sidecar + secrets).
- **B5** `systemctl --user start fme-train-web`; `curl 127.0.0.1:8000/health` → ok.
- **B6** From the office IP: `dig fme-train.base.safe.com` → EIP; `curl https://fme-train.base.safe.com/health` over TLS.
- **B7** Add `https://fme-train.base.safe.com/auth/callback` to the Google OAuth client; sign-in test.
- **B8** Set the three GH secrets → finish KNOW-2293 E2E (push→deploy, broken-health→rollback, dispatch a specific SHA).
- **B9** Backups (nightly `pg_dump`→S3 + EBS snapshot) and patching (`dnf-automatic`/SSM).
- **B10** Smoke: sign in, run a real pipeline, watch the worker via `journalctl`, confirm completion + draft saved + (optional) Skilljar push.

**Post-cutover follow-ups:** KNOW-2309 (dedicated IAM + SSM, retire shared
`fmetraining` creds), delete the redundant `ec2-pivot` branch, close
KNOW-2257/2294/2295/2298 and transition 2293/2296 to Done.

---

## Pre-cutover gate checklist (must all be ✅ before Stage 7)

- [ ] Stage 1 baseline green (suite, lint, app smoke)
- [ ] KNOW-2274 verified (no `localhost:8080` in saved/pushed HTML)
- [ ] KNOW-2296 verified + merged to integration
- [ ] KNOW-2293 graceful-skip verified + merged to integration
- [ ] KNOW-2295 / 2298 cleanup verified (hostname=base.safe.com, no certbot, /var/lib provisioned)
- [ ] integration → main merged; merged `main` suite-green, marker-free; security review done
- [ ] DNS `fme-train.base.safe.com` resolves to the EIP from the office IP
- [ ] `*.base.safe.com` wildcard cert in hand (Drive folder)
- [ ] Google OAuth client id+secret in hand; callback URL ready to add
- [ ] All Stage-7 secrets staged
