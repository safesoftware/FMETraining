# `infra/` — AWS CDK stacks for FME Training Automation

This directory contains the AWS CDK (Python) code that provisions the
multi-user web app described in
[`docs/plans/2026-04-29-multi-user-web-app.md`](../docs/plans/2026-04-29-multi-user-web-app.md).

It implements **section 6 — Deployment, CI/CD, IaC** of that plan.

> ### Status
>
> **No `cdk deploy` has been run yet.** This stack code is authored ahead
> of IT/security sign-off so deployment is one command away once
> KNOW-2257 (the IT review) is approved. Until then, `cdk synth` and
> `cdk diff` (which only generate CloudFormation locally) are safe to
> run; `cdk deploy` is not.

---

## What's in here

```
infra/
├── app.py                   # CDK app entrypoint; instantiates one env per synth
├── cdk.json                 # CDK config (default env = staging)
├── requirements.txt         # aws-cdk-lib + constructs (no jsii pre-release)
├── README.md                # this file
├── config/
│   ├── __init__.py
│   ├── staging.py           # smaller RDS, looser alarms, $75/mo budget
│   └── production.py        # larger RDS, 7-day backups, $150/mo budget
├── stacks/
│   ├── __init__.py
│   ├── network.py           # VPC, subnets, security groups, NAT gateway
│   ├── data.py              # RDS Postgres, S3 buckets, KMS, Secrets refs, CloudFront
│   ├── compute.py           # App Runner, ECR, Fargate cluster + worker task def, IAM
│   └── observability.py     # CloudWatch alarms, dashboard, AWS Budget
└── tests/
    └── test_cdk.py          # synth + IAM least-privilege assertions
```

Each stack maps to a layer of the plan's architecture diagram. They are
synthesized into separate CloudFormation stacks (so each can be deployed,
diffed, and rolled back independently), wired together at the CDK level
via cross-stack handles rather than `CfnOutput` lookups.

---

## Prerequisites (one-time, on your laptop)

1. **Python 3.11+** (matches the rest of this repo).
2. **AWS CLI v2**, with a profile that has admin perms in the target
   AWS account. We'll call this profile `fme-train` below.
3. **Node.js 20+** — required by the AWS CDK toolkit.
4. **CDK toolkit** — install once globally:

   ```bash
   npm install -g aws-cdk@2
   ```

5. **Python deps** — installed inside `infra/`:

   ```bash
   cd infra
   python -m venv .venv
   source .venv/bin/activate     # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

---

## Local "does it synth" loop

```bash
cd infra
source .venv/bin/activate
cdk synth -c env=staging      # full CFN to stdout
cdk synth -c env=production   # ditto, prod sizing
pytest tests/                 # CDK assertions (run quickly)
```

`cdk synth` does **not** call AWS; it's a pure local code-gen step. You
can run it without any AWS credentials configured.

`cdk diff -c env=<env>` *does* call AWS (`describe-stacks`) but only
performs read operations. Against an account where no stack has been
deployed yet it prints a "this will create N resources" preview.

---

## First deploy runbook (for IT, after KNOW-2257 sign-off)

Do these steps in order. Stop and ask if anything looks wrong.

### 1. Pick / create the AWS account

Per plan section D, the recommended target is a sub-account of the Safe
AWS organization in **us-west-2** (matches the existing `safeskilljar`
S3 bucket).

Note the account ID (12-digit number) and configure an `AWS_PROFILE` for
it locally.

### 2. Bootstrap the CDK environment

CDK needs a one-time bootstrap stack per (account, region) pair. This
creates the staging/CFN-deploy buckets and the IAM roles CDK uses
internally.

```bash
export AWS_PROFILE=fme-train
cd infra
cdk bootstrap aws://<ACCOUNT_ID>/us-west-2
```

This writes a stack named `CDKToolkit`. Run once per account.

### 3. Pre-create the Secrets Manager secrets

CDK references each secret by ARN — it does **not** create them or write
their values. Create the following secrets manually before the first
`cdk deploy`:

| Secret name (in Secrets Manager)         | Notes                                            |
|------------------------------------------|--------------------------------------------------|
| `fme-train/<env>/openai-api-key`         | OpenAI API key for the corporate Safe org        |
| `fme-train/<env>/jira-api-token`         | Jira API token for the service-account           |
| `fme-train/<env>/skilljar-api-key`       | Skilljar REST API key                            |
| `fme-train/<env>/google-oauth-client-secret` | Google OIDC client secret                    |
| `fme-train/<env>/session-signing-key`    | 64+ random bytes, base64 (cookie HMAC key)       |

`rds-master-credentials` is created automatically by RDS during `cdk
deploy` — do not create it manually.

Then write the secret ARN to SSM Parameter Store so CDK can find it:

```bash
aws ssm put-parameter \
  --name "/fme-train/<env>/secrets/openai-api-key/arn" \
  --type String \
  --value "<full secret ARN>"
# repeat for the four other secrets
```

This indirection lets you rotate / recreate the secret without re-deploying CDK.

### 4. Deploy the stacks (staging first)

```bash
cd infra
cdk deploy -c env=staging --all --require-approval=any-change
```

The four stacks deploy in order: `Network` → `Data` → `Compute` →
`Observability`. Roughly 25 minutes for the first deploy (RDS + App
Runner are slow).

### 5. Push the first container image

App Runner will be in `CREATE_FAILED` until ECR has at least one image
tagged `:latest`. Build and push from the repo root:

```bash
# from repo root
docker build -t fme-train:latest .
aws ecr get-login-password --region us-west-2 | \
  docker login --username AWS --password-stdin \
  <ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com
docker tag fme-train:latest \
  <ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/fme-train-staging:latest
docker push \
  <ACCOUNT_ID>.dkr.ecr.us-west-2.amazonaws.com/fme-train-staging:latest
```

(GitHub Actions takes over this step once `main.yml` is wired up.)

Then re-run `cdk deploy` to pick up the now-resolvable image:

```bash
cdk deploy -c env=staging FmeTrainStgCompute
```

### 6. Subscribe to alarms

The observability stack creates an SNS topic per env
(`fme-train-<env>-alarms`). Subscribe the team's email distribution
list to it manually once:

```bash
aws sns subscribe \
  --topic-arn arn:aws:sns:us-west-2:<ACCOUNT_ID>:fme-train-staging-alarms \
  --protocol email \
  --notification-endpoint training-alerts@safe.com
```

### 7. Repeat for production

```bash
cdk deploy -c env=production --all --require-approval=any-change
```

After production is up, point GitHub Actions' `deploy-prod.yml` workflow
at the prod account.

### 8. Activate cost-allocation tags in the AWS Billing console

The observability stack's AWS Budget filters spend by `Project=fme-training-automation`
and `Environment=<env>`. CDK applies these tags to every resource, but
**AWS will not include them in cost reports until they are activated as
user-defined cost allocation tags** in the Billing & Cost Management
console. Until you do this, the $75 staging / $150 production budget
alarms see $0.00 spend regardless of real usage and will never fire.

This step is a one-time manual click; CDK cannot do it.

1. Open <https://console.aws.amazon.com/billing/home#/tags>.
2. In the **User-defined cost allocation tags** list, find `Project` and
   `Environment`. Tick both and click **Activate**.
3. Wait up to 24 hours for cost data to start flowing through the new
   filters before trusting the alarm thresholds.

### 9. CI guard against committing live AWS credentials into the image

The repo's `.env` (gitignored) currently holds personal AWS access keys
left over from the legacy pipeline. Once we deploy, the workers must use
the IAM task role automatically — but if `.env` ever gets baked into a
container image (e.g. a `COPY .` that bypasses `.dockerignore`), those
hardcoded keys would silently override the role credentials at runtime.

Belt-and-suspenders guard: add this step to the GitHub Actions image
build job (`build-image.yml`) so any image carrying static credentials
fails CI:

```yaml
- name: Reject images that bake AWS keys
  run: |
    if docker run --rm --entrypoint /bin/sh "${IMAGE_TAG}" \
         -c 'cat /app/.env 2>/dev/null; printenv' \
       | grep -qE '^(AWS_ACCESS_KEY_ID|AWS_SECRET_ACCESS_KEY)='; then
      echo "::error::Image contains AWS credentials. Check .dockerignore."
      exit 1
    fi
```

The Dockerfile in this repo (`Dockerfile`, owned by KNOW-2263) already
excludes `.env` via `.dockerignore`; this guard catches future
regressions.

---

## Stack reference

### `NetworkStack` (`stacks/network.py`)

* **VPC** with two AZs.
* **Public subnets** (one per AZ) host the NAT gateway.
* **Private-with-egress subnets** host the App Runner VPC connector
  ENIs and the Fargate task ENIs.
* **Isolated subnets** host the RDS instance (no NAT egress — defence
  in depth against outbound exfiltration).
* **Security groups**:
  * `app_runner_sg` — App Runner connector. Allows all outbound.
  * `fargate_sg` — Fargate run-task ENIs. Allows all outbound.
  * `rds_sg` — RDS. Ingress on 5432 from `app_runner_sg` and
    `fargate_sg` only. **No egress.**

### `DataStack` (`stacks/data.py`)

* **KMS CMK** with annual rotation.
* **RDS Postgres** (db.t4g.micro / db.t4g.small), encrypted, in
  isolated subnets (no internet egress), master credentials in Secrets
  Manager (auto-created with `Credentials.from_generated_secret`).
* **S3 buckets** — all private, KMS-encrypted, TLS-only:
  * `artifacts/`         — run artifacts.
  * `drafts/`            — versioned, replaces local
    `2026.1/.../index.html` writes.
  * `skilljar-content/`  — canonical content cache.
  * `cache/`             — shared OpenAI / Jira cache. Glacier transition
    after 365 days.
* **`images` bucket** + **CloudFront distribution** for Skilljar
  embedding (private bucket, OAI for CloudFront read).
* **Secrets Manager refs** — imported by ARN from SSM. CDK never
  creates these or writes their values.

### `ComputeStack` (`stacks/compute.py`)

* **ECR repo** with image scan on push, immutable tags, lifecycle rules
  to expire old images.
* **Fargate cluster** with container insights enabled.
* **App Runner service** (CfnService L1, since the L2 is jsii pre-
  release):
  * VPC connector to private subnets.
  * Reads from ECR.
  * Inject secrets as env vars at container start.
  * Ingress public via App Runner's managed HTTPS endpoint.
* **IAM roles**:
  * `task_execution_role` — pull image, ship logs. **Scoped to this
    repo + this log group.** The one `Resource: "*"` is on
    `ecr:GetAuthorizationToken` (AWS API limit).
  * `worker_role` — Fargate worker app perms. Scoped to its run's S3
    prefixes via `${aws:PrincipalTag/run_id}`. Reads the named
    secrets only. KMS Decrypt only on the data CMK.
  * `app_runner_access_role` — ECR pull. Scoped to the repo.
  * `app_runner_instance_role` — runtime app perms. Scoped reads/writes
    on the four buckets, scoped `ecs:RunTask` on this task family in
    this cluster, `iam:PassRole` constrained to `ecs-tasks.amazonaws.
    com`, scoped secret reads.
* **SSM parameter** `/fme-train/<env>/max-run-usd` — read by worker
  for the per-run cost ceiling.

### `ObservabilityStack` (`stacks/observability.py`)

* **SNS topic** per env (`fme-train-<env>-alarms`). Subscribe an email
  endpoint manually post-deploy.
* **Metric filters** on the worker log group:
  * `RUN_COST_CEILING_EXCEEDED` → `FmeTrain.CostCeilingExceeded` metric.
  * `WORKER_FATAL` → `FmeTrain.WorkerFatal` metric.
* **Alarms**:
  * Cost ceiling exceeded.
  * Worker fatal-error rate.
  * RDS CPU sustained.
  * RDS free storage.
  * App Runner 5xx rate.
* **AWS Budget** — env-specific monthly cost cap with 80% actual + 100%
  forecasted SNS notifications.
* **Dashboard** — App Runner request rate / 5xx, RDS CPU + free
  storage, worker cost-ceiling + fatal counts.

---

## IAM least-privilege notes for IT review

The CDK code follows three rules, validated by `tests/test_cdk.py`:

1. **No `Resource: "*"` for write actions.** The few `*` resources in
   the synthesized output are read-only metadata actions where AWS does
   not allow resource-level scoping (`ecr:GetAuthorizationToken`,
   `ecs:ListTasks`, `ecs:DescribeTaskDefinition`).
2. **Scoped bucket prefixes for the worker.** The Fargate task role
   gets per-run S3 access via `${aws:PrincipalTag/run_id}` substitution.
   At RunTask dispatch time the App Runner control plane sets the tag
   on the task; the worker can only touch its own prefix. The same
   pattern scopes draft writes to `${aws:PrincipalTag/to_version}`.
3. **PassRole is constrained.** App Runner can only pass the worker /
   execution roles to `ecs-tasks.amazonaws.com`, never to other
   services.

RDS row-level isolation (the worker can only update rows where
`run_id = $RUN_ID`) is enforced **in SQL inside the worker**, not by
IAM. Postgres without IAM auth doesn't expose a way to do row-level
authorization at the IAM layer; we considered IAM database
authentication and rejected it as overkill for a 2-5 user team. This
trade-off is documented here so IT review can flag it if undesirable.

---

## Useful commands

```bash
# What stacks exist for the current env?
cdk ls -c env=staging

# Show the CFN that *would* be deployed.
cdk synth -c env=staging FmeTrainStgCompute

# Diff against the deployed stack (calls AWS, read-only).
cdk diff -c env=staging FmeTrainStgCompute

# Deploy a single stack only.
cdk deploy -c env=staging FmeTrainStgNetwork

# Tear it all down (DESTRUCTIVE, uses RemovalPolicy on each resource).
# Production resources have RETAIN policies and will not actually delete.
cdk destroy -c env=staging --all
```

### Cleanup after `cdk destroy` on production

Production S3 buckets use `RemovalPolicy.RETAIN`, and the RDS instance
uses `RemovalPolicy.SNAPSHOT`. After a `cdk destroy` on production these
resources stay behind, no longer managed by any stack. They will keep
costing money until manually disposed of. Checklist:

1. List orphaned buckets:
   ```bash
   aws s3api list-buckets \
     --query 'Buckets[?starts_with(Name,`fme-train-prod-`)].Name' \
     --output text
   ```
2. Confirm contents are no longer needed (or copy to a long-term archive
   bucket), then `aws s3 rb --force s3://<bucket-name>` for each.
3. Find the final RDS snapshot:
   ```bash
   aws rds describe-db-snapshots \
     --query 'DBSnapshots[?starts_with(DBSnapshotIdentifier,`fme-train-prod`)]'
   ```
   Either keep it for compliance/recovery, or `aws rds delete-db-snapshot`.
4. Check Secrets Manager for any retained secrets:
   `aws secretsmanager list-secrets --query 'SecretList[?starts_with(Name,`fme-train-prod`)]'`.

---

## Troubleshooting

### `cdk synth` fails with "Cannot resolve SSM parameter"

The Secrets Manager ARN parameters under `/fme-train/<env>/secrets/...`
must exist before `cdk synth` runs against a real account. For pure
local synth (no AWS calls), set `CDK_DEFAULT_ACCOUNT` to a placeholder
or run `cdk synth --no-lookups`.

### App Runner stuck in `CREATE_FAILED` with image-not-found

You need at least one image in the ECR repo (`fme-train-<env>`) tagged
to match what the task definition references (`:latest` by default, or
the tag passed via `cdk deploy -c image_tag=<sha>`).

### Budget alarm reports "no cost data yet"

AWS Budgets needs ~24h of cost data before the first evaluation. New
deploys fire alarms based on forecast, not actuals.

---

## Out of scope for this directory

* Any application code (FastAPI, worker, migrations) — lives at the
  repo root.
* GitHub Actions workflows — those live in `.github/workflows/` and
  call `cdk deploy` from CI.
* Manual seed data scripts (`runs.json`, `update-job.json` migrations)
  — separate one-shot scripts in the app codebase.
