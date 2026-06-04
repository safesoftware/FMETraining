---
name: syncing-branches-with-main
description: Use when a change updates shared project state (deployment/architecture plans, runbooks, conventions, CLAUDE.md) from a feature or issue branch, when deciding whether work belongs on main vs a branch, or before committing/merging/PRing docs that other branches will need.
allowed-tools: Bash, Read, Grep, Glob
---

# Syncing Branches with Main

## Overview

`main` is the single source of truth for **shared project state**. Feature/issue branches hold feature-specific work. Shared state must reach `main` on its own and flow *outward* to branches — it must never be trapped on one branch or hand-copied between branches.

Core principle: **shared changes go to main and fan out; feature changes stay on the branch until the feature merges.**

## The rule

- **Shared / cross-cutting changes** — deployment & architecture plans, runbooks, conventions, `CLAUDE.md`, anything multiple branches rely on for context — land on `main` first, in a small **docs-only PR**. Low-risk, fast to review, immediately available to every branch.
- **Feature-specific changes** stay on the feature branch and reach main when the feature merges.
- **Branches pull, never hand-copy.** To get shared updates into a branch, `git merge origin/main` (or rebase onto it). Git fans one source out; copying creates divergent forks that drift.
- **Never merge a whole feature branch into main just to ship a shared doc** — that drags in unrelated, unready code. Split the shared part into its own branch cut from `main`.

## Landing shared docs on main

```bash
git fetch origin -q
git checkout -b docs/<topic> origin/main
# bring ONLY the shared files from the branch that has them:
git checkout <feature-branch> -- docs/plans/<file>.md
git commit -m "docs: <summary>"
git push -u origin docs/<topic>
gh pr create --base main --title "docs: <summary>"
```

Then any branch that needs them runs `git merge origin/main`.

## Commit conventions (this repo)

- Prefix feature commits with the Jira key: `KNOW-1234: <summary>`. Use `docs: <summary>` for shared-doc PRs.
- End every commit message with the required `Co-Authored-By:` trailer.
- Commit/push only when the user asks. If you're on `main`, branch first.

## Common mistakes

| Mistake | Fix |
| --- | --- |
| Authoring a plan/runbook on a feature branch and leaving it there | Land it on `main` via a docs-only PR so every branch sees it |
| Copying a doc into each open branch "so Claude has context" | Keep one source on `main`; branches `git merge origin/main` |
| Merging a 50-commit feature branch to deliver one shared doc | Split the doc into a branch cut from `main` |
| Editing a shared doc on a branch that's behind `main` | Pull `main` in first, then edit |
