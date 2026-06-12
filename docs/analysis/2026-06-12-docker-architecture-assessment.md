# Docker / Local-Dev Architecture Assessment

> **Status: DRAFT assessment** — uncommitted, read-only architect review. No code changed.
> **Date:** 2026-06-12 · **Author:** architecture review (read-only) · **Parent epic:** KNOW-2257 (multi-user web app)
> **Scope reviewed:** `Dockerfile`, `docker-compose.yml` (+ `docker-compose.override.yml`), `.dockerignore`,
> `docker/entrypoint.sh`, `app/config.py`, `pipeline/config.py`, `app/services/worker_lifecycle.py`,
> `app/services/pipeline_runner.py`, `worker.py`, `Makefile`, `bin/setup-ec2.sh`, `bin/deploy-prod.sh`,
> `docs/running-locally.md`, plus the `pipeline/*` modules that read paths.

---

## 1. Verdict

**Targeted fixes suffice for the bugs — but they should be applied as ONE structural change, not N per-bug patches.**

The containerization is fundamentally sound: the image, the dual-mode entrypoint, the Compose stack, and the
*app layer* (`app/config.py` → `artifacts_root`, `lesson_content_root`, `database_url`) are coherent and already
container-aware. The bug class has a single, narrow root cause: **`pipeline/config.py` derives every runtime path
from `REPO_ROOT = Path(__file__).parent.parent`, and several `pipeline/*` modules read content/cache paths from
those globals directly instead of from the values the worker already threads in.** That is one seam, not a design
flaw spread across the system. The right move is therefore *option B+C combined but minimal*: give the pipeline a
single container-aware source of truth for the *content root* and the *cache dir* (the only two globals that are
genuinely location-sensitive at runtime), and make the image's writable-dir story explicit rather than a one-off
`mkdir/chown`. KNOW-2352 and KNOW-2353 are not independent bugs — they are the same `REPO_ROOT`-blindness surfacing
at different call sites, and at least one more instance (step 6 / `edit_suggestions.py`) is still latent on `main`.
A full rewrite (S3-backed content source, etc.) is **not** warranted now and is already tracked as future work.

---

## 2. Root-cause architecture analysis

### 2.1 The two-config seam (how the worker reaches the pipeline)

The worker does **not** run `pipeline.py` as a subprocess. The path is:

```
docker/entrypoint.sh (ENTRYPOINT_MODE=worker)
  → python -m worker            (worker.py)
    → run_worker(..., step_body=make_step_body())     (app/services/worker_lifecycle.py)
      → make_step_body()        (app/services/pipeline_runner.py)
          reads get_settings()  → app/config.py  (container-aware)
          → calls pipeline/manifest.py, changelog.py, assessment.py, report.py, edit_suggestions.py
            in asyncio.to_thread, passing explicit output_dir / repo_root args
```

So the worker runs *in the same Python process* as the app and **does** have access to the container-aware
`Settings`. `make_step_body()` correctly resolves `Settings.artifacts_root` and `Settings.lesson_content_root` and
threads them into the legacy functions as explicit arguments. This is the intended (and good) design: the legacy
functions take `output_dir=` and `repo_root=` so they bypass the pipeline globals.

**The seam leaks wherever a `pipeline/*` module ignores its passed-in root and reaches back to `config.REPO_ROOT`
or a `REPO_ROOT`-derived global.** Concretely, on `main` today:

| `pipeline/config.py` global | Derives from | Threaded in by worker? | Status in container |
|---|---|---|---|
| `ARTIFACTS_DIR` (`REPO_ROOT/artifacts`) | REPO_ROOT | **Yes** — `make_step_body` passes `output_dir` from `Settings.artifacts_root` | ✅ Bypassed correctly |
| content root for manifest | REPO_ROOT | **Yes** — step 1 gets `repo_root=Settings.lesson_content_root` | ✅ Correct (this was the KNOW-2353 fix point) |
| `JIRA_CACHE_PATH` (`REPO_ROOT/.cache/...`) | REPO_ROOT | **No** — read directly in `jira_api.py:55` | ⚠️ **KNOW-2352**: `/app/.cache` not writable by `appuser` |
| content root for **edit suggestions** | REPO_ROOT | **No** — `edit_suggestions.py:263, 665` read `config.REPO_ROOT / lesson_dir` | 🔴 **Latent KNOW-2353 #2**: step 6 still reads lesson HTML from `/app`, not `/content` |
| content root for **alt-text enrich** | REPO_ROOT | **No** — `enrich_alt_text.py:201, 206` use `config.REPO_ROOT` | 🔴 Latent (same class; opt-in feature, less exercised) |
| `DATA_DIR` (`product-mapping.json`, `jira_export.csv`) | REPO_ROOT | **No** — read via globals | 🟡 Works *by coincidence*: Compose mounts `./data:/app/data`, the exact path `REPO_ROOT/data` resolves to |
| `PROMPTS_DIR` | REPO_ROOT | **No** | 🟡 Works: `prompts/` is **baked** at `/app/prompts` (not in `.dockerignore`) and also mounted |
| `SKILLJAR_MAPPING_PATH` (`REPO_ROOT/data/...`) | REPO_ROOT | n/a (Skilljar flow not in worker yet) | 🟡 Same coincidence as DATA_DIR |

**Conclusion:** Two globals are genuinely *runtime-location-sensitive* and currently broken or latent — the **cache
dir** (`JIRA_CACHE_PATH`) and the **content root** (used by `edit_suggestions`, `enrich_alt_text`, and historically
`manifest`). Everything else "works" only because `data/`/`prompts/` happen to be mounted/baked at the precise
`/app/...` path that `REPO_ROOT`-relative resolution expects. That coincidence is fragile and is the same trap that
produced 2352/2353.

The fix is a **single source of truth for the two location-sensitive roots**, consumed by *both* layers:

- a `content_root` the pipeline reads from `Settings`/env (not `REPO_ROOT`), and
- a writable `cache_root` (and by extension any writable scratch) read from env, defaulting to a writable place.

### 2.2 Ownership model

The image bakes code at `/app` via `COPY --chown=appuser:appuser . /app`, then runs as `appuser` (uid 10001).
This is internally fine **for the baked image**. The breakage comes from the **bind mounts**:

- Compose mounts host dirs (`./app`, `./pipeline`, `./data`, `./artifacts`, and in the override `.:/content` and
  `./.github`) over `/app/...`. Bind mounts carry the **host** ownership (uid 1000 / `vscode`), not `appuser`
  (10001). So inside the container the mounted trees are owned by an unknown-to-the-container uid.
- Read paths are fine (appuser can read world-readable files). **Write paths fail**: appuser cannot create
  `/app/.ruff_cache` (Makefile works around it with `RUFF_CACHE_DIR=/tmp`), and could not create `/app/.cache`
  (the KNOW-2352 crash). The Dockerfile patches *that one path* with `RUN mkdir -p /app/.cache && chown ...` — but
  a bind mount over `/app` at runtime can still shadow it, and the next REPO_ROOT-relative writable path will hit
  the same wall. **This is a recurring bug class, not a one-off.**

The `mkdir/chown` in the Dockerfile is an ad-hoc patch. A coherent model is: **never write under `/app` at
runtime.** All writable runtime state (cache, scratch, artifacts, drafts) should live under a dedicated writable
root (e.g. `/var/lib/fme-train` or a tmpfs) that is either a named volume or explicitly created+owned, and is
pointed to by env vars that *both* layers read. That removes the uid-mismatch bug class entirely rather than
chasing each new write site.

> Matching uids (build the image as uid 1000, or run Compose with `user: "1000:1000"`) is a *tempting* shortcut but
> couples the image to the dev host's uid and diverges from prod (where the app runs as `fmetrain`, a different
> uid). Prefer "no writes under the mounted tree" over "make the uids match."

### 2.3 Content/data baking vs mounting

`.dockerignore` strips the version content trees (`2021.0 … 2026.1`), `artifacts`, `data`, `tests`, `infra`. The
image is therefore *content-free* by design (Skilljar is the intended canonical source for prod). For local QA,
content is restored only via **`docker-compose.override.yml`**, which mounts the whole repo read-only at `/content`
and sets `LESSON_CONTENT_ROOT=/content`.

The inconsistency that bites: **`.env.compose` sets `LESSON_CONTENT_ROOT=/app`**, but `/app` has *no* content
(it was `.dockerignore`'d). Only the override flips it to `/content` (where content is actually mounted). So the
base configuration advertises a content root that does not contain content — exactly the confusion behind 2353.
The well-known-root invariant is the fix: **pick one mount point (`/content`) and one env var (`LESSON_CONTENT_ROOT`)
that BOTH layers read, set it consistently, and delete the misleading `/app` default.**

### 2.4 Prod vs local divergence (quantified)

Prod works **because it is still the old single-root layout** — the very thing containerization split apart:

| Dimension | Prod (`bin/setup-ec2.sh`) | Local Docker | Divergent? |
|---|---|---|---|
| Code location | `/opt/fme-train` (git clone) | `/app` (baked) + bind mounts | Yes |
| Content location | **In-repo** at `/opt/fme-train/<version>/...` (version folders are tracked on `main`) | Mounted at `/content` (override only) | **Yes — key** |
| `REPO_ROOT` resolves to | `/opt/fme-train` | `/app` | Yes |
| `LESSON_CONTENT_ROOT` | **unset** → app default `.` → CWD = `/opt/fme-train` | `/app` (base, wrong) / `/content` (override) | **Yes** |
| → content root vs `REPO_ROOT` | **Identical** (`/opt/fme-train`) | **Different** (`/content` ≠ `/app`) | **This is the divergence engine** |
| Writable repo / `.cache` | Yes (owned by `fmetrain`, writable) | No (`/app` baked root-owned; mounts host-uid) | **Yes** |
| `ARTIFACTS_ROOT` | unset → app default `/var/lib/fme-train/artifacts` (created by setup-ec2) | `/app/artifacts` via `.env.compose` + override mount | Yes (both work) |
| Run user | `fmetrain` (native uid) | `appuser` uid 10001 | Yes |
| Process model | systemd unit `fme-train-worker@<run_id>` (`python -m worker`) | in-process dispatcher (`TASK_DISPATCHER=inprocess`) | Yes (different dispatcher) |

**The risk is real and asymmetric.** On prod, `content_root == REPO_ROOT` by construction, so *every*
`config.REPO_ROOT`-relative content/cache read resolves correctly — the latent step-6 and alt-text bugs **cannot
fire on prod** and would pass any prod-only test. Locally they fire because the roots differ. The drift therefore
runs **"green on prod, red locally"** for the content-root bugs (the opposite of the usual fear), which is why these
stayed latent until a full local run completed today. The *inverse* danger also exists: anything that "works
locally" only because of the `/content` override (read-only, whole-repo mount) is not how prod sources content, so
a local pass does not prove the prod content path. Collapsing the two layers onto one env-driven `content_root`
removes the divergence in both directions.

---

## 3. Remediation options

### Option A — Keep patching per-bug (status quo)
Fix each `REPO_ROOT` leak as it's discovered (2352 done, 2353 in flight, step-6/alt-text next).
- **Effort:** Low per bug. **Risk:** High cumulative — guaranteed recurrence; each patch (e.g. the Dockerfile
  `mkdir /app/.cache`) adds drift and comments explaining a coincidence. No prevention. **Not recommended.**

### Option B — Unify path/config into one container-aware source both layers use
Add a `content_root` and `cache_root` (writable scratch) to the pipeline that resolve from env/`Settings`, defaulting
to `REPO_ROOT` so prod and the legacy CLI are unchanged. Replace the direct `config.REPO_ROOT / lesson_dir` reads in
`edit_suggestions.py` (and `enrich_alt_text.py`) with the threaded-in content root (pass it down from
`make_step_body` exactly as step 1 already does). Point `JIRA_CACHE_PATH` at `cache_root` (env, writable).
- **Effort:** Medium (a handful of call sites + signature plumbing already modeled by `manifest.build_manifest`).
- **Risk:** Low — default-to-`REPO_ROOT` keeps prod/CLI behavior identical; change is additive. **Core of the fix.**

### Option C — Fix the image ownership / mount model
Stop writing under `/app` at runtime. Move all writable runtime state to a dedicated writable root (named volume or
explicitly-owned `/var/lib/fme-train`), drive it by env var, and **remove** the ad-hoc `mkdir /app/.cache` once
`cache_root` no longer lives under `/app`. Make the `LESSON_CONTENT_ROOT` story consistent (one mount point
`/content`, drop the misleading `/app` default in `.env.compose`).
- **Effort:** Low–Medium (Dockerfile + compose + `.env.compose` edits). **Risk:** Low. Eliminates the uid-mismatch
  write-failure class.

### Option D — Combination (B + C, minimal) — **RECOMMENDED**
Do B and C together as a single coherent change, because they share the same root cause (REPO_ROOT-blindness for
location-sensitive paths) and the same invariant ("both layers read runtime roots from env, never from a baked
`__file__` path; never write under the mounted code tree").

**Recommendation: Option D.** It is bounded (two roots: `content_root`, `cache_root`/scratch), low-risk
(defaults preserve prod + legacy CLI), and it closes the whole bug class rather than the two known instances. A
full content-source rewrite (SkilljarContentSource, S3) is explicitly *out of scope* — it's already stubbed and
tracked for the future migration; pulling it in now would be over-engineering.

---

## 4. Prevention — in-container end-to-end smoke test

**Why it was missing:** no test ever ran a *full pipeline inside the container against the mounted content with the
non-root user*. Unit tests pass `tmp_path` for both roots, so they never exercise the `/app`-vs-`/content` split or
the appuser write-permission reality. Both 2352 and 2353 would have been caught by a single in-container run.

**Design — `make smoke` (cheap, ~30–60s, no OpenAI spend):**

1. **What it runs:** a worker dry-run over a **1-lesson scope** through at least **steps 1, 2, and 6** (these three
   touch every leaky surface: step 1 = content root for manifest; step 2 = `JIRA_CACHE_PATH` write under the
   cache root with `--jira-source api` *or* the CSV read for `csv`; step 6 = content root for `edit_suggestions`).
   Step 3 LLM assessment runs in `dry_run` mode (no real API calls) so there is no spend and no API key needed.
2. **How:** `docker compose run --rm worker-runner` against a tiny seeded run row (or a thin `python -m worker`
   harness that builds an in-memory 1-lesson scope), with the **override active** (so content is at `/content`,
   `LESSON_CONTENT_ROOT=/content`) and **as `appuser`** (the real runtime user, so permission failures surface).
3. **Assertions (the guard):**
   - exit code 0 / final status `done`;
   - the manifest resolved **≥1 lesson** (catches "content root points at an empty `/app`" → would have caught 2353);
   - **no `PermissionError`** and **no `FileNotFoundError`** in the run log (catches the `/app/.cache` write →
     2352, and any REPO_ROOT-relative content miss → 2353/step-6);
   - the per-run artifact dir exists and contains `manifest-*.json` + `report-*.html`.
4. **Where it runs:** a `make smoke` target plus a CI job (GitHub Actions) that does `docker build` →
   `docker compose up -d postgres minio-init` → `make migrate` → seed 1 run → `make smoke`. Pin it to **no network
   egress to OpenAI** (dry_run) so it's deterministic and free. Use a committed synthetic 1-lesson content fixture
   (a few-KB `index.html` under a fake `9999.0/.../index.html`) so the test does not depend on the large version
   corpus and runs identically in CI and locally.

This is the cheapest possible guard that exercises the exact seam (container layout × non-root user × mounted
content × writable scratch) the unit tests structurally cannot.

---

## 5. Proposed ticket breakdown (parent: KNOW-2257)

| # | Title | Type | Notes |
|---|---|---|---|
| 1 | **Pipeline `content_root`/`cache_root` single source of truth** (Option B) | Story | Add env/`Settings`-driven `content_root` + writable `cache_root` to the pipeline; default to `REPO_ROOT` (no prod/CLI change). Thread `content_root` into `edit_suggestions.py` (lines 263, 665) and `enrich_alt_text.py` (201, 206); point `JIRA_CACHE_PATH` at `cache_root`. Closes the 2352/2353 *class*. **Supersedes/absorbs in-flight KNOW-2353** and folds in the latent step-6 + alt-text leaks. |
| 2 | **Image/mount ownership + writable-root model** (Option C) | Story | Move runtime writable state off `/app`; drive by env; remove the ad-hoc `mkdir /app/.cache` once `cache_root` relocates; make `LESSON_CONTENT_ROOT` consistent (one mount `/content`; drop the misleading `/app` default in `.env.compose`). |
| 3 | **`make smoke` in-container 1-lesson dry-run guard + CI job** (Prevention) | Story | The §4 smoke test + synthetic 1-lesson fixture + GitHub Actions job. Asserts no Permission/FileNotFound errors, ≥1 lesson resolved, artifacts produced. **The guard that would have caught 2352/2353.** |
| 4 | **(Optional) Pipeline config audit / lint** | Task | A quick test or grep-guard that fails CI if a *new* `config.REPO_ROOT / <content-or-cache path>` read is introduced in `pipeline/*`, so the seam can't silently re-leak. Low effort; cheap insurance. |

**Sequencing:** #1 + #2 land together (same root cause, same PR ideally), then #3 makes the fix self-defending; #4
is a nice-to-have that prevents regression of the pattern.

---

## 6. Appendix — load-bearing evidence

- `app/services/pipeline_runner.py:95-96` — worker resolves `Settings.artifacts_root` + `Settings.lesson_content_root`
  and threads them in (the *correct* pattern step 1 already follows: `_run_step_1(... repo_root=_content_root)`).
- `pipeline/edit_suggestions.py:665` — `html_path = config.REPO_ROOT / lesson_dir / "index.html"` (and `:263`) —
  **latent KNOW-2353 #2**: step 6 ignores the content root.
- `pipeline/enrich_alt_text.py:201,206` — same `config.REPO_ROOT` pattern.
- `pipeline/jira_api.py:55` + `pipeline/config.py:63` — `JIRA_CACHE_PATH = REPO_ROOT/.cache/...` → KNOW-2352.
- `Dockerfile:114` — `RUN mkdir -p /app/.cache && chown appuser:appuser /app/.cache` (the one-off patch).
- `.env.compose:67` `LESSON_CONTENT_ROOT=/app` vs `docker-compose.override.yml:21` `LESSON_CONTENT_ROOT=/content`
  — the inconsistent content-root default.
- `bin/setup-ec2.sh` — prod clones to `/opt/fme-train`, content in-repo, `LESSON_CONTENT_ROOT`/`ARTIFACTS_ROOT`
  unset (defaults); `git ls-tree HEAD` confirms `2021.0 … 2026.1` are tracked on `main` → prod content is in-repo,
  so `content_root == REPO_ROOT` on prod and these bugs cannot fire there.
- `app/main.py:210` + `app/config.py:105` — `/artifacts` static mount and worker both use `Settings.artifacts_root`
  (`/var/lib/fme-train/artifacts`), correctly bypassing `pipeline.config.ARTIFACTS_DIR` (this layer is *not* leaky).
