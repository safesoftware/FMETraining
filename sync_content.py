#!/usr/bin/env python3
"""
sync_content.py - Sync versioned lesson content from the FMETraining repo.

For each versioned directory (matching 20XX.X) in FMETraining/main:
  - Replaces local copy entirely, including handling deleted files
For any versioned directory that exists locally but was removed from FMETraining:
  - Removes it locally

Does NOT touch README.md or any other non-versioned files.

Usage:
    python sync_content.py
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

REMOTE_NAME = "fmetraining"
REMOTE_URL = "https://github.com/safesoftware/FMETraining"
REMOTE_BRANCH = "main"
VERSION_PATTERN = re.compile(r"^20\d{2}\.\d+$")
REPO_ROOT = Path(__file__).parent


def run(cmd: list[str]) -> str:
    """Run a git command, print it, exit on failure, return stdout."""
    print(f"  $ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  ERROR: {result.stderr.strip() or result.stdout.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def run_quiet(cmd: list[str]) -> int:
    """Run a git command silently, return exit code (no exit on failure)."""
    return subprocess.run(cmd, cwd=REPO_ROOT, capture_output=True).returncode


def main() -> None:
    print("=== FMETraining Content Sync ===\n")

    # 1. Ensure remote exists with correct URL
    existing_remotes = run(["git", "remote"]).splitlines()
    if REMOTE_NAME in existing_remotes:
        current_url = run(["git", "remote", "get-url", REMOTE_NAME])
        if current_url != REMOTE_URL:
            print(f"Updating remote URL for '{REMOTE_NAME}'...")
            run(["git", "remote", "set-url", REMOTE_NAME, REMOTE_URL])
        else:
            print(f"Remote '{REMOTE_NAME}' already configured.")
    else:
        print(f"Adding remote '{REMOTE_NAME}' -> {REMOTE_URL}")
        run(["git", "remote", "add", REMOTE_NAME, REMOTE_URL])

    # 2. Fetch
    print(f"\nFetching {REMOTE_NAME}/{REMOTE_BRANCH} (this may take a moment)...")
    run(["git", "fetch", REMOTE_NAME, REMOTE_BRANCH])

    # 3. Discover versioned dirs in FMETraining
    remote_tree = run(["git", "ls-tree", "--name-only", f"{REMOTE_NAME}/{REMOTE_BRANCH}"])
    remote_dirs = sorted(d for d in remote_tree.splitlines() if VERSION_PATTERN.match(d))

    # 4. Discover versioned dirs locally
    local_dirs = sorted(
        d.name for d in REPO_ROOT.iterdir()
        if d.is_dir() and VERSION_PATTERN.match(d.name)
    )

    print(f"\nFMETraining has: {remote_dirs}")
    print(f"Local has:       {local_dirs}")

    # 5. Remove dirs that exist locally but not in FMETraining
    for d in local_dirs:
        if d not in remote_dirs:
            print(f"\nRemoving '{d}/' (not in FMETraining)...")
            shutil.rmtree(REPO_ROOT / d)
            run_quiet(["git", "rm", "-r", "--cached", "-q", d])

    # 6. For each remote versioned dir: nuke local copy and re-checkout from FMETraining.
    #    Nuking first ensures deleted files in FMETraining are removed locally too.
    print(f"\nSyncing {len(remote_dirs)} versioned directories from {REMOTE_NAME}/{REMOTE_BRANCH}...")
    for d in remote_dirs:
        local_path = REPO_ROOT / d
        if local_path.exists():
            print(f"  Replacing {d}/")
            shutil.rmtree(local_path)
        else:
            print(f"  Adding {d}/ (new)")
        # Remove from index (ignore errors if not tracked)
        run_quiet(["git", "rm", "-r", "--cached", "-q", d])
        # Restore entirely from FMETraining
        run(["git", "checkout", f"{REMOTE_NAME}/{REMOTE_BRANCH}", "--", d])

    print("\n=== Sync complete ===")
    print("Review changes with: git diff --stat HEAD")
    print("Then commit with:    git add . && git commit -m 'Sync lesson content from FMETraining'")


if __name__ == "__main__":
    main()
