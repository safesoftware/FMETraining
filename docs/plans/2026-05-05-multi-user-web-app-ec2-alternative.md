# Deployment: single EC2 + local services

> **Status:** Approved 2026-05-05. Active deployment plan for v1.
> Replaces `2026-05-05-multi-user-web-app-deployment.md` (kept on disk
> as a record of the original heavier shape, marked superseded).
>
> **Update 2026-06-04 — VPN access.** IT requires the app to sit behind
> their VPN. The hostname is **`fme-train.base.safe.com`** and only
> resolves / is routable from inside the VPN — you must be on the VPN to
> reach it. Two consequences are **open IT asks**, not yet decided:
> (1) **TLS** — the Let's Encrypt HTTP-01 flow (`certbot --nginx`) below
> needs inbound port 80 from the public internet, which the VPN likely
> removes; the cert mechanism (DNS-01 vs. an IT-issued internal cert)
> is TBD with IT. (2) **Ingress** — the `80+443 from anywhere` security
> group rule should likely tighten to the VPN CIDR; range TBD from IT.
> Both are flagged inline below.
>
> The architecture in `2026-04-29-multi-user-web-app.md` is still the
> source of truth for application design (FastAPI, Postgres schema,
> run lifecycle, content cache, release tab) — only the deployment
> stack changes here.

---

## First-time deployment runbook

The steps below take us from "we have an idea" to "the team can sign in at the URL." Step 1 (infra) is **done**; the only open IT asks are the DNS record and the Google OAuth client. Steps 2, 3, 5 are things **I** do over an SSH session with you watching.

### Step 1 — Instance, Elastic IP, and DNS *(done 2026-06-04)*

The instance, Elastic IP, security group, and key pair were created directly via the AWS API (boto3) using the account's existing credentials — not via an IT ticket. Provisioned resources (account `201369646709`, us-west-2):

| Resource | Value |
|---|---|
| Instance | `i-0389b1e00a2661746` — `t4g.small`, Amazon Linux 2023 ARM64, 30 GB gp3 (encrypted) |
| VPC / subnet | `vpc-01d6d635aa6fd6181` (FME Training-vpc) / `subnet-081826309e7c2e41c` (public1-us-west-2a) |
| Security group | `sg-0e5a5a8774ee07f9d` (`fme-train`): 22/tcp from the operator IP, 80+443/tcp from anywhere — ⚠️ **to tighten to the VPN CIDR** (range TBD from IT, see Step 4) |
| Elastic IP | **`44.241.192.143`** (`eipalloc-034acf685f5906c51`) |
| Key pair | `fme-train` (ed25519) |
| SSH | `ec2-user@44.241.192.143` |

> ⚠️ Provisioned using the shared `fmetraining` IAM user (the S3 service account), and SSH is currently pinned to a single operator IP. Both are tracked for cleanup — dedicated IAM principal + SSM-based access — in **KNOW-2309**.

**Remaining IT asks** (filed in the `IS` service desk):

- **DNS** (**IS-20384**): VPN-internal `A` record `fme-train.base.safe.com` → `44.241.192.143` (TTL 300), resolvable only from inside the VPN. ⚠️ Because the host is no longer publicly reachable, the Let's Encrypt HTTP-01 flow in Step 4 won't work as written — **confirm the TLS mechanism with IT** (DNS-01 challenge, or an IT-issued internal/`*.base.safe.com` cert).
- **VPN ingress** (**IT ask, TBD**): the VPN CIDR range to scope the security group's 80/443 rule to (replacing `from anywhere`). Request alongside the DNS record.
- **Google OAuth client** (**IS-20383**): Internal-consent Web client in Safe's GCP; see Step 4 for the redirect URIs.

### Step 2 — Provide secrets you'll need *(you, in parallel)*

Gather these so they're ready to paste into `/etc/fme-train/env` in step 3:

```
[  ] OpenAI API key
[  ] Jira base URL, user email, API token, filter ID
[  ] Skilljar API key (use existing for now; rotate to a service-account key later)
[  ] Google OAuth client ID + secret  (requested from IT in IS-20383; Internal-consent Web client)
[  ] Session signing key (just run `openssl rand -hex 32` in your terminal)
[  ] AWS access key + secret for S3 image upload (existing `fmetraining` IAM user keys in .env — to be replaced per KNOW-2309)
```

### Step 3 — Provision and start the app *(I drive, you watch)*

Once you have ssh access to the instance, do this together. Total wall time ≈ 15 minutes.

```bash
# 1. SSH in
ssh ec2-user@<instance-public-dns>

# 2. Clone the repo and run the provisioner. setup-ec2.sh is idempotent —
#    safe to re-run if anything goes sideways.
sudo dnf install -y git
sudo git clone https://github.com/safesoftware/fme-training-automation.git /opt/fme-train
cd /opt/fme-train
sudo bin/setup-ec2.sh
# This installs Postgres + Nginx + Python + the venv, creates the
# `fmetrain` user with linger enabled, writes the systemd units, and
# leaves /etc/fme-train/env as a placeholder.

# 3. Drop your secrets into the env file. The file is chmod 600, root-owned.
sudo $EDITOR /etc/fme-train/env
# Fill in every value listed in step 2. Important: keep the
# `DATABASE_URL=postgresql+asyncpg://fmetrain:<password>@127.0.0.1:5432/fme_train`
# line that setup-ec2.sh wrote to /etc/fme-train/env.new — copy that
# password into the main env file.

# 4. Start the web service (run as the fmetrain user via its user-mode systemd).
sudo -u fmetrain XDG_RUNTIME_DIR=/run/user/$(id -u fmetrain) \
  systemctl --user start fme-train-web

# 5. Confirm /health responds locally.
curl http://127.0.0.1:8000/health
# Expect: {"status":"ok","version":"...","environment":"production"}
```

### Step 4 — Wire up TLS and the Google OAuth callback *(you, ~5 min)*

**You must be connected to the VPN for the steps below** — `fme-train.base.safe.com`
only resolves and routes from inside it.

```bash
# 1. Confirm DNS resolves (while on the VPN)
dig +short fme-train.base.safe.com
# Expect: the EIP from step 1
```

**2. TLS — ⚠️ open IT decision.** The previous `certbot --nginx` command
used the Let's Encrypt **HTTP-01** challenge, which needs inbound port 80
from the public internet. Behind the VPN the host isn't publicly reachable,
so that challenge can't complete. Confirm the approach with IT, then use one of:

- **Let's Encrypt DNS-01** — `certbot certonly --dns-<provider>` (or a manual
  `--preferred-challenges dns` run with IT adding the TXT record). Works
  without public reachability; wire the issued cert into the nginx server block.
- **IT-issued cert** — an internal-CA or `*.base.safe.com` wildcard cert
  supplied by IT, installed directly into nginx (no certbot). Set up renewal
  per IT's process.

```bash
# 3. Confirm /health is reachable over the VPN
curl https://fme-train.base.safe.com/health
# Expect: {"status":"ok",...}
```

Then in the Google Cloud OAuth client (the one you created in B6 of the
original deployment doc), add `https://fme-train.base.safe.com/auth/callback`
to "Authorized redirect URIs". Save.

### Step 5 — Routine deploys after this *(you, ~30 sec each)*

```bash
ssh fmetrain@fme-train.base.safe.com             # via the VPN
bash /opt/fme-train/bin/deploy-prod.sh           # default: deploy origin/main
bash /opt/fme-train/bin/deploy-prod.sh some-tag  # deploy a specific ref
```

The script captures the previous SHA before deploying, so a bad deploy is reversible by:

```bash
cd /opt/fme-train && git reset --hard <prev-sha> && systemctl --user restart fme-train-web
```

The deploy script prints that exact one-liner if the post-deploy health check fails.

---

## Context

The audience is **2–5 people on the Knowledge team**. Traffic is, at peak, a
few simultaneous HTTP requests plus 1–2 background pipeline runs (which
spend 95% of their time waiting on OpenAI / Skilljar / Jira anyway). There
is no SLA, no external customer, no compliance regime beyond Safe's
internal `@safe.com`-restricted access. Downtime measured in minutes is
fine; downtime measured in hours is fine on a weekend.

The original plan was scoped as if this were a customer-facing product:
multi-AZ RDS with backups, Fargate per-run isolation, App Runner managed
deploys, CloudFront CDN, KMS, Secrets Manager, full CDK IaC across staging
+ production environments. Each of those decisions makes sense in
isolation; together, on a 5-user internal tool, they are over-engineered.

This document proposes the simpler alternative IT is steering us toward:
**one Linux VM running the FastAPI app, the worker, Nginx, and Postgres on
the same box.**

---

## Architecture (Plan B)

```
Browser  ── HTTPS ─►  Nginx (TLS, Let's Encrypt)  ─►  Uvicorn (FastAPI on :8000)
                                                          │
                                  ┌───────────────────────┼─────────────────┐
                                  │                       │                 │
                                  ▼                       ▼                 ▼
                          Postgres 16            Worker (forked              Local disk:
                          (localhost)            subprocess per run)        /var/lib/fme-train/
                                                  ▲                          (artifacts +
                                                  │ run_logs / runs           drafts)
                                                  ▼
                                           OpenAI · Jira · Skilljar
                                                  │
                                                  ▼
                                          AWS S3 (image hosting only —
                                          Skilljar embeds image URLs)
```

### One EC2 instance

- **Type:** `t4g.small` (Graviton, 2 vCPU, 2 GB RAM, ARM). Plenty for a
  FastAPI app + Postgres at this scale.
- **OS:** Amazon Linux 2023 (or Ubuntu 24.04 — either is fine; AL2023 ships
  with newer Postgres in dnf and has a smaller AWS support gap).
- **Disk:** 30 GB gp3 EBS volume. Encrypted at rest by default.
- **Network:** default VPC, public subnet, security group allowing:
  - port 22 from your IP (or via Session Manager — see below)
  - port 80 + 443 — ⚠️ **scope to the VPN CIDR** (range TBD from IT), not
    `from anywhere`, since access is VPN-only. (If TLS ends up using Let's
    Encrypt DNS-01 or an IT-issued cert, port 80 needn't be open publicly.)
  - no other inbound
- **Address:** Elastic IP attached so a stop/start doesn't change DNS. Reached
  via `fme-train.base.safe.com`, which IT resolves only inside the VPN.

### Services on the box

All managed by `systemd`:

| Unit | Runs | Notes |
|------|------|-------|
| `postgresql.service` | Distro-provided Postgres 16 | DB lives at `/var/lib/postgresql`. Tuning: keep defaults — load is tiny. |
| `nginx.service` | Reverse proxy + TLS termination | Single server block proxying to `127.0.0.1:8000`. Lets Encrypt cert via certbot, auto-renewing cron. |
| `fme-train-web.service` | `uvicorn app.main:app --host 127.0.0.1 --port 8000 --workers 2` | The FastAPI app. `--workers 2` because at 5 users we want a tiny bit of HTTP concurrency, not because we need to scale. |
| `fme-train-scheduler.service` | The scheduler half of `app/services/run_scheduler.py` | Continues to run as a background asyncio task in the FastAPI process — no separate unit needed, actually. (Listed here only to make explicit the same code path applies as Plan A.) |
| (per-run, on-demand) `fme-train-worker@<run_id>.service` | `python -m worker` with `RUN_ID=...` injected | Templated systemd unit so each pipeline run gets its own service instance. Scheduler invokes `systemd-run --unit=fme-train-worker@<id> ...`; status visible in `systemctl status`. |

The worker model maps cleanly to what we already built in PR #5: a new
`SystemdTaskDispatcher` replaces `EcsRunTaskDispatcher`, calling
`systemd-run` instead of `ecs.RunTask`. `RunScheduler`, `RunCostMeter`,
`RunLogger`, `WorkerLifecycle`, the Postgres schema — all unchanged.

### Local Postgres, not RDS

- Runs on `localhost` — no network exposure.
- Backed up via nightly `pg_dump | gzip | aws s3 cp …` cron job to a private
  S3 bucket. ~30 days retention.
- An EBS snapshot of the whole disk runs daily via a small AWS Backup plan
  (or a cron'd `aws ec2 create-snapshot`). Restore = launch new EC2 from
  snapshot, attach EIP, done.
- Migrations: `alembic upgrade head` runs in the `fme-train-web.service`
  ExecStartPre, so every deploy that touches the schema upgrades atomically
  with the code that needs it.

### Drafts and artifacts on local disk

`/var/lib/fme-train/{artifacts,drafts}/<run_id>/...`. With ~5 users doing a
few runs a week each, a 30 GB volume holds many years of run output. We
S3-archive anything older than 90 days via a cron + `aws s3 sync`.

The exception: lesson **images** Skilljar embeds in published lessons
*must* live behind a public URL Skilljar can hit. Those continue to upload
to the existing S3 bucket Sam already operates (the legacy
`fmetraining` IAM user's bucket from PR #5's probe). No CloudFront — the
S3 URL is already HTTPS and free egress within AWS region or to Skilljar's
servers is small.

### TLS + DNS

- **DNS:** ask IT to add a **VPN-internal** `A` record
  `fme-train.base.safe.com` → the EIP. Resolvable only from inside the VPN,
  so the app is unreachable from the public internet.
- **TLS — ⚠️ open IT decision.** certbot's `--nginx` (HTTP-01) plugin needs
  public port-80 reachability, which the VPN-only setup removes. Confirm with
  IT and use either Let's Encrypt **DNS-01** (`certbot certonly`, TXT-record
  challenge, auto-renews via systemd timer) or an **IT-issued internal /
  `*.base.safe.com` cert** installed directly into nginx. See Step 4.

### Auth

Same Google OIDC flow as Plan A — `authlib` + `itsdangerous`-signed cookies
+ `hd == safe.com` check. The deployment doesn't change the auth code at
all; Sam still creates an OAuth client in Safe's GCP, redirect URL is
`https://fme-train.base.safe.com/auth/callback`. (Google's OAuth endpoints
are reached from the user's browser, which is on the VPN — the callback
redirects back to the VPN-internal host, so the flow works as long as the
user is connected to the VPN.)

### Secrets

A single root-readable `/etc/fme-train/env` file holds the dozen secrets
(OpenAI / Jira / Skilljar / Google OAuth / session signing / DB password).
The systemd unit references it via `EnvironmentFile=`. No Secrets Manager,
no KMS, no boto3 lookup at startup. Permissions: `chmod 600`, owner root.

> **Why not Secrets Manager?** It's $0.40 per secret per month and adds an
> AWS API dependency at startup. For a single VM, the OS file-permission
> model is sufficient — the only people with shell access are the same
> people who'd have IAM access to read Secrets Manager anyway.

### Deployment

`git pull && systemctl restart fme-train-web` from inside an SSH session.
Or, for slightly more discipline, a one-line shell script
`bin/deploy-prod.sh` that does:

```bash
set -euo pipefail
cd /opt/fme-train
git fetch origin && git reset --hard origin/main
/opt/fme-train/.venv/bin/pip install -q -r requirements.txt
/opt/fme-train/.venv/bin/alembic upgrade head
sudo systemctl restart fme-train-web
```

GitHub Actions can run this remotely on tag-push if we want CI/CD —
straightforward via SSM or an ed25519 deploy key — but it's not required.

### Observability

- App + Nginx logs go to `journalctl` (systemd unit logs) and `/var/log/nginx/`.
- A 5-line shell uptime monitor cronned every 5 minutes:
  `curl --fail https://fme-train.base.safe.com/health || mail -s 'fme-train down' team@…`
  (runs on the box itself, so it reaches the host over the VPN-internal name)
- AWS CloudWatch agent installed only if Sam wants metrics; not required.

### Hardening checklist

- Unattended-upgrades for OS security patches (1-line config).
- `fail2ban` watching SSH and 401s on the app (optional, AL2023 ships it).
- AWS SSM Session Manager enabled so we can disable port 22 entirely once
  SSM works for ops. (One IAM role attached to the instance.)

---

## What's reusable from the work already done

The Phase 0 PRs that have merged into `feature/multi-user-web-app` and the
worker+scheduler PR open today are **almost entirely reusable**:

| Component | Plan A | Plan B | Notes |
|-----------|:------:|:------:|-------|
| FastAPI app skeleton (KNOW-2258) | ✅ | ✅ | Identical. |
| SQLAlchemy + Alembic (KNOW-2260) | ✅ | ✅ | Identical schema. Hosted on RDS in A, on the box in B. |
| Dockerfile (KNOW-2263) | ✅ | optional | Plan B doesn't need Docker in production but the dev container Compose stack stays useful for local dev. |
| Worker + scheduler + cost meter (PR #5) | ✅ | ✅ | Replace `EcsRunTaskDispatcher` with a `SystemdTaskDispatcher`. The dispatcher abstraction was designed for this. |
| AWS CDK stacks (KNOW-2262) | ✅ | ❌ | Plan B doesn't use CDK. Keep the directory in case we ever revisit Plan A. |
| Migration scripts (KNOW-2271) | ✅ | ✅ | Same scripts, just point at local Postgres. |
| Pytest bootstrap (KNOW-2265) | ✅ | ✅ | Identical. |
| GitHub Actions CI/CD (KNOW-2264) | ✅ | scaled-down | Plan B's `deploy-prod.yml` becomes "ssh in, run deploy script" instead of a multi-stack `cdk deploy`. |
| Skilljar content source + drafts (KNOW-2272 / 2273) | ✅ | ✅ | Identical. |
| Google OIDC auth (KNOW-2259) | ✅ | ✅ | Identical. |

Net result: of the 9 backlog tickets, **8 are unchanged**. KNOW-2262 (the
AWS CDK ticket) becomes "filed under future" but is already mostly done
and easy to dust off if we ever need to scale.

---

## Cost comparison

Both totals are monthly USD, post-deploy steady state.

| Line item | Plan A (managed) | Plan B (single EC2) |
|---|---:|---:|
| Compute | App Runner: $20 (staging) + $40 (prod) = **$60** | t4g.small EC2: **$12.26** |
| Database | RDS db.t4g.micro × 2 envs + storage: **$34** | Postgres on the box: **$0** |
| NAT Gateway | $32 × 2 envs: **$64** | None (default VPC, public subnet): **$0** |
| Storage (S3 + EBS) | S3 + CloudFront: **$5** | EBS 30 GB gp3: **$2.40**; S3 (image bucket only): **$1** |
| Backups | RDS auto-backups included; EBS snaps **$1** | Daily EBS snapshot + S3 pg_dump: **$2** |
| Secrets Manager | 6 secrets × 2 envs × $0.40: **$4.80** | None: **$0** |
| KMS | 2 keys × $1: **$2** | None: **$0** |
| ECR | Stored images: **$0.50** | None: **$0** |
| CloudWatch logs/alarms | **$5** | Optional, default **$0** |
| Fargate per-run | Variable, ~**$5–30** | None: **$0** |
| Elastic IP | Included in App Runner | **$3.60** |
| Bandwidth | Tiny | Tiny: **~$1** |
| **Total monthly** | **~$120–200** | **~$22–25** |
| **Annualised** | **$1,440–2,400/yr** | **~$280/yr** |
| **5-year run rate** | $7,200–12,000 | ~$1,400 |

Cost delta: **~$100–175/month**, ≈ **$1,200–2,100/year**, ≈
**$5,800–10,500 over 5 years**.

> The largest single line item in Plan A is **NAT Gateways** — $64/mo
> across two environments, just to give private RDS subnets outbound
> internet for OS patching and OpenAI calls. Plan B has no NAT because the
> single EC2 sits in the default public subnet and routes via the IGW
> directly. NAT gateways are a managed-services tax that doesn't apply
> when you don't need private subnets.

---

## Ease-of-use comparison

### From your seat (operator: Sam)

| Task | Plan A | Plan B |
|------|--------|--------|
| First-time deploy | `cdk bootstrap` + `cdk deploy --all` (~25 min, 4 stacks). 6 secrets to pre-create in console. Wait for App Runner to spin up. | Launch EC2, run a setup script (~30 min). Add an A record. |
| Routine deploy | Push to `main` → GitHub Actions runs `cdk deploy` on staging → manual gate to prod. | `ssh` in, `bash bin/deploy-prod.sh`. Or use the same GHA pattern with a remote-run step. |
| Schema migration | Alembic auto-runs in CI/CD pipeline against RDS. | Alembic auto-runs in `ExecStartPre` of the systemd unit. |
| Reading logs | CloudWatch Logs Insights query syntax, multiple log groups. | `journalctl -u fme-train-web -f` in an SSH session. |
| Restart the app | Push a commit, wait for App Runner to redeploy. | `sudo systemctl restart fme-train-web` — instant. |
| Edit a secret | Console click into Secrets Manager, paste, App Runner needs new task to pick up. | `vim /etc/fme-train/env`, `systemctl restart fme-train-web`. |
| Restore from backup | RDS point-in-time restore. Wait ~10 min. Re-point app. | Restore EBS snapshot → launch new EC2 → re-attach EIP. ~15 min. |
| Add a new feature flag / env var | Update CDK code → `cdk deploy` (~10 min). | Edit `/etc/fme-train/env` → restart unit (~5 sec). |

### Knowledge each plan demands of you

| Plan A demands you understand | Plan B demands you understand |
|---|---|
| AWS CDK (Python flavour) | Linux systemd basics |
| App Runner deployment model | Nginx config (one server block) |
| Fargate task definitions | `certbot` once |
| RDS knobs (instance class, storage, backups) | `pg_dump` / `pg_restore` |
| Secrets Manager + IAM least-privilege | OS file permissions for `/etc/fme-train/env` |
| CloudWatch + log groups + alarms | `journalctl` |
| VPC subnets + security groups + NAT | One security group |
| ECR + Docker push workflow | Git pull |
| CloudFormation rollback troubleshooting | `systemctl status` |

For someone whose deployment experience is a static site, Plan B is a much
shorter ramp. The skills it teaches (Linux ops) are also the foundation
you'd need before AWS managed services would actually feel comfortable to
operate.

---

## When does Plan A become worth it?

Plan A's premium pays off when at least one of these is true:

1. **You have many tens of users or external users.** Then HA, autoscaling,
   and per-user-isolated workers matter.
2. **Downtime is measured in dollars.** App Runner self-heals; an EC2 box
   needs a human after a kernel panic.
3. **You're on a regulated workload.** SOC 2 / HIPAA / etc. preferes
   managed services with AWS-shared compliance posture.
4. **You don't have any Linux ops capacity at all.** Then App Runner
   abstracts away the OS entirely.

None of those apply to a 5-person internal training automation tool.

---

## Risks to be honest about (Plan B)

1. **Single point of failure.** If the EC2 dies, the team is offline until
   you restore from snapshot or launch a new instance. For 2–5 internal
   users, with no SLA, this is acceptable; for a customer-facing app, no.
2. **OS patching is on you.** `dnf-automatic` set to `apply_updates = yes`
   handles security patches automatically; plan a manual reboot quarterly
   for kernel updates.
3. **No staging environment.** Staging in Plan B is "test on the box during
   a quiet hour" or "spin up a second EC2 temporarily and tear it down". If
   you really want a staging environment full-time, add ~$15/mo for a
   second t4g.small. Even then, total is ~$40/mo — still a fraction of
   Plan A.
4. **Manual scaling.** If usage triples and the box runs hot, you bump to
   `t4g.medium` (still $25/mo) — a one-line change in the EC2 console. You
   don't get autoscaling. At 5 users, you don't need it either.
5. **You'll touch Linux.** It's not hard, but it's real. You will type
   things like `sudo journalctl -u fme-train-web -f`. The first time
   something goes wrong, you'll need to read a man page.

---

## Recommendation

**Plan B (single EC2) for v1.** Specifically:

- IT's pushback is correct for our scale. Plan A pays $1,500/year of
  managed-services premium for capabilities (HA, autoscaling, multi-AZ,
  per-run isolation) the team will not exercise.
- The application code we've already shipped — FastAPI, SQLAlchemy,
  Alembic, worker/scheduler — works in both plans with a different
  dispatcher class. **No code is wasted.**
- Sam learns Linux ops, which is a more transferable skill than CDK.
- If the tool ever grows beyond the team or gains an external surface, the
  CDK stacks are still on disk and pivoting is a few weeks of work.

**Practical follow-ups if you adopt this:**

1. Replace the deployment plan in
   `2026-05-05-multi-user-web-app-deployment.md` with a thin "Part C" that
   describes the EC2 setup: launch instance, run setup script, attach EIP,
   request DNS, run the deploy script. ~20 lines instead of 300.
2. Implement `SystemdTaskDispatcher` (small follow-up ticket — replaces
   `EcsRunTaskDispatcher` in `app/services/task_dispatcher.py`).
3. Write `bin/setup-ec2.sh` (idempotent provisioning script) and
   `bin/deploy-prod.sh`. Both small.
4. KNOW-2262 (AWS CDK) gets reclassified as "deferred — keep code on
   branch, do not deploy." Closes as `Won't Do for v1`.
5. Confirm IT will provide one EC2 instance with admin SSH access in their
   AWS account, plus the VPN-internal DNS record for `fme-train.base.safe.com`,
   the VPN CIDR for the security group, and the TLS approach (DNS-01 vs.
   IT-issued cert).

The conversation with IT is now: "we'll launch one t4g.small in your
account, put it behind `fme-train.base.safe.com` on the VPN, ssh-managed by
me. Cost ceiling: $30/month. Backups: nightly EBS + nightly pg_dump to S3."

That's a request IT can approve in a sentence.
