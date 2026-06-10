# EC2 cutover — live progress checklist

> **Purpose:** Resumable state tracker for the Stage 7 cutover. Companion to
> `2026-06-08-ec2-migration-qa-and-cutover.md` (the runbook — *what* each step
> is) and `2026-05-05-multi-user-web-app-ec2-alternative.md` (architecture).
> Update the checkboxes as we go so an interrupted session can pick back up.
>
> **Last updated:** 2026-06-09

## Locked facts (don't re-derive)

| Thing | Value |
|---|---|
| Hostname | `fme-train.base.safe.com` |
| EIP (server) | `44.241.192.143` |
| Office IP (only allowed source) | `72.2.40.92/32` on 22/80/443 |
| Instance | `i-0389b1e00a2661746` (bare as of 2026-06-09) |
| Security group | `sg-0e5a5a8774ee07f9d` |
| TLS | IT `*.base.safe.com` wildcard cert (IS-20384); **no certbot** |
| App dir / env / cert paths | `/opt/fme-train`, `/etc/fme-train/env`, `/etc/ssl/fme-train/{fullchain,privkey}.pem` |
| App ref deployed | `origin/main` (Stage 6 merge confirmed landed) |

## Prerequisite state (2026-06-09)

- [x] DNS resolves → `44.241.192.143` (resolution works from anywhere; TLS reach needs office IP)
- [x] `main` carries `setup-ec2.sh` / `deploy-prod.sh` / deploy workflow / `docs/deployment.md`
- [x] Google OAuth client id + secret in hand
- [x] Wildcard cert assembled — `fullchain.pem` (leaf→DigiCert G2 intermediate→root) + `privkey.pem`, modulus md5 match `fa3af43…`, valid Jul 22 2025 → **Aug 19 2026**. Built from `.p7b`+`.key` (no password). Files in the Downloads cert folder, ready to scp at B3.
- [ ] Stage-7 secrets staged (OpenAI, Jira, Skilljar, SESSION_SIGNING_KEY, S3)

## Open snags to resolve

- [x] ~~**Cert format**~~ RESOLVED — assembled `fullchain.pem`+`privkey.pem` from `.p7b`+`.key`; chain + key verified. (`.pfx` import password was never provided / unknown — sidestepped.)
- [x] **GitHub auth for `fmetrain`:** read-only **deploy key** installed at `/home/fmetrain/.ssh/fme_deploy` (+ `config`, `known_hosts`, all owned by `fmetrain`). `ssh -T git@github.com` returns the "Hi safesoftware/…" line. ✅
- [x] EIP `44.241.192.143` confirmed associated with `i-0389b1e00a2661746` (shows as Public IPv4).
- [x] **Console access:** reached the box via browser **EC2 Instance Connect**. Required a temp SG inbound rule: SSH from `18.237.140.160/29` (EIC us-west-2 range) on `sg-0e5a5a8774ee07f9d`. Revisit at B0.

---

## Repo follow-ups found during cutover
- [ ] `bin/setup-ec2.sh` and `bin/deploy-prod.sh` are committed mode `100644` (not executable). Had to invoke via `sudo bash bin/setup-ec2.sh`. `chmod +x bin/*.sh` and commit so `deploy-prod.sh` / the deploy workflow don't fail to exec.
- [ ] **App is an early-stage skeleton on `main`** (integration is 0 ahead / main 24 ahead — fully merged, not a deploy miss). `/` is the KNOW-2258 *placeholder index* with **no sign-in link** (users have no entry point; must hit `/auth/login` directly). Routers mounted: `health, index, auth, drafts, report_drafts, skilljar, sse` — **no `runs` router**, so `/api/runs` 404s and there's no web UI to launch a pipeline run. ⚠️ **This puts B10 (smoke a real run from the UI) in question** — need to confirm how a run is triggered in this build before B10. Likely product-backlog items, not cutover blockers.
- [ ] Stale references in the QA runbook: `/api/runs → 401` (no such route; 404) and implied GET logout (it's POST-only, 405 on GET).
- [ ] **`setup-ec2.sh` Postgres auth gap:** creates a password role + TCP `DATABASE_URL` (`@127.0.0.1`), but PG16's default `pg_hba.conf` uses `ident` for host connections → `InvalidAuthorizationSpecificationError: Ident authentication failed`. Had to flip the `127.0.0.1/32` + `::1/128` host lines to `scram-sha-256` and `reload postgresql`. setup-ec2.sh should do this (or use a local socket + peer).

## Cutover steps (Stage 7 = Phase B)

### Do-now (laptop, while box is idle)
- [x] Assemble `fullchain.pem` + `privkey.pem`; verified key⇄cert match + CN/SAN + expiry
- [ ] `openssl rand -hex 32` → save as `SESSION_SIGNING_KEY`
- [ ] Collect remaining secrets (OpenAI / Jira×4 / Skilljar×2 / AWS×4)

### B0 — Security group + EIP ✅
- [x] EIP `44.241.192.143` attached to `i-0389b1e00a2661746`
- [x] 443 + 80 from `72.2.40.92/32` (office); 22 from `18.237.140.160/29` (EIC)
- [x] Revoked both `0.0.0.0/0` rules (80 + 443) and the stray `38.145.234.125/32` "claude sandbox" SSH rule. **Office IP confirmed `72.2.40.92` before revoking.**
- **Deviation from plan:** SSH is allowed from the EIC `/29`, not office-IP-only — preserves keyless browser-terminal admin access. Tighten/replace with SSM when KNOW-2330/2309 lands.

### B1 — Secrets staged
- [ ] All values ready to paste into `/etc/fme-train/env` (covered by Do-now)

### B2 — SSH + provision
- [x] Access via browser EC2 Instance Connect (temp SG rule from EIC range)
- [x] GitHub auth for `fmetrain` sorted (read-only deploy key)
- [x] Cloned repo (1.7 GiB, deploy key worked), ran `sudo bash bin/setup-ec2.sh` → `Setup complete`. PG16 + nginx (HTTP-only) + venv + systemd units in place; `DATABASE_URL` candidate in `/etc/fme-train/env.new`.

### B3 — Install cert, enable HTTPS
- [x] Moved `fullchain.pem`/`privkey.pem` to `/etc/ssl/fme-train/` via base64 single-line paste (no scp; heredoc/multiline unreliable in EIC terminal). Key `600` root-owned.
- [x] Re-ran `sudo bash bin/setup-ec2.sh` → "Wildcard cert found… writing HTTPS config", `nginx -t` clean. `curl -k https://127.0.0.1/health` (Host header) → ok.

### B4 — Fill `/etc/fme-train/env`
- [x] Merged `DATABASE_URL` from `.new`; filled `SESSION_SIGNING_KEY`, `GOOGLE_OAUTH_*`, OpenAI/Jira/Skilljar/AWS; `TASK_DISPATCHER=systemd`. No empty values; exactly one active `DATABASE_URL`.

### B5 — Start service
- [x] DB auth fixed (pg_hba scram), migrations 0001–0003 applied, `systemctl --user start fme-train-web` → `active (running)`
- [x] `curl http://127.0.0.1:8000/health` → `{"status":"ok","version":"dev"}`

### B6 — TLS reachability (from office IP)
- [x] `dig`/resolve → EIP
- [x] Added 443+80 from `72.2.40.92/32` to SG; `https://fme-train.base.safe.com/health` loads in browser with **valid padlock** (chain trusted) + `{"status":"ok"}`. HTTP→HTTPS redirect works.

### B7 — Google OAuth
- [x] Added `https://fme-train.base.safe.com/auth/callback` to the OAuth client
- [x] `@safe.com` sign-in via `/auth/login` works (OAuth round-trip + session set, redirects to `/`)
- [x] Non-`@safe.com` rejection confirmed (403). **B7 complete — app is live: provisioned, TLS, Google auth enforcing `@safe.com`.**

### B8 — GitHub Actions deploy (finish KNOW-2293 E2E) — ⛔ DEFERRED
- Workflow runs on `ubuntu-latest` (GitHub-hosted runner) + `appleboy/ssh-action` → SSH to `DEPLOY_HOST`. GitHub runner IPs are neither the office IP nor the EIC range, so the **office-IP lockdown blocks it**. E2E cannot pass as designed.
- **Decision: defer.** Deploy manually via `bin/deploy-prod.sh` on the box for now. Rework KNOW-2293 to SSM send-command (ties KNOW-2330/2309) or a self-hosted runner. Do **not** open 22 to GitHub IP ranges.
- [ ] (later) Rework 2293 deploy path; then set GH secrets + run E2E

### B9 — Backups + patching

**Step 1 — Local nightly DB backup (in the EC2 Instance Connect terminal).**
Paste the single `echo '<base64>' | base64 -d | sudo bash` line provided in the session and press Enter. (It's the heredoc-safe form of a small installer — heredocs typed directly into this terminal get mangled, so it's base64-wrapped.) It installs:
  - `/usr/local/bin/fme-train-backup.sh` — `pg_dump -Fc fme_train` → `/var/lib/fme-train/backups/`, deletes dumps older than 14 days
  - `fme-train-backup.service` (oneshot, `User=postgres`) + `fme-train-backup.timer` (`OnCalendar=*-*-* 08:15 UTC`, `Persistent=true`)
  - …then runs one backup immediately and lists the timer.
  - **Verify:** a `fme_train-<timestamp>.dump` file exists in `/var/lib/fme-train/backups/`, and `systemctl list-timers fme-train-backup.timer` shows a next run.
- [x] **done + verified** — first dump `fme_train-20260609T221800.dump` (78 KB) written; timer next run 2026-06-10 08:15 UTC. (Files built via short `printf|tee` append lines — the base64 one-liner and long `printf` lines got mangled by the EC2 Instance Connect terminal's paste limit.)

**Step 2 — Off-box EBS snapshots (AWS Console).** ⛔ **Blocked on IAM (IT).**
DLM (and AWS Backup) need a service role; the `TrainPower` SSO role has no IAM write, so creating `AWSDataLifecycleManagerDefaultRole` fails (`iam:GetRole` denied). **Bundle into one IT/IAM request with KNOW-2330 (SSM instance role) + KNOW-2309 (dedicated app IAM):** (1) `aws dlm create-default-role`, (2) `AmazonSSMManagedInstanceCore` on `i-0389b1e00a2661746`, (3) dedicated app IAM to retire shared `fmetraining` creds + allow `pg_dump`→S3.
Interim: a **manual one-off snapshot** ✅ taken 2026-06-09 (`fme-train baseline 2026-06-09`) — `ec2:CreateSnapshot` works under TrainPower. Consolidated IAM ask posted to KNOW-2309. Data also protected by the nightly `pg_dump`.
- [ ] (IT) DLM default role created, then create the daily snapshot policy

**Step 3 — Patching (in the terminal).**
```
sudo dnf install -y dnf-automatic
sudo systemctl enable --now dnf-automatic.timer
```
Default is download-only; to auto-apply security updates set `apply_updates = yes` in `/etc/dnf/automatic.conf`.
- [ ] done

**Deferred:** shipping the `pg_dump` files off to S3 needs a proper IAM role (box creds are image-upload-scoped) — folded into KNOW-2309.

### B10 — Full smoke
**Finding (2026-06-09):** the deployed app (`main`) has the full run *execution* backend — `RunScheduler` (live, polls `runs` for `status='queued'`), `SystemdTaskDispatcher` (spawns `fme-train-worker@<id>`), `worker.py`, SSE logs, drafts routes — but **no route/service to *create* a run.** Only `scripts/migrate/seed_runs.py` / direct DB insert make a `Run` row. So "launch a run from the UI" is not possible on `main` (the launch UI is unmerged/unbuilt; `main` == integration). ⚠️ App is not end-user-usable for *starting* runs until that lands.
**Finding 2 (bigger):** the worker runs `_stub_step_body` — its docstring says *"Placeholder until the real pipeline integration ships."* `worker.py` calls `run_worker()` without a real `step_body`, so the deployed worker logs 6 stub steps and produces **no real lesson content** (no Jira/OpenAI). So the deployed app is multi-user *scaffolding*: lifecycle (scheduler/worker/steps/logs/cost/SSE) is real, but **(a) no run-creation UI/endpoint and (b) the real pipeline isn't integrated**. Two backlog stories needed before the app is actually usable.
- [x] Backend smoke **PASSED** (run `smoke-20260610-01`): scheduler claimed the queued run → `systemd` worker ran → 6 steps `done` → full lifecycle logged in `run_logs`, status `done`. (Steps are stubs, so no real content — safe, no cost. journalctl `--user` read fails (same quirk as web svc); use `sudo journalctl _SYSTEMD_USER_UNIT=…` if needed.)
- [x] Decomposition gap audited + filed: **KNOW-2334** (integrate real pipeline into worker — follow-up to KNOW-2270, which was closed but shipped only scaffolding; commented + Relates-linked) and **KNOW-2335** (run-creation UI/endpoint — genuinely missing story; KNOW-2334 Blocks it). Both Component=Development, ref KNOW-2257 umbrella.

---

## Post-cutover follow-ups
- [ ] KNOW-2309 (dedicated IAM + SSM, retire shared `fmetraining` creds)
- [ ] Delete redundant `feature/multi-user-web-app-ec2-pivot` branch
- [ ] Close KNOW-2257/2294/2295/2298; transition KNOW-2293/2296 → Done
- [ ] **Cert renewal reminder** — `*.base.safe.com` wildcard expires **Aug 19 2026** (~10 weeks out). File a reminder so TLS doesn't lapse; renewal is a manual re-issue from IT (no certbot).
