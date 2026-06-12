# FME Training Automation

## Quick Start

Run the launcher script for your operating system. It will check all prerequisites, install any missing Python packages, and open the tool in your browser automatically.

**Windows**
```
launch.bat
```

**macOS / Linux**
```bash
bash launch.sh
```

The only thing you need to set up manually is a `.env` file with your **OpenAI API and Jira keys** — the script will create one from the template and prompt you to fill it in if it doesn't exist.

> The rest of this document describes the underlying pipeline in detail. **End-users running the browser UI do not need to read further.**

---

This repositiory extends the FMETraining repository to automate training update tasks using AI.

This repository contains an archive of Safe Software's training content, including:

1. Archived course manuals (2016-2020) 
2. Content for the original FME Academy online learning platform (2020-2022)
3. Content from the [relaunched FME Academy](https://academy.safe.com/) online learning platform (2023-present)

The relaunched FME Academy content is also [available on S3](https://safeskilljar.s3.us-west-2.amazonaws.com/index.html).

This training material can be reused and adapted under our [Terms of Use](https://engage.safe.com/legal/terms-and-conditions/fme-training/) and [License](LICENSE.md).

# FME Academy Content

Current FME Academy contentis available on the `main` branch. Past years' Academy content is archived in `fme-academy-YEAR` branches. The directory structure for 2024 forward contains:

- Folders by FME version
  - Within folders, learning paths
    - Within learning paths, courses
      - Within courses, lessons
        - Within lessons, the lesson content is stored in `index.html`. Some lessons have hotlinked images and some have images included in an `images` folder. We eventually hope to have all images saved in the repo.

# Issues/Questions

Any issues or questions can be directed to train@safe.com or by opening a GitHub Issue.

---

# Training Update Pipeline

The `api-approach` branch contains an AI-powered pipeline that analyzes Jira issues and identifies which training lessons need updating when a new FME version is released.

## Dev Container (Optional)

A `.devcontainer/devcontainer.json` is included for use with VS Code Dev Containers. Before opening the container, each developer must set a `CLAUDE_DIR` environment variable pointing to their local `.claude` folder so it can be bind-mounted into the container.

**macOS / Linux** — add to `~/.bashrc` or `~/.zshrc`:
```bash
export CLAUDE_DIR=$HOME/.claude
```

**Windows, running Claude Code from WSL** — add to your WSL `~/.bashrc`:
```bash
export CLAUDE_DIR=$HOME/.claude
```

**Windows, running Claude Code natively (not from WSL)** — add to your WSL `~/.bashrc`, substituting your Windows username:
```bash
export CLAUDE_DIR=/mnt/c/Users/YOUR_WINDOWS_USERNAME/.claude
```

After adding the line, reload your shell (`source ~/.bashrc`) and verify with `echo $CLAUDE_DIR`.

### One-time auth migration (first time only)

Claude's auth token is stored in `~/.claude.json`. Inside the container it is symlinked from `~/.claude/.claude.json` so it lives inside the bind-mounted directory and persists across rebuilds. Before opening the container for the first time, move the file into the `.claude` folder on your host:

**macOS / Linux / WSL**
```bash
mv ~/.claude.json ~/.claude/.claude.json
```

**Windows native Claude** — run in WSL, substituting your Windows username:
```bash
mv /mnt/c/Users/YOUR_WINDOWS_USERNAME/.claude.json /mnt/c/Users/YOUR_WINDOWS_USERNAME/.claude/.claude.json
```

If `~/.claude.json` does not exist yet (you haven't logged in), skip this step — the symlink will be created automatically and the file will be written there when you first run `claude` inside the container.

Then use **Dev Containers: Rebuild and Reopen in Container** in VS Code.

### Troubleshooting: container won't build (or Claude won't connect) on the company VPN

If the container fails to build while you're connected to the corporate VPN (Cisco AnyConnect) — typically a `docker pull ... i/o timeout` on `mcr.microsoft.com` — and Claude inside the container can't reach `api.anthropic.com`, the cause is almost always an **MTU mismatch**, not the VPN blocking traffic.

The VPN tunnel uses a smaller MTU (observed: **1390**) than Docker/WSL's default network (**1500**). Small TCP handshakes connect, but the larger TLS packets get silently dropped inside the tunnel ("MTU black hole"), so pulls hang and `api.anthropic.com` calls fail. The Windows host itself works because Windows auto-clamps to the VPN's MTU; WSL2/Docker does not.

**Quick check** (while on the VPN, from PowerShell) — the second ping failing confirms it:
```powershell
ping mcr.microsoft.com -f -l 1362 -n 2   # ~1390 bytes — should reply
ping mcr.microsoft.com -f -l 1472 -n 2   # 1500 bytes — "needs to be fragmented but DF set"
```

**Fix — put WSL in mirrored networking mode** so it inherits the host's adapters, routes, and MTU automatically (works on or off VPN, no toggling). Add to `~/.wslconfig` (Windows user home, e.g. `C:\Users\<you>\.wslconfig`):
```ini
[wsl2]
networkingMode=mirrored
```
Then run `wsl --shutdown` and **fully restart Docker Desktop**. Verify with `wsl -d Ubuntu -e sh -c "ip link show eth0 | grep -o 'mtu [0-9]*'"` — you should see `mtu 1390`, after which the build and Claude both work.

**Fallback** if mirrored mode misbehaves: revert that change and instead set `"mtu": 1350` in Docker Desktop → Settings → Docker Engine (more scoped — fixes container/runtime networking but may not fix the daemon's own base-image pull).

---

## Prerequisites

- **Python 3.9 or newer** — [Download Python](https://www.python.org/downloads/)
- **pip** (bundled with Python)
- An **OpenAI API key** with access to `gpt-4o-mini` (or `gpt-4o`)
- A **Jira API token** (optional — only needed for the `--jira-source api` mode)

## Installation

```bash
# 1. Clone or pull this branch
git checkout api-approach

# 2. Install Python dependencies
pip install -r requirements.txt
```

## Configuration

Copy (or create) a `.env` file in the repo root. All settings are optional except `OPENAI_API_KEY`:

```env
# Required
OPENAI_API_KEY=sk-...

# Optional — OpenAI model (default: gpt-4o-mini)
OPENAI_MODEL=gpt-4o-mini

# Optional — Jira project keys to include (comma-separated)
# Default: FOUNDATION,FMEENGINE,FMEFLOW,FMEFORM
JIRA_PROJECT_KEYS=FOUNDATION,FMEENGINE,FMEFLOW,FMEFORM

# Optional — Jira API (required only for --jira-source api)
JIRA_BASE_URL=https://your-instance.atlassian.net
JIRA_USER=your@email.com
JIRA_API_KEY=your_jira_api_token
JIRA_FILTER_ID=12345

# Optional — OpenAI concurrency / rate limiting
OPENAI_MAX_CONCURRENT=5
OPENAI_RPM=60

# Optional — include full lesson text in prompts (fewer false positives, ~3× cost)
INCLUDE_FULL_TEXT=true

# Optional — Skilljar integration (required for Push to Skilljar and Release tabs)
SKILLJAR_API_KEY=sk-live-...
SKILLJAR_DOMAIN=academy.safe.com   # only needed for Release tag updates

# Optional — AWS S3 (required if you push lessons that contain images)
# Images get uploaded here with public-read ACL and embedded directly in the
# lesson HTML — Skilljar's /v1/assets endpoint is not used because it returns
# 1-hour-signed URLs that expire mid-lesson. See "Image Upload Workflow" below.
AWS_S3_BUCKET=YourBucketName
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_S3_REGION=us-east-1
```

## Defining a Run (update-job.json)

Create `data/update-job.json` to describe what you want to update:

```json
{
  "to_version": "2025.2",
  "scope": {
    "lessons": [
      "2024.2/integrate-spatial-data/Analyze Spatial Data 2024.2/Exercise_ Analyze Spatial Data/index.html"
    ],
    "courses": [
      {"learning_path": "integrate-spatial-data", "course": "Analyze Spatial Data"}
    ],
    "learning_paths": [
      "integrate-spatial-data"
    ]
  }
}
```

| Scope key | Format | Description |
|---|---|---|
| `lessons` | List of full relative paths (`version/lp/course/lesson/index.html`) | Specific lessons to include |
| `courses` | List of `{"learning_path": "...", "course": "..."}` objects — course is the folder name without the version suffix | All lessons in matching courses |
| `learning_paths` | List of LP folder names | All lessons in matching learning paths |

All three keys are unioned. Omit the `scope` key (or use `{}`) to include all lessons.

## Running the Pipeline

```bash
# Full run (all 5 steps)
python pipeline.py

# Dry run — shows lesson/issue counts and estimated cost, makes no API calls
python pipeline.py --dry-run

# Use Jira API instead of CSV (fetches and caches to inputs/jira_api_cache.json)
python pipeline.py --jira-source api

# Force re-fetch from Jira API (ignore existing cache)
python pipeline.py --jira-source api --refresh-jira

# Run only specific steps (e.g. re-run assessment and report without re-fetching issues)
python pipeline.py --resume <RUN_ID> --steps 3,4,5

# Resume an interrupted run (skips already-completed steps)
python pipeline.py --resume <RUN_ID>

# Regenerate the HTML report only for an existing run
python pipeline.py --report-only <RUN_ID>

# Use a custom job file
python pipeline.py --job path/to/my-job.json

# Write artifacts to a custom directory
python pipeline.py --output-dir path/to/output
```

## Pipeline Steps

| Step | Name | Description |
|---|---|---|
| 1 | Build Manifest | Scans lesson HTML files and extracts structure (headings, steps, UI strings, images) |
| 2 | Build Changelog | Loads Jira issues from CSV or API and filters to the relevant version window |
| 3+4 | Assessment | Calls the OpenAI API to assess each (lesson, issue) pair for update likelihood |
| 5 | Report | Generates a self-contained HTML report |

## Viewing the Report

The HTML report (`artifacts/report-{RUN_ID}.html`) fetches its data from a JSON file via `fetch()`. Most browsers block `fetch()` for `file://` URLs, so you need a local HTTP server.

**Recommended — the FastAPI web app** (`app/`), which serves runs, reports, and the Lesson Edits tab on **http://localhost:8000**:

```bash
make up
# open http://localhost:8000, sign in, then open a run's report from "Recent Runs"
```

> **Legacy:** `python serve.py` (port **8080**) is the old single-user launcher. It is superseded by the FastAPI app and retained only for the Skilljar release flow until that ports across (KNOW-2307 / KNOW-2323). The standalone `python -m http.server 8080` below still works for *viewing* a report file (the Save feature falls back to a browser download).

Alternatively, use Python's built-in server (report viewing only — the Save feature will fall back to a browser download):

```bash
python -m http.server 8080
```

> **Note:** The server must run from the project root so that lesson images (e.g. `2024.2/...`) resolve correctly in the report.

### Lesson Edits Tab — Save to Version Folder

After running Step 6 (`--steps 6`), the **Lesson Edits** tab lets you review and accept/reject suggested text changes. When you click **Save to Version Folder**:

- `serve.py` computes the target path by replacing the source version with `to_version` from your `update-job.json` (e.g. `2024.2/...` → `2026.1/...`)
- Any pasted images embedded as `data:image/...;base64,...` URIs are uploaded to S3 first and the `<img>` tags are rewritten to point at the permanent S3 URL (see [Image Upload Workflow](#image-upload-workflow))
- Track-changes report markup and empty `<p></p>` separators left behind by contenteditable paste are stripped
- The lesson HTML is written to the new path
- Images are copied from the source lesson's `images/` folder to the target

If the target file already exists, you will be prompted to overwrite it.

### Push to Skilljar

Once a lesson is saved to the version folder, **Push to Skilljar** sends the accepted HTML to the live Skilljar lesson via `PATCH /v1/lessons/{id}`. The pre-flight dialog confirms one of three actions:

- **Update lesson** — the target lesson is already mapped in `data/skilljar-mapping.json`; only the HTML is patched
- **Create lesson** — the target course exists in Skilljar but the lesson does not; a new lesson is created and patched
- **Create course and lesson** — neither exists; both are created from the source course's metadata

Push requires `SKILLJAR_API_KEY` in `.env`. If the lesson contains pasted data URIs, they are uploaded to S3 the same way as Save to Version Folder.

### Image Upload Workflow

When pushed lessons reference images, those images need a publicly fetchable URL or Skilljar's renderer can't load them. Two cases:

**Pasted images (data: URIs).** When you paste an image — or HTML containing `<img src="data:image/…;base64,…">` from Word, Slack, or a webpage — the data URI lands in the contenteditable WYSIWYG. On Save to Version Folder or Push to Skilljar, the backend:

1. Walks the HTML for `<img src="data:image/…">` matches.
2. Decodes each unique base64 payload (deduped by content hash).
3. Uploads to your `AWS_S3_BUCKET` via `_s3_put` with `public-read` ACL — keys are `skilljar-uploads/<random>-pasted-<hash>.<ext>`.
4. Rewrites the `<img>` `src` to the permanent `https://s3.{region}.amazonaws.com/{bucket}/{key}` URL.

**Lesson `images/` folder (Release pipeline).** During release (`/api/release-execute`), every relative `<img src="images/foo.png">` that can't be resolved against the previous version's lesson HTML is uploaded to your S3 bucket the same way and rewritten in place.

Both paths bypass Skilljar's `POST /v1/assets` endpoint on purpose: per the Skilljar API spec (`docs/skilljar-api-04-20-2026.yaml`), `GET /v1/assets/{id}` returns "a signed download URL valid for 1 hour" — fine for API-side downloads, useless for embedding in `content_html`. Hosting on your own bucket gives URLs that don't expire.

Implementation: `pipeline/data_uri_upload.py` (paste path) and `pipeline/skilljar_release.py:_upload_and_rewrite_images` (release path). Both reuse `_s3_put` / `_s3_sign` from `pipeline/skilljar_push.py`.

The report includes:
- **Likelihood filters** (High / Medium / Low / None)
- **Status checklist** — mark each card as Active, Done, or Incorrect; status is saved in your browser's localStorage and persists between sessions
- **Learning path / Course / Lesson dropdowns**
- **Free-text search**
- **Sort** by likelihood, lesson name, or issue key
- **Recommendation IDs** (click to copy) for referencing specific findings

## Updating Course Content

Run `python sync_content.py` to update the training content from the source FMETraining repository.

---

## Testing

The project has an automated test suite under `tests/`. All tests run without API keys or a live browser.

### Setup

Testing dependencies are included in `requirements.txt`. Install them with:

```bash
pip install -r requirements.txt
```

### Running the Tests

```bash
# Run the full suite (unit + integration + mocked LLM)
pytest

# Run with verbose output
pytest -v

# Run only the fast unit tests
pytest tests/unit/

# Run integration tests (file I/O, no API calls)
pytest tests/integration/

# Run mocked LLM tests (OpenAI mocked with unittest.mock)
pytest tests/mocked_llm/

# Exclude browser tests (which require Playwright)
pytest -m "not browser"
```

The full suite runs in under 20 seconds with no network calls.

### Test Layers

| Layer | Location | What it tests |
|---|---|---|
| **Unit** | `tests/unit/` | Pure functions — version parsing, changelog filtering, post-processing logic |
| **Integration** | `tests/integration/` | HTML parsing and Step 1 (manifest) against fixture HTML; no API calls |
| **Mocked LLM** | `tests/mocked_llm/` | Step 6 post-processing with OpenAI mocked; validates silent failure detection, filters, and HTML stripping |
| **Browser** | `tests/browser/` | Playwright tests for report UI behaviour (requires separate Playwright install) |

### What the Tests Catch

The unit and mocked LLM tests are specifically designed to guard against the failure patterns documented in `AGENTS.md`:

- **Silent failures in Step 6** — `TestSilentFailureGuard` asserts `_call_openai` returns `None` after all retries fail, so callers can detect and log the failure rather than silently marking a lesson complete
- **`safe_note.png` false positives** — asserted filtered from `screenshot_updates` output
- **HTML tags in `suggested_text`** — asserted stripped for `change`-type edits, preserved for `add`-type
- **Stale `original_text`** (issue #74) — changes whose text no longer exists in the lesson HTML are dropped
- **Empty heading on auto-generated version changes** (issue #75) — `_ensure_version_changes` must populate `heading` from the nearest preceding `<h2>/<h3>`, not leave it blank
- **FMEENGINE filter for conceptual lessons** (issue #72) — FMEENGINE-only changes suppressed when lesson has no exercise steps

### Browser Tests (Optional)

Browser tests use [Playwright](https://playwright.dev/python/) and require a separate install:

```bash
pip install playwright
playwright install chromium
```

Run them with:

```bash
pytest -m browser
```

These tests open the generated report HTML in a headless browser and verify interactive behaviour: accept/reject popups, cascading markup correctness, save-to-disk flow, and Re-Run prefill state.