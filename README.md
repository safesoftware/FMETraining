# FME Training Automation

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

## Prerequisites

- **Python 3.10 or newer** — [Download Python](https://www.python.org/downloads/)
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

The HTML report (`artifacts/report-{RUN_ID}.html`) fetches its data from a JSON file via `fetch()`. Most browsers block `fetch()` for `file://` URLs, so serve the **project root** with Python's built-in HTTP server:

```bash
# Run from the project root (not the artifacts/ subdirectory)
python -m http.server 8080
# Then open http://localhost:8080/artifacts/report-{RUN_ID}.html
```

> **Note:** The server must run from the project root so that lesson images (e.g. `2024.2/...`) resolve correctly in the report.

The report includes:
- **Likelihood filters** (High / Medium / Low / None)
- **Status checklist** — mark each card as Active, Done, or Incorrect; status is saved in your browser's localStorage and persists between sessions
- **Learning path / Course / Lesson dropdowns**
- **Free-text search**
- **Sort** by likelihood, lesson name, or issue key
- **Recommendation IDs** (click to copy) for referencing specific findings

## Updating Course Content

Run `python sync_content.py` to update the training content from the source FMETraining repository.