"""
Configuration module for the FME Training Update Pipeline.

Loads environment variables from .env and exposes typed constants.
Import this module before any other pipeline module.
"""

import json
import os
import re
from pathlib import Path

from dotenv import load_dotenv

APP_VERSION = "0.3.0"
APP_NAME = "FME Training Update Assistant"

# Locate repo root (parent of the pipeline/ package directory)
REPO_ROOT: Path = Path(__file__).parent.parent.resolve()

# Load .env from repo root
load_dotenv(REPO_ROOT / ".env")

# ---------------------------------------------------------------------------
# Location-sensitive runtime roots (the single source of truth — KNOW-2354)
#
# Only TWO globals are genuinely location-sensitive at runtime: the read-only
# lesson-content corpus and the writable scratch/cache dir. Everything else
# (prompts/, data/, artifacts/) either is baked/mounted at its exact
# REPO_ROOT-relative path or is threaded in explicitly by the worker. These
# two roots are env-driven and BOTH default to their historical REPO_ROOT
# location, so when the envs are unset (prod box + CLI) behaviour is identical
# to before. In the Docker split the code lives at /app (root-owned,
# content-stripped) while content is bind-mounted at /content and writable
# scratch lives on a separate writable mount — see
# docs/analysis/2026-06-12-docker-architecture-assessment.md.
# ---------------------------------------------------------------------------

# Root of the versioned lesson-content corpus (e.g. 2025.0/, 2026.1/). On the
# box and for the CLI this IS the repo root, so it defaults to REPO_ROOT and
# behaviour is unchanged. In the container the corpus is bind-mounted at a
# SEPARATE path (/content) from the code (/app, = REPO_ROOT), so the worker
# sets LESSON_CONTENT_ROOT=/content. Lesson HTML / image reads must resolve
# against THIS root, not REPO_ROOT (KNOW-2353). Mirrors app.config
# Settings.lesson_content_root. Do NOT use this for prompts/, data/, or
# artifacts — those stay on their own repo-relative roots.
LESSON_CONTENT_ROOT: Path = Path(os.getenv("LESSON_CONTENT_ROOT") or REPO_ROOT)

# Writable scratch/cache root. On the box and for the CLI this defaults to
# REPO_ROOT/.cache (writable, gitignored) so behaviour is unchanged. In the
# container /app is root-owned and not writable by appuser, so compose points
# FME_CACHE_DIR at a writable bind-mounted dir — that retires the ad-hoc
# `mkdir /app/.cache` Dockerfile patch (KNOW-2352) and means NOTHING writes
# under /app at runtime. Anything the pipeline needs to write outside the
# per-run artifacts dir (e.g. the Jira metadata cache) MUST live under here.
CACHE_ROOT: Path = Path(os.getenv("FME_CACHE_DIR") or (REPO_ROOT / ".cache"))

# WRITABLE root for the "Save to Version Folder" output (Wave 2, S3-content
# publish side). The new-version lesson tree that Save writes and the Skilljar
# release reads/pushes lives HERE, not under LESSON_CONTENT_ROOT — which is the
# READ-ONLY public mirror when CONTENT_SOURCE=s3mirror. Defaults to REPO_ROOT so
# the box + CLI keep their historical in-repo layout; the container/EC2 box set
# SAVED_VERSIONS_ROOT to a writable mount. Mirrors app.config
# Settings.saved_versions_root. CONTRACT (P3): saved lessons live at
#   {SAVED_VERSIONS_ROOT}/{to_version}/{lp}/{course} {to_version}/{lesson}/index.html
SAVED_VERSIONS_ROOT: Path = Path(os.getenv("SAVED_VERSIONS_ROOT") or REPO_ROOT)


# ---------------------------------------------------------------------------
# Lesson-content source selection (KNOW-2360, S3-mirror keystone)
#
# Selects which backend pipeline.content_source.get_content_source() builds:
#   "local"    — read the on-disk corpus under LESSON_CONTENT_ROOT (default;
#                identical to historical behaviour for the box + CLI + tests).
#   "s3mirror" — read all lesson HTML/images from the public S3 mirror over
#                anonymous HTTPS, and discover lessons via ListObjectsV2.
# CONTENT_S3_BASE_URL is the mirror's origin (no trailing slash); keys mirror
# the corpus layout byte-for-byte. Mirrored into app.config Settings so the app
# and pipeline agree. Defaults keep "local" behaviour when the envs are unset.
# ---------------------------------------------------------------------------
CONTENT_SOURCE: str = os.getenv("CONTENT_SOURCE", "local").strip().lower()
CONTENT_S3_BASE_URL: str = os.getenv(
    "CONTENT_S3_BASE_URL", "https://safeskilljar.s3.us-west-2.amazonaws.com"
).rstrip("/")


# ---------------------------------------------------------------------------
# Credentials / API config
# ---------------------------------------------------------------------------

def _require_env(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.sample to .env and fill in your credentials."
        )
    return val


def get_openai_api_key() -> str:
    """Return OPENAI_API_KEY, raising if not set."""
    return _require_env("OPENAI_API_KEY")


OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
OPENAI_MAX_CONCURRENT: int = int(os.getenv("OPENAI_MAX_CONCURRENT", "5"))
OPENAI_RPM: int = int(os.getenv("OPENAI_RPM", "60"))

# Include full stripped lesson text in LLM prompts (~3x input token cost, fewer false positives)
INCLUDE_FULL_TEXT: bool = os.getenv("INCLUDE_FULL_TEXT", "false").lower() == "true"

_raw_project_keys = os.getenv("JIRA_PROJECT_KEYS", "FOUNDATION,FMEENGINE,FMEFLOW,FMEFORM")
JIRA_PROJECT_KEYS: list[str] = [k.strip() for k in _raw_project_keys.split(",") if k.strip()]

# Jira API credentials (for --jira-source api)
JIRA_BASE_URL: str = os.getenv("JIRA_BASE_URL", "").rstrip("/").replace("http://", "https://")
JIRA_USER: str = os.getenv("JIRA_USER", "")
JIRA_API_TOKEN: str = os.getenv("JIRA_API_KEY", "")  # reuse JIRA_API_KEY from .env
JIRA_FILTER_ID: str = os.getenv("JIRA_FILTER_ID", "")
# Slim metadata-only cache: descriptions are NOT persisted here.
# Jira issue descriptions (which contain customer PII) are fetched on demand
# and held in memory for the duration of a run only. See pipeline/jira_api.py.
# Lives under the writable CACHE_ROOT (default REPO_ROOT/.cache, gitignored
# via /.cache/) so it resolves to a writable dir in every layout (KNOW-2354).
JIRA_CACHE_PATH: Path = CACHE_ROOT / "jira_api_cache.json"

# Base URL of the FastAPI app the report's auto-save JS POSTs to. The app
# serves the report HTML (via /artifacts) and the API from the SAME origin, so
# this should be RELATIVE ("" -> "/api/...") by default. A non-empty default
# (e.g. http://localhost:8000) made browser-side drafts calls target the report
# viewer's own machine, hanging the load (KNOW-2342). Only the legacy serve.py
# workflow (report on a separate static server) needs an absolute base — set
# APP_BASE_URL explicitly there.
APP_BASE_URL: str = os.getenv("APP_BASE_URL", "")

# Skilljar API credentials (for Push to Skilljar feature)
SKILLJAR_API_KEY: str = os.getenv("SKILLJAR_API_KEY", "")
SKILLJAR_DOMAIN: str = os.getenv("SKILLJAR_DOMAIN", "")
SKILLJAR_MAPPING_PATH: Path = REPO_ROOT / "data" / "skilljar-mapping.json"

# AWS S3 credentials (for image upload during Release)
AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_S3_BUCKET: str = os.getenv("AWS_S3_BUCKET", "")
AWS_S3_REGION: str = os.getenv("AWS_S3_REGION", "us-east-1")


# ---------------------------------------------------------------------------
# Directory paths
# ---------------------------------------------------------------------------

DATA_DIR: Path = REPO_ROOT / "data"
ARTIFACTS_DIR: Path = REPO_ROOT / "artifacts"
PROMPTS_DIR: Path = REPO_ROOT / "prompts"


def get_artifacts_dir(override: Path | None = None) -> Path:
    """Return the artifacts directory, creating it if needed."""
    d = override if override is not None else ARTIFACTS_DIR
    d.mkdir(parents=True, exist_ok=True)
    return d


# ---------------------------------------------------------------------------
# Well-known file paths
# ---------------------------------------------------------------------------

UPDATE_JOB_PATH: Path = DATA_DIR / "update-job.json"
JIRA_CSV_PATH: Path = DATA_DIR / "jira_export.csv"
PRODUCT_MAPPING_PATH: Path = DATA_DIR / "product-mapping.json"
ASSESSMENT_PROMPT_PATH: Path = PROMPTS_DIR / "ASSESSMENT.md"
EDIT_SUGGESTIONS_PROMPT_PATH: Path = PROMPTS_DIR / "EDIT_SUGGESTIONS.md"
EDITORIAL_GUIDELINES_PATH: Path = PROMPTS_DIR / "EDITORIAL_GUIDELINES.md"

# Model for Step 6 edit suggestions (separate from assessment model; gpt-4o recommended)
EDIT_SUGGESTIONS_MODEL: str = os.getenv("EDIT_SUGGESTIONS_MODEL", "gpt-4o")

# Model and concurrency for alt text enrichment (issue 53)
ALT_TEXT_MODEL: str = os.getenv("ALT_TEXT_MODEL", "gpt-4o")
ALT_TEXT_MAX_CONCURRENT: int = int(os.getenv("ALT_TEXT_MAX_CONCURRENT", "5"))

# Enable vision-based screenshot verification pass in Step 6 (issue 73)
# Adds one multimodal API call per non-decorative image per lesson — opt-in only
ENABLE_VISION_SCREENSHOT_REVIEW: bool = os.getenv("ENABLE_VISION_SCREENSHOT_REVIEW", "false").lower() == "true"


# ---------------------------------------------------------------------------
# Product mapping
# ---------------------------------------------------------------------------

def load_product_mapping() -> dict[str, list[str]]:
    """Load the learning-path → product list mapping from product-mapping.json."""
    if not PRODUCT_MAPPING_PATH.exists():
        raise FileNotFoundError(
            f"Product mapping file not found: {PRODUCT_MAPPING_PATH}. "
            "It should have been created alongside this pipeline."
        )
    with open(PRODUCT_MAPPING_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Regex patterns
# ---------------------------------------------------------------------------

# Matches top-level FME version folder names like "2025.0", "2021.1"
VERSION_FOLDER_PATTERN: re.Pattern = re.compile(r"^\d{4}\.\d+$")

# Strips a version suffix from a course folder name, e.g. " 2025.0" at the end
COURSE_VERSION_SUFFIX_PATTERN: re.Pattern = re.compile(r"\s+\d{4}[\.\d]*$")

# Matches exercise step h2 headings, e.g. "1) Open Workspace" or "2. Add Reader"
EXERCISE_STEP_PATTERN: re.Pattern = re.compile(r"^(\d+)[).]")

# Flush assessment results to disk every N completions
ASSESSMENT_FLUSH_INTERVAL: int = 25

# Maps Jira project keys to the FME products they cover.
# If a lesson's product list has no intersection with this mapping for a given
# issue's project key, that (lesson, issue) pair is skipped — avoiding e.g.
# FMEFLOW issues being assessed against FME Form-only lessons.
# Project keys NOT listed here are treated as relevant to all products.
# Issue summary prefixes for standalone FME programs not covered in Academy training.
# Issues whose summaries start with any of these prefixes are excluded from the changelog
# before reaching the LLM assessment step.
EXCLUDED_SUMMARY_PREFIXES: list[str] = [
    "Quick Translator:",
    "FME Quick Translator:",
    "Data Inspector:",
    "FME Data Inspector:",
    "Licencing Assistant:",
    "FME Licencing Assistant:",
    "Transformer Designer:",
    "FME Transformer Designer:",
]

PROJECT_KEY_TO_PRODUCTS: dict[str, list[str]] = {
    "FMEFORM": ["fme_form"],
    "FMEFLOW": ["fme_flow"],
    "FMEENGINE": ["fme_form", "fme_flow"],
    "FOUNDATION": ["fme_form", "fme_flow"],
}
