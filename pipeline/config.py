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

# Locate repo root (parent of the pipeline/ package directory)
REPO_ROOT: Path = Path(__file__).parent.parent.resolve()

# Load .env from repo root
load_dotenv(REPO_ROOT / ".env")


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

_raw_project_keys = os.getenv("JIRA_PROJECT_KEYS", "FOUNDATION,FMEENGINE,FMEFLOW,FMEFORM")
JIRA_PROJECT_KEYS: list[str] = [k.strip() for k in _raw_project_keys.split(",") if k.strip()]


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
