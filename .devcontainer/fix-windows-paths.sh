#!/bin/bash
# Normalizes Windows-style paths in Claude config files to their Linux equivalents.
# Runs on every devcontainer start via postStartCommand.
# The .claude directory is bind-mounted from the Windows host, so JSON files
# written on Windows contain paths like C:\Users\name\.claude\... which break
# Claude Code inside the container.

python3 << 'PYEOF'
import json, os, re, glob

CLAUDE_DIR = "/home/vscode/.claude"

def fix_value(v):
    """Recursively replace Windows .claude paths with the Linux mount point."""
    if isinstance(v, str):
        # Match Windows paths up to and including .claude
        # Handles both backslash (C:\Users\name\.claude) and
        # forward-slash variants (C:/Users/name/.claude)
        fixed = re.sub(
            r'[A-Za-z]:[/\\][^"]*?[/\\]\.claude',
            CLAUDE_DIR,
            v,
            flags=re.IGNORECASE
        )
        if fixed != v:
            # Normalize any trailing backslashes that follow .claude
            fixed = fixed.replace('\\', '/')
        return fixed
    elif isinstance(v, dict):
        return {k: fix_value(val) for k, val in v.items()}
    elif isinstance(v, list):
        return [fix_value(item) for item in v]
    return v

# Scan known config files plus any JSON at the top level of .claude/
targets = set([
    f"{CLAUDE_DIR}/plugins/known_marketplaces.json",
    f"{CLAUDE_DIR}/settings.json",
    "/home/vscode/.claude.json",
] + glob.glob(f"{CLAUDE_DIR}/*.json"))

fixed_count = 0
for filepath in sorted(targets):
    if not os.path.exists(filepath):
        continue
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        fixed_data = fix_value(data)
        if fixed_data != data:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(fixed_data, f, indent=2)
            print(f"  Fixed: {filepath}")
            fixed_count += 1
    except Exception:
        pass  # skip non-JSON or unreadable files

if fixed_count:
    print(f"Normalized Windows paths in {fixed_count} file(s).")
else:
    print("No Windows paths to normalize.")
PYEOF
