# Multi-user web app — remaining work + deployment plan

## Context

The architecture for the multi-user web app is settled in `docs/plans/2026-04-29-multi-user-web-app.md`. Four Phase 0 PRs are pushed and "Ready for QA" on Jira (KNOW-2258 FastAPI, KNOW-2260 SQLAlchemy/Alembic, KNOW-2262 AWS CDK, KNOW-2263 Dockerfile/Compose). They cover the *frame* — but **9 more Phase 0 tickets are still in the backlog**, all of which can be built and tested locally before we touch AWS.

You wanted to know: is there remaining web-app work I can do today? **Yes — a lot.** This plan breaks the remaining work into:

- **Part A — local work I can do now**, ordered by impact, all testable in your dev container against the Compose stack from PR #1.
- **Part B — what you need to do before we deploy**, in plain English, with links and what to expect.
- **Part C — the actual deployment**, step by step, with what you do vs what I do.
- **Part D — a glossary** so the AWS/cloud terms don't get in the way.

We are *not* starting the deployment today. The local work in Part A keeps the codebase moving forward while you do the prep work in Part B in parallel.

---

## Part A — Local work I can do today (no AWS needed)

All of these are open Jira tickets, all assigned to you, all in the backlog. Each can be built on a fresh branch off `feature/multi-user-web-app` and tested against the local Compose stack (`docker compose up`) which gives us a real Postgres, an S3 stand-in (MinIO), and the FastAPI app.

### Priority 1 — unblocks "can the app actually run a pipeline"
| Ticket | Title | Why it's first | Local test |
|---|---|---|---|
| **KNOW-2270** | Worker mode and dual-mode container entrypoint | The Dockerfile (PR #1) routes `ENTRYPOINT_MODE=worker` to `python -m worker`, but **`worker.py` does not exist**. Without it, no pipeline run can ever launch in production. | `docker compose run --rm worker-runner` (already wired in PR #1) executes the new `worker.py` end-to-end with a fixture run row, asserts artifacts land in MinIO. |
| **KNOW-2269** | Run scheduler + RunCostMeter (concurrency 2, $50 ceiling) | The web tier needs to dispatch worker tasks, enforce the 2-run cap, and abort on cost overruns. Pure Python — testable with a fake "ECS run-task" stub locally. | Pytest with an in-process scheduler driving fake tasks; assert queue ordering, cost-ceiling abort, partial-artifact retention. |
| **KNOW-2261** | SSE live log streaming | Worker writes rows to `run_logs`; FastAPI streams them over Server-Sent Events to the browser. Pure Postgres + asyncio. | Pytest + `httpx.AsyncClient` reads the SSE endpoint while a fake worker appends rows; assert rows arrive within ~200ms. |

### Priority 2 — unblocks "can the app see Skilljar content"
| Ticket | Title | Why | Local test |
|---|---|---|---|
| **KNOW-2272** | Skilljar canonical content source + taxonomy sync | Replaces the old "scan local folders" approach with a Skilljar-API-backed `LessonContentSource`. Without it, the pipeline has no input. The actual Skilljar API can be hit from your dev container today using your existing `SKILLJAR_API_KEY`. | Pytest with mocked Skilljar responses (`respx`); plus one optional live integration test you can run when you trust your key. |
| **KNOW-2273** | Lesson drafts S3 store + Save Draft API | New `/api/drafts` endpoint writes drafts to S3 (MinIO locally). Replaces today's `_handle_save_lesson` writing to local folders. | Pytest with the MinIO fixture from PR #1; round-trip a draft and confirm the `lesson_drafts` row + S3 object both exist. |

### Priority 3 — needed before any real deploy, but doesn't block local development
| Ticket | Title | Why | Local test |
|---|---|---|---|
| **KNOW-2271** | Migration scripts: legacy JSON state → Postgres + S3 | Five small one-shot scripts: `runs.json`, `artifacts/*`, `update-job.json`, `inputs/jira_api_cache.json`, local `2026.1/` drafts. Run each twice on a copy of prod data and confirm idempotency. | Pytest using a fixture copy of your real `artifacts/` and `inputs/` directories. |
| **KNOW-2265** | Pytest suite bootstrap (covering current pipeline) | Today's tests are scattered. This consolidates them under `tests/{unit,integration,smoke}` with shared fixtures (Postgres, MinIO, fake Skilljar). Phase 0 cutover gate calls for it. | Running the suite *is* the test. |
| **KNOW-2264** | GitHub Actions CI/CD workflows | Three YAMLs: `pr.yml` (lint+test+build on PRs), `main.yml` (auto-deploy to staging when KNOW-2257 is approved and we have an AWS account), `deploy-prod.yml` (manual gate). The YAMLs themselves are written and committed today; the *deploy* steps stay no-op until your AWS account exists. | Push a no-op commit; confirm `pr.yml` runs and gates merge. |
| **KNOW-2259** | Google OIDC sign-in restricted to `@safe.com` | The auth code (FastAPI routes, `authlib`, signed cookie, `hd` claim check) is fully buildable with a temporary OAuth client in a sandbox GCP project. Once IT creates the real client (Part B), we just swap the client ID. | Pytest with a stubbed Google ID token verifier; manual end-to-end test with a Google account in a throwaway browser profile. |

**Today's scope (confirmed):** **KNOW-2270 + KNOW-2269** as a single bundle (worker + scheduler). They need to be designed together. ~half a day. Other tickets get sequenced into subsequent days.

I will check with you before merging into `feature/multi-user-web-app` — this work goes onto a fresh branch + new PR.

---

## Part B — What you need to gather (plain English checklist)

IT has approved the plan and you have an AWS login. The remaining prep is a short list of facts I need from you and a permissions check. Each item below tells you exactly where to look and what to copy back. **You can do this in parallel with my Part A work — don't wait for me.**

If any item turns out to need elevated permissions that IT didn't grant, that's fine — flag it, I'll work around it locally until IT extends your access.

### B1. AWS account ID *(30 seconds)*
- Sign into the AWS console at <https://console.aws.amazon.com>.
- Top-right corner: click your name. The dropdown shows a 12-digit number labelled **Account ID**.
- **Copy that number to me.** That's the only thing I need to wire CDK to the right account.

> **Is the account ID secret?** It's *mildly* sensitive — not at the level of an access key, but Safe probably doesn't want it on a public webpage either. It's safe to paste in this chat (the conversation is private to you and Anthropic) and it's safe to keep in your `.env` (which is gitignored). What you should *not* do is commit it to a public file or paste it in a public Slack channel. We'll keep it out of the committed repo via `.env` references.

### B2. AWS region — *decided: `us-east-1` (N. Virginia)*
Both your console default and the existing image-upload bucket sit in **us-east-1**. We'll deploy there too. The `safeskilljar` public-training bucket is technically in us-west-2, but our new app reads training content via the Skilljar API (not directly from that bucket), so cross-region traffic isn't a hot path. Staying in one region keeps things simple and matches what you already operate.

I'll pass `--region us-east-1` to CDK and the AWS CLI.

### B3. CLI authentication — likely needs IT *(blocking for deploy, but check existing keys first)*

**Your current state, from the permission probes you ran:**
- IAM is the auth model in this account (the SSO page just shows an "Enable" marketing call-to-action), AND
- You don't have permission to view or modify IAM yourself (`iam:GetAccountSummary` was denied).

So you can't create access keys via the console. **However**, you mentioned existing access keys already in use for the image-upload feature (the `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` in your `.env`). Two questions about those:

**Q1: Can we reuse the existing keys for deployment?** Almost certainly **no**, for three reasons:
1. **Permissions** — keys provisioned for "upload PNG to one bucket" almost never have `cloudformation:*`, `iam:*`, `rds:*`, etc. CDK will fail on the first call.
2. **Blast radius** — if these keys are compromised, you don't want both image upload and infra deployment affected.
3. **Audit clarity** — CloudTrail will commingle "image uploaded by the app" with "deploy run by Sam". Future you will hate untangling that.

**Q2: Should we even *try* the existing keys?** Yes — quick sanity check before you ping IT. The existing access key + secret are already in your `.env` (the `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` lines). I can run, in this dev container:

```
aws sts get-caller-identity                # tells us which IAM user owns the keys
aws iam get-user                           # reads that user's metadata, if allowed
aws iam list-attached-user-policies --user-name <result-of-above>
                                           # lists the policies on that user
```

That gives us a precise read on what permissions those keys have. If the user shows up as something like `s3-image-uploader` with only narrow S3 permissions, we're confirmed: separate deploy keys needed (the email below). If by some surprise it has broader permissions, we can talk about whether to reuse.

**Recommendation:** ask IT for separate credentials. Send them this email:

> **Subject:** AWS access for FME Training Automation deploy (KNOW-2257)
>
> Hi IT — KNOW-2257 is approved and I'm starting on the AWS deploy. I have console access to the account but lack the IAM permissions to create access keys for myself. We have an existing service-account key used for S3 image uploads in the legacy app, but it's scoped narrowly and shouldn't be reused for deployment (different blast radius, different audit trail).
>
> Could you do **one** of the following:
>
> **(a) Quick path** — create an IAM user named `fme-train-deployer-sam` with the AWS-managed policy `AdministratorAccess` attached, generate access keys, and send me the **Access Key ID + Secret Access Key**. We can tighten the policy after the first successful deploy.
>
> **(b) Longer-term path** — enable AWS IAM Identity Center for the account and add me as an admin user. Send me the AWS access portal URL (ends in `.awsapps.com/start`).
>
> Either works. (a) is faster for unblocking me; (b) is the right answer long-term and we'll want to migrate within a quarter regardless. If (b) is heavy lift right now, (a) is fine as a stepping stone.
>
> A narrower alternative if `AdministratorAccess` feels too broad for option (a): the user needs `cloudformation:*`, `iam:*` (with `iam:PassRole` constrained), `s3:*`, `rds:*`, `ec2:*` (for VPC), `apprunner:*`, `ecs:*`, `ecr:*`, `secretsmanager:*`, `kms:*`, `logs:*`, `sns:*`, `cloudwatch:*`, `budgets:*`. Functionally admin minus billing — not really an improvement, hence the recommendation for (a) up front.

**Until IT gets back to you,** my Part A work doesn't need this — I can build worker.py + scheduler against the Compose stack with no AWS at all. The blocker only kicks in at Part C Step 1.

Once you have new access keys (option a) or portal URL (option b), paste them in chat and I'll wire them into the dev container.

### B4. Permissions sanity check *(2 minutes, after IT delivers B3)*
Once IT delivers your access, I'll run five tiny read-only commands to confirm the grant is wide enough:

```
aws sts get-caller-identity         # always works if creds are set
aws s3 ls                           # needs S3 read
aws cloudformation list-stacks      # needs CFN — required for CDK
aws iam list-roles --max-items 1    # needs IAM read — required for CDK
aws secretsmanager list-secrets     # needs Secrets Manager — required for the secret pre-create step
```

If you asked for option (a) `AdministratorAccess`, all five will succeed and we move on. If IT gave you a narrower policy and one fails, we have a precise pointer for a follow-up request.

### B5. Existing AWS resources check *(2 minutes, also once B3 is done)*
We need to make sure nothing already exists in the account that would collide with what CDK creates. I'll run:

```
aws ec2 describe-vpcs --query 'Vpcs[*].[VpcId,CidrBlock,Tags]'
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE
```

If the account is empty or only has a default VPC, we're fine. If there's already infrastructure, we'll either reuse the VPC (cheaper) or pick a different CIDR for ours (safer) — I'll decide once I see the output.

### B6. Google OAuth client *(10 minutes, once you have GCP access)*
The Google side of sign-in needs an OAuth client. IT may have already given you access to a Safe Google Cloud project; if not, this is a separate small ask of IT.

Once you can reach <https://console.cloud.google.com>:

1. **Confirm the project.** Top of the page, click the project dropdown. There should be one related to internal tooling, or IT should have created `safe-fme-training-automation` for us. Pick that project.
2. **APIs & Services → OAuth consent screen.** If it's not yet configured, click **Configure**. **User type: Internal** (Google enforces `@safe.com` for free; we don't need to). App name: `FME Training Automation`. Save.
3. **APIs & Services → Credentials → Create Credentials → OAuth client ID.**
   - Application type: **Web application**.
   - Name: `fme-train-staging`.
   - Authorized redirect URIs: add `http://localhost:8000/auth/callback` for now (we'll add the App Runner URL after Step 3 of Part C).
   - Click Create.
4. **Hand me the Client ID and Client Secret.** Both are shown in a popup; client secret only shown there.

Repeat for `fme-train-production` later when we promote.

### B7. Skilljar service-account API key *(5 minutes)*
You already have a personal Skilljar API key in your `.env`. For deployment we want service-account keys so audit trails don't show "Sam Walker did this" for every action.

- Skilljar admin → **Settings → API Access** (or wherever your domain has it).
- Create a new key called `fme-training-automation-staging`. **Copy the key immediately.**
- Repeat for `fme-training-automation-production`.
- **Hand both to me.** I'll put them in AWS Secrets Manager in Step 2 of Part C.

### B8. Domain name *(decide later, not blocking)*
- **Easy mode (default):** use the AWS-generated `xxxxx.us-west-2.awsapprunner.com` URL. Free, HTTPS, works forever. Recommend for v1.
- **Pretty mode:** `fme-train.safe.com` or similar. Needs Safe IT to add a DNS record and AWS to issue a free certificate. Defer to v2.

---

**Summary checklist of things to send me (or already have):**

```
[  ] AWS account ID                            (B1)
[x] AWS region — us-east-1                     (B2 — decided)
[x] Existing AWS keys in .env                  (B3 — I'll probe these first)
[  ] Either: NEW IAM access key + secret       (B3 option A) — likely needs IT
[  ]    or:  AWS access portal URL             (B3 option B) — likely needs IT
[x] Existing Skilljar key in .env              (B7 — usable for staging dev work)
[  ] Google OAuth: client ID + secret          (B6) — for staging
[  ] Skilljar API key — production             (B7) — can wait
[  ] Google OAuth client for production        (B6) — can wait
```

Once I have the staging-tier values from this list, we're ready for Part C.

---

## Part C — Deployment plan, step by step

This part assumes B1–B7 are complete. Steps marked **[you]** are clicks/commands you run; **[me]** are things I do via PR or in your terminal with you watching.

### Step 1 — One-time AWS account bootstrap **[me, with you watching]**
- Verify `aws sts get-caller-identity` shows the right account.
- Run `cdk bootstrap aws://ACCOUNT_ID/us-west-2`. **What this does in plain English:** CDK uploads its deployment toolkit (an S3 bucket and an IAM role) so it can ship code to your account on every later deploy. You only do this once per AWS account.
- Cost: about $0.05/month for the bucket. Negligible.

### Step 2 — Pre-create the Secrets Manager secret values **[you, with me coaching]**
The CDK stacks reference secrets *by name* (so the deploy doesn't ship plaintext into CloudFormation). You create the secrets manually first, paste the values in, then deploy.

In the AWS console → **Secrets Manager → Store a new secret → Other type of secret → Plaintext**, create six secrets named exactly:
- `fme-train-staging/openai/api-key` — paste your staging OpenAI key
- `fme-train-staging/jira/api-token` — paste your Jira API token
- `fme-train-staging/skilljar/api-key` — paste the staging Skilljar key from B4
- `fme-train-staging/google/oauth-client-secret` — paste the secret from B3
- `fme-train-staging/session/signing-key` — paste 32 random bytes (run `openssl rand -hex 32` in your terminal)
- `fme-train-staging/jira/filter-id` — paste your Jira filter ID (the number in the filter URL)

This is tedious clicking but only happens once per environment. Each secret costs $0.40/month. Repeat the list with `fme-train-production/...` once we promote.

There is also a separate `rds-master-credentials` secret created automatically by RDS when the database starts — you don't pre-create that one.

### Step 3 — First staging deploy **[me]**
With B1–B4 done and Step 1–2 complete, this is `cdk deploy -c env=staging --all` from the `infra/` directory. AWS will provision (in order, ~25 minutes total):
1. VPC + private/isolated subnets + NAT gateway *(~5 min)*
2. RDS Postgres + KMS key + S3 buckets + CloudFront distribution *(~12 min)*
3. ECR repository (empty) + IAM roles + Fargate cluster *(~3 min)*
4. CloudWatch alarms + Budget *(~2 min)*

Then I push the first container image to the new ECR repo and re-run `cdk deploy compute` so App Runner can find it. App Runner takes ~5 more minutes to spin up.

After Step 3, you have a live `https://xxxxx.us-west-2.awsapprunner.com` URL serving the FastAPI app. Sign-in won't work yet because the Google OAuth client doesn't have that URL in its redirect list (B3 step 3).

### Step 4 — Wire up the OAuth callback URL **[you, 2 minutes]**
Now that you have the App Runner URL from Step 3, go back to the Google Cloud OAuth client (B6) and add `https://xxxxx.us-west-2.awsapprunner.com/auth/callback` to its "Authorized redirect URIs". Save.

### Step 5 — Run the database migrations **[me]**
`alembic upgrade head` against the staging RDS instance. AWS Secrets Manager hands the connection string to my terminal. **Plain English:** the database starts empty; this command creates the 14 tables.

### Step 6 — One-time data migration **[me]**
Run the migration scripts from KNOW-2271:
- Upload the existing `artifacts/*` JSON files to S3.
- Seed the `runs`, `run_steps`, `jobs` tables from `runs.json` and `update-job.json`.
- Bootstrap the Skilljar inventory by calling `POST /api/skilljar-inventory/sync` once.
- Upload any existing local `2026.1/` drafts to S3 + `lesson_drafts`.

### Step 7 — Activate cost-allocation tags **[you, 1 minute]**
This is the runbook step from KNOW-2262 PR #4. AWS Billing console → **Cost Allocation Tags** → activate `Project` and `Environment`. Without this, the budget alarms see $0 forever.

### Step 8 — Subscribe to alarms **[you, 1 minute]**
AWS console → **SNS → fme-train-staging-alarms → Create subscription → Email**. Use a team distribution list, not a personal email. Confirm via the email AWS sends.

### Step 9 — Staging dry-run week **[you + me]**
For about a week, run real workflows on staging:
- Sign in with three or four `@safe.com` Google accounts. Confirm row appears in `users`.
- Kick off small runs (1–2 lessons each). Watch SSE logs in the browser.
- Try the Save Draft → S3 path. Confirm a `lesson_drafts` row + S3 object appear.
- Try a release flow against a *staging Skilljar lesson* (or a sandbox course in Skilljar's admin if you can create one). Confirm the conflict-guard locks behave as the plan describes.
- **Do not** point the team at staging URL yet — this week is debugging.

### Step 10 — Production deploy **[me, after Step 9 is clean]**
- Repeat Step 2 with `fme-train-production/...` secrets.
- `cdk deploy -c env=production --all`.
- Repeat Step 5 (alembic upgrade) against production RDS.
- Repeat Step 6 (data migration).
- Repeat Step 7 (cost tags) and Step 8 (alarm subscription).
- Smoke-test for a day with just the two of us.

### Step 11 — Cutover **[you]**
- Email the team the production URL. Tell them to bookmark it.
- Retire the local `launch.sh` / `serve.py` path. Move the script to an `archive/` directory in the repo (don't delete — you may want to read the old code later).

---

## Verification

| Stage | How we know it worked |
|---|---|
| Part A — local code | Pytest suite passes (`pytest tests/`). Compose stack starts cleanly (`docker compose up`). One-lesson run completes end-to-end with logs visible in the browser. |
| Step 1 (bootstrap) | `cdk ls -c env=staging` lists all four stacks. |
| Step 3 (staging deploy) | `curl https://staging-url/health` returns `{"status":"ok"}`. CloudWatch shows zero errors in App Runner logs. |
| Step 5 (migrations) | `psql … -c "\dt"` against staging RDS lists all 14 tables. |
| Step 6 (data migration) | `select count(*) from runs;` matches the row count in your local `runs.json`. |
| Step 9 (dry-run week) | Three real `@safe.com` users have signed in, a real run has completed, a real Skilljar release has happened against a non-customer-facing lesson, no CloudWatch alarms fired, AWS Budget shows under $20 spent for the week. |
| Step 11 (cutover) | Team is on the URL. `serve.py` archived. KNOW-2257 closed. |

---

## Critical files / functions we'll be modifying

- `app/main.py` — wire up DB engine, scheduler, auth middleware (currently has TODOs for these)
- `app/routes/` — add `runs.py`, `auth.py`, `drafts.py`, `skilljar.py`, `sse.py` (only `health.py` and `index.py` exist today)
- `app/services/` — new directory for `run_scheduler.py`, `run_cost_meter.py`, `run_logger.py`, `lesson_content_source.py`
- `worker.py` — new file at repo root, imports the existing `pipeline.*` modules
- `migrations/` — new directory with five one-shot scripts (KNOW-2271)
- `.github/workflows/` — three new YAML files (KNOW-2264)
- `tests/` — restructure under `unit/`, `integration/`, `smoke/` (KNOW-2265)

Existing reusable code:
- `pipeline/jira_api.py::fetch_descriptions` — already ephemeral; reused as-is by the worker
- `pipeline/skilljar_release.py::_upload_and_rewrite_images` — reused for draft promotion
- `pipeline/utils.py::changelog_path`, `recommendations_path`, `edit_plans_path` — adapt to take `run_id` + S3 key prefix

---

## Part D — Glossary (only AWS terms used in this plan)

- **AWS Account** — Like a Google account but for AWS. Has its own billing.
- **CDK** — "Cloud Development Kit". Python code that describes AWS resources. `cdk deploy` makes AWS create them. `cdk destroy` makes AWS delete them.
- **CloudFormation** — AWS's underlying "describe stuff in JSON" service. CDK compiles down to it.
- **CloudFront** — AWS's CDN. We use it for one public bucket of lesson images so Skilljar can embed them.
- **CloudWatch** — AWS's logging + monitoring + alarms.
- **ECR** — AWS's Docker image registry, like Docker Hub but private to your account.
- **Fargate** — Run a container without managing servers. We use it for one-off pipeline runs.
- **IAM** — "Identity and Access Management". AWS permissions.
- **KMS** — Encryption keys, managed by AWS. Used for at-rest encryption.
- **NAT Gateway** — Gives private resources outbound internet access. Costs ~$32/mo per environment.
- **OIDC** — Standard for "sign in with Google/anywhere". We use the Google flavor.
- **RDS** — Managed Postgres. AWS handles backups, patches, failover.
- **App Runner** — AWS's "give me a container, get a public HTTPS URL" service. Hosts our FastAPI app.
- **S3** — File storage by URL. Buckets hold files.
- **Secrets Manager** — AWS's password vault.
- **VPC** — A private network inside your AWS account.

---

## What happens next

In this order, today:

1. **I** merge the four open PRs (KNOW-2258, 2260, 2262, 2263) into `feature/multi-user-web-app`. They're all in "Ready for QA" on Jira and re-reviewed in our last session — clean to merge. I'll do GitHub-side merges (squash or merge-commit, whichever you prefer; default to merge-commit so the per-ticket commits stay legible).
2. **I** save this plan to `docs/plans/2026-05-05-multi-user-web-app-deployment.md` and update `AGENTS.md` with the convention rule.
3. **I** cut a new branch off the post-merge `feature/multi-user-web-app` for the worker + scheduler work (`feature/multi-user-web-app-KNOW-2269` or similar).
4. **You** in parallel: probe the existing access keys (Q2 in B3), then send the IT email in B3, then gather B1, B6, B7 as time allows.
5. **I** start KNOW-2270 + KNOW-2269 on the new branch and open a PR when it's tested locally.
6. Loop: once IT delivers B3 and that PR is reviewed and merged, I pick up the next priority ticket from Part A. We continue until either Part A is done or you have all of Part B together — whichever comes first kicks off Part C.

## Plan persistence (post-approval housekeeping)

Step 2 above is the persistence step. Specifically I will:

1. Copy this file to `docs/plans/2026-05-05-multi-user-web-app-deployment.md` (so it lives alongside the architecture doc).
2. Update `AGENTS.md` with a rule that any approved plan should be saved to `docs/plans/` with the date prefix, so future sessions inherit the convention.
3. Commit both on the new feature branch alongside the worker + scheduler work (one logical bundle: "the plan we agreed to + the first ticket we executed").
