"""
Step 2: Build the Change Log.

Reads data/jira_export.csv, filters to FME-relevant project keys and to issues
that affect versions within the update window, and writes
artifacts/changelog-{RUN_ID}.json.
"""

from __future__ import annotations

import csv as csv_module
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from tqdm import tqdm

from pipeline import config
from pipeline.utils import (
    changelog_path,
    parse_version,
    version_in_range,
)

# Regex for pandas-renamed duplicate column detection
_AV_PATTERN = re.compile(r"^Affects versions(\.\d+)?$")
_FV_PATTERN = re.compile(r"^Fix versions(\.\d+)?$")


def build_changelog(
    run_id: str,
    manifest: dict,
    output_dir: Path,
    dry_run: bool = False,
) -> dict:
    """
    Filter the Jira CSV to issues relevant to the update window derived from
    the manifest and write artifacts/changelog-{RUN_ID}.json.

    Args:
        run_id:     Current run ID.
        manifest:   The manifest dict from Step 1.
        output_dir: Artifacts directory.
        dry_run:    If True, compute counts but don't write output.

    Returns:
        The changelog dict.
    """
    print("\n[Step 2] Building change log from Jira CSV...")

    job = manifest.get("job", {})
    to_version_str = str(job.get("to_version", ""))
    to_version = parse_version(to_version_str)
    if to_version is None:
        raise ValueError(f"Cannot parse to_version from job: {to_version_str!r}")

    # Determine version range from manifest lessons
    lesson_versions = [
        parse_version(lesson["version"])
        for lesson in manifest.get("lessons", [])
        if parse_version(lesson.get("version", "")) is not None
    ]
    if not lesson_versions:
        raise ValueError("Manifest contains no lessons with parseable versions. Run Step 1 first.")

    from_min = min(lesson_versions)

    print(f"  Version range: ({from_min}, {to_version}]")
    print(f"  Project keys: {config.JIRA_PROJECT_KEYS}")

    csv_path = config.JIRA_CSV_PATH
    if not csv_path.exists():
        raise FileNotFoundError(f"Jira CSV not found: {csv_path}")

    issues = _load_and_filter_csv(csv_path, from_min, to_version)

    print(f"  Found {len(issues)} relevant issues.")

    changelog = {
        "run_id": run_id,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "filter_config": {
            "project_keys": config.JIRA_PROJECT_KEYS,
            "version_range": {
                "from_min": from_min,
                "to": to_version,
            },
        },
        "issues": issues,
    }

    if dry_run:
        print("  [dry-run] Skipping changelog write.")
        return changelog

    out_path = changelog_path(run_id, output_dir)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(changelog, f, indent=2, ensure_ascii=False)

    print(f"  Changelog written: {out_path.name}")
    return changelog


# ---------------------------------------------------------------------------
# CSV loading
# ---------------------------------------------------------------------------

def _load_and_filter_csv(
    csv_path: Path,
    from_min: float,
    to_version: float,
) -> list[dict]:
    """
    Load the Jira CSV in chunks and filter to relevant issues.

    Returns a list of issue dicts (deduplicated by issue_key).
    """
    project_keys_set = set(config.JIRA_PROJECT_KEYS)

    # First pass: detect column positions from the raw header row.
    # We read the first row with a minimal reader to avoid pandas renaming duplicates.
    col_positions = _detect_column_positions(csv_path)

    # Build the usecols list (integers) for pandas
    usecols = sorted(set(
        col_positions["summary"]
        + col_positions["issue_key"]
        + col_positions["issue_id"]
        + col_positions["issue_type"]
        + col_positions["status"]
        + col_positions["project_key"]
        + col_positions["description"]
        + col_positions["affects_versions"]
        + col_positions["fix_versions"]
    ))

    seen_keys: set[str] = set()
    results: list[dict] = []

    # Count total rows for the progress bar (approximate)
    # We estimate from file size to avoid a full pre-scan
    total_rows_estimate = _estimate_row_count(csv_path)
    chunk_size = 5000

    with tqdm(
        total=total_rows_estimate,
        desc="Scanning Jira CSV",
        unit="row",
        unit_scale=True,
    ) as pbar:
        reader = pd.read_csv(
            csv_path,
            engine="python",
            header=0,
            usecols=usecols,
            chunksize=chunk_size,
            dtype=str,
            keep_default_na=False,
            on_bad_lines="warn",
        )

        for chunk in reader:
            pbar.update(len(chunk))

            # Rename columns to logical names for consistent access
            chunk = _rename_chunk_columns(chunk, col_positions)

            # Filter by project key
            mask = chunk["project_key"].isin(project_keys_set)
            chunk = chunk[mask]
            if chunk.empty:
                continue

            for _, row in chunk.iterrows():
                issue_key = str(row.get("issue_key", "")).strip()
                if not issue_key or issue_key in seen_keys:
                    continue

                # Skip Bug issue types — they rarely impact training content
                issue_type = str(row.get("issue_type", "")).strip()
                if issue_type.lower() == "bug":
                    continue

                # Skip issues for standalone programs not used in Academy training
                summary = str(row.get("summary", "")).strip()
                if any(summary.startswith(p) for p in config.EXCLUDED_SUMMARY_PREFIXES):
                    continue

                # Collect all affects_versions values (non-empty)
                affects_raw = [
                    str(row.get(f"affects_versions_{i}", "")).strip()
                    for i in range(len(col_positions["affects_versions"]))
                ]
                affects_raw = [v for v in affects_raw if v]

                # Collect all fix_versions values (non-empty)
                fix_raw = [
                    str(row.get(f"fix_versions_{i}", "")).strip()
                    for i in range(len(col_positions["fix_versions"]))
                ]
                fix_raw = [v for v in fix_raw if v]

                # Parse affects and fix versions to floats
                affects_parsed = [v for v in (parse_version(v) for v in affects_raw) if v is not None]
                fix_parsed = [v for v in (parse_version(v) for v in fix_raw) if v is not None]

                # Include if any affects_version is in range.
                # Fall back to fix_versions when affects_versions is empty (common for Epics
                # and feature issues that only have Fix version set, not Affects version).
                affects_in_range = any(version_in_range(v, from_min, to_version) for v in affects_parsed)
                fix_in_range = (not affects_raw) and any(version_in_range(v, from_min, to_version) for v in fix_parsed)

                if not affects_in_range and not fix_in_range:
                    continue

                seen_keys.add(issue_key)

                issue = {
                    "issue_key": issue_key,
                    "issue_id": str(row.get("issue_id", "")).strip(),
                    "summary": str(row.get("summary", "")).strip(),
                    "issue_type": str(row.get("issue_type", "")).strip(),
                    "status": str(row.get("status", "")).strip(),
                    "project_key": str(row.get("project_key", "")).strip(),
                    "description": str(row.get("description", "")).strip() or None,
                    "affects_versions": affects_raw,
                    "fix_versions": fix_raw,
                    "affects_versions_parsed": affects_parsed,
                }
                results.append(issue)

    return results


def _detect_column_positions(csv_path: Path) -> dict[str, list[int]]:
    """
    Read just the header row of the CSV to find column positions.

    pandas renames duplicate headers to 'Name', 'Name.1', 'Name.2' etc.
    We read the raw first line to get original names, then build a mapping
    from logical field names to lists of column indices.
    """
    # Read only the header row using Python's csv module to avoid any pandas
    # renaming or multiline complications
    import csv as csv_module
    with open(csv_path, encoding="utf-8", errors="replace", newline="") as f:
        reader = csv_module.reader(f)
        raw_headers = next(reader)

    positions: dict[str, list[int]] = {
        "summary": [],
        "issue_key": [],
        "issue_id": [],
        "issue_type": [],
        "status": [],
        "project_key": [],
        "description": [],
        "affects_versions": [],
        "fix_versions": [],
    }

    for idx, col in enumerate(raw_headers):
        col_lower = col.strip().lower()
        if col_lower == "summary":
            positions["summary"].append(idx)
        elif col_lower == "issue key":
            positions["issue_key"].append(idx)
        elif col_lower == "issue id":
            positions["issue_id"].append(idx)
        elif col_lower == "issue type":
            positions["issue_type"].append(idx)
        elif col_lower == "status":
            positions["status"].append(idx)
        elif col_lower == "project key":
            positions["project_key"].append(idx)
        elif col_lower == "description":
            positions["description"].append(idx)
        elif col_lower == "affects versions":
            positions["affects_versions"].append(idx)
        elif col_lower == "fix versions":
            positions["fix_versions"].append(idx)

    # Keep only the first occurrence of singleton fields
    for key in ["summary", "issue_key", "issue_id", "issue_type", "status", "project_key", "description"]:
        if positions[key]:
            positions[key] = [positions[key][0]]

    return positions


def _rename_chunk_columns(chunk: pd.DataFrame, col_positions: dict[str, list[int]]) -> pd.DataFrame:
    """
    Rename chunk columns to logical names for consistent access.

    pandas auto-suffixes duplicate column names from the CSV:
      "Affects versions" → "Affects versions", "Affects versions.1", ...
      "Fix versions"     → "Fix versions", "Fix versions.1", ...

    We rename:
      - Singleton fields to their logical name (e.g. "Summary" → "summary")
      - Duplicate fields to indexed names (e.g. "Affects versions.2" → "affects_versions_2")
    """
    singleton_map = {
        "Summary": "summary",
        "Issue key": "issue_key",
        "Issue id": "issue_id",
        "Issue Type": "issue_type",
        "Status": "status",
        "Project key": "project_key",
        "Description": "description",
    }

    col_name_to_logical: dict[str, str] = {}
    av_count = 0
    fv_count = 0

    for col in chunk.columns:
        col_str = str(col)
        if col_str in singleton_map:
            col_name_to_logical[col_str] = singleton_map[col_str]
        elif _AV_PATTERN.match(col_str):
            col_name_to_logical[col_str] = f"affects_versions_{av_count}"
            av_count += 1
        elif _FV_PATTERN.match(col_str):
            col_name_to_logical[col_str] = f"fix_versions_{fv_count}"
            fv_count += 1

    return chunk.rename(columns=col_name_to_logical)


def _estimate_row_count(csv_path: Path) -> int:
    """Estimate total row count from file size (used only for tqdm total)."""
    try:
        size = csv_path.stat().st_size
        # Rough estimate: average row ~300 bytes
        return max(1, size // 300)
    except Exception:
        return 250000
