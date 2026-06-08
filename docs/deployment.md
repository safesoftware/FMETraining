# Deploying the FME Training app

This is the operator runbook for the FME Training Automation web app. It covers how to deploy a new version to production, how to roll back if something goes wrong, how to read the production health page, and what to do when things look off. The actual deploy is a single button click in GitHub — you don't need to SSH anywhere for the normal flow.

## How to deploy

**Summary:** open GitHub Actions, click "Deploy to prod", click "Run workflow", click the green button. That's it.

Detailed steps:

1. Open the repo in GitHub: <https://github.com/safesoftware/fme-training-automation>.
2. Click the **Actions** tab at the top of the page.
3. In the left sidebar, click the workflow named **Deploy to prod**.
4. On the right side of the workflow page, click the **Run workflow** dropdown button.
5. Leave the `ref` input as `main` to deploy the current tip of the main branch. To deploy a different commit, paste a full git SHA (or a branch/tag name) into the `ref` field. Defaults to `main`.
6. Click the green **Run workflow** button to confirm.

> Screenshots will be added after the first successful production deploy.

You can also skip the manual click entirely: every push to `main` triggers the same workflow automatically. The manual button is for when you want to deploy a non-`main` ref or re-run a deploy.

### What happens next

A new run appears at the top of the workflow page within a few seconds. Click it to watch the live log. A typical deploy takes about 30 seconds from click to green checkmark.

The log lines worth watching all start with `[deploy]` — those come from the deploy script running on the production box. You'll see things like:

- `[deploy] starting forward deploy of ref=main`
- `[deploy] pre-deploy health check OK`
- `[deploy] atomic checkout to origin/main`
- `[deploy] restarting fme-train-web.service`
- `[deploy] deploy complete: <old-sha> -> <new-sha>`

A green checkmark on the workflow run means the deploy finished and the post-deploy health check returned 200 OK. A red X means something failed — see [When something looks wrong](#when-something-looks-wrong) below. The deploy script automatically rolls back to the previous good version if its own post-deploy health check fails, so a red X usually means you're already back on the previous version, not stuck on broken code.

## How to roll back

**Summary:** same workflow as deploying, but paste the previous good SHA into `ref`.

Most of the time you do not need to roll back manually. The deploy script rolls itself back automatically when its post-deploy health check fails. The instructions below are for the rare case where the deploy "succeeded" (green checkmark) but you later discover the new version is broken in production.

Two options:

**Option A — re-run the workflow at the previous SHA (preferred):**

1. Find the SHA of the previous-good deploy. Easiest source: the **Actions** tab, look at the previous successful run of "Deploy to prod" — its commit SHA is shown in the run header.
2. Click **Run workflow**, paste that SHA into the `ref` input, click the green button.
3. The workflow will deploy that older commit just like any other deploy.

**Option B — SSH to the box and run `--rollback`:**

You'll need SSH access (ask Sam if you don't have it). Then run:

```
ssh fmetrain@fme-train.base.safe.com bash /opt/fme-train/bin/deploy-prod.sh --rollback
```

The `--rollback` flag tells the deploy script to read the SHA at `/var/lib/fme-train/last-good-sha` (the last deploy that passed its post-deploy health check) and re-deploy it. It does *not* update the last-good-sha file — by definition the rollback target is already the previously-known-good version.

## Reading the health page

The production health endpoint is <https://fme-train.base.safe.com/health>. Open it in any browser. It returns JSON that looks like this:

```
{
  "status": "ok",
  "version": "abc1234567890def...",
  "environment": "production"
}
```

What the fields mean:

- **`status`** — `"ok"` means the app process is up and its dependencies (database, etc.) are reachable. `"degraded"` means the process is running but at least one dependency check failed. The page still returns HTTP 200 in both cases; you have to look at the JSON body to tell the difference.
- **`version`** — the full git SHA of the currently-deployed commit. Compare against the SHA shown in the GitHub Actions run to confirm a deploy actually took effect.
- **`environment`** — always `"production"` on the production box. If you see something else, you're looking at the wrong URL.

Quick sanity check after a deploy: refresh the `/health` URL and confirm `version` matches the SHA you just deployed.

## When something looks wrong

If a user reports an outage or a deploy failed unexpectedly, walk through these four checks in order:

1. **Is `/health` returning 200 with `"status": "ok"`?** Open <https://fme-train.base.safe.com/health> in a browser. If the JSON shows `"status": "degraded"` or the page doesn't load at all, move to step 2. If `status` is `ok` and `version` matches what you expected, the app is healthy — the user's issue is probably elsewhere (browser cache, their account, etc.).

2. **What does the web service log say?** SSH into the box and tail the systemd journal. ("SSH" means logging into a remote server over a secure shell; "systemd" is the Linux service manager that keeps the app running and restarts it on crashes.)

   ```
   ssh fmetrain@fme-train.base.safe.com journalctl -u fme-train-web -n 100 --no-pager
   ```

   This shows the last 100 lines of the web service log. Look for Python tracebacks, repeated 5xx errors, or `[deploy]`-prefixed lines from the most recent deploy.

3. **Is the disk full?** A full disk is the most common preventable production outage. Run:

   ```
   ssh fmetrain@fme-train.base.safe.com df -h /var/lib/fme-train /
   ```

   Each line of output has a `Use%` column. If either filesystem is over 85%, page Sam — disk cleanup needs a human decision about what to delete.

4. **Page Sam.** If steps 1-3 didn't reveal the problem, or you found something but aren't sure what to do about it: email <sam.walker@safe.com> with the timestamp, what you saw (paste the JSON from `/health` and any relevant log lines), and what you've already tried. If it's an active outage, Slack works too.

## GitHub Actions secrets

The deploy workflow reads three secrets from the repository's GitHub Actions settings (Settings → Secrets and variables → Actions):

- **`DEPLOY_HOST`** — the EC2 instance's hostname (e.g. `fme-train.base.safe.com`).
- **`DEPLOY_USER`** — the Linux user the workflow SSHes in as. This is `fmetrain`.
- **`DEPLOY_SSH_KEY`** — the private SSH key (the multi-line PEM-format one, including the `-----BEGIN OPENSSH PRIVATE KEY-----` and `-----END` lines) for the deploy user. Paste the whole file contents into the secret value. To rotate: generate a new keypair, add the public half to `~fmetrain/.ssh/authorized_keys` on the box, then update this secret with the new private half and remove the old line from `authorized_keys`.

**Until these three secrets are set, the workflow is intentionally a no-op.** The first step in the workflow checks for `DEPLOY_HOST` and, if it's empty, logs `DEPLOY_HOST not set; skipping deploy` and exits 0 (success). That's expected behavior for a freshly-cloned repo or before EC2 has been provisioned — not a bug.

## Where things live

Cross-references for when you need to dig deeper:

- `.github/workflows/deploy-prod.yml` — the GitHub Actions workflow itself (added in KNOW-2293). Defines the triggers, the SSH steps, and the failure-rollback step.
- `bin/deploy-prod.sh` — the deploy script that runs on the EC2 box (hardened in KNOW-2296). Implements the pre/post health gates, atomic checkout, the `--rollback` flag, and the `DEPLOY_DRY_RUN=1` smoke-test mode.
- `docs/plans/2026-05-05-multi-user-web-app-ec2-alternative.md` — the architecture plan that explains *why* the deploy looks like this (single EC2 box, single button, in-flight runs continue on old code, etc.).
- `AGENTS.md` — top-level entry point for anyone (human or AI) working in this repo.
