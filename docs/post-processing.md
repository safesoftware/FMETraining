# Post-Processing Filters in `edit_suggestions.py`

## Why post-processing exists

The edit-suggestions step (`pipeline/edit_suggestions.py`) calls an LLM to generate proposed changes. The LLM's output is then passed through a chain of deterministic post-processing filters before being written to the edit-plans artifact. These filters correct known failure modes that are cheaper and more reliably addressed in code than in prompts.

**Policy:** Prefer prompt improvements when the LLM has enough information to make the right decision on its own. Use post-processing only when:
- The failure mode is structural (e.g., LLM cannot know what text is in the HTML without repeating the whole thing)
- The check is trivially deterministic (e.g., substring search)
- The LLM reliably gets it wrong despite correct prompting

All filters log to stdout with a `[filter-NN]` prefix so pipeline runs record what was removed and why.

---

## Filter chain in `_call_openai()` (`pipeline/edit_suggestions.py`)

Filters run in this order after the LLM responds:

| # | Issue | Filter | Removes / Modifies | Method |
|---|-------|--------|--------------------|--------|
| 1 | #33 | Already-present `add` | Removes `type: "add"` changes whose `suggested_text` already exists verbatim in the lesson HTML — prevents duplicating content that is already there. | Inline in `_call_openai()` |
| 2 | #65 | HTML tags in `suggested_text` | Strips all HTML tags from `suggested_text` for `type: "change"` entries — the LLM sometimes wraps replacement text in `<p>` or `<strong>` despite instructions not to. | Inline in `_call_openai()` |
| 3 | #51/#56 | Apply rename pairs | For each rename pair the LLM returned, generates additional `change` entries for every occurrence of the old term in the lesson HTML not already covered by an existing change. | `_apply_rename_pairs()` |
| 4 | #51/#56 | Propagate renames | Detects implicit renames from existing changes (e.g., LLM changed "Visual Preview" → "Data Preview" in one place) and generates changes for all remaining occurrences. | `_propagate_renames()` |
| 5 | #56 | Version string coverage | Scans lesson HTML for any occurrence of `FROM_VERSION` in text content not already covered by an LLM change, and auto-inserts a `change` entry for each. | `_ensure_version_changes()` |
| 6 | #57 | Decorative image exclusion | Removes `screenshot_updates` entries whose `src` contains `safe_note.png` — a decorative callout icon, never a real UI screenshot. | Inline in `_call_openai()` |
| 7 | #74 | Stale `original_text` | Removes `type: "change"` and `type: "delete"` entries whose `original_text` cannot be found in the normalized lesson HTML — prevents unapplyable suggestions from reaching the report. | `_filter_stale_original_text()` |
| 8 | #72 | FMEENGINE conceptual filter | Removes changes where every `issue_key` is FMEENGINE-prefixed AND the `heading` is not an exercise step AND the lesson has no instructional headings at all — catches backend-only changes that leaked through the prompt rule. | `_filter_fmeengine_no_ui()` |

---

## Adding a new filter

1. Implement the filter as a standalone function named `_filter_<short_name>()` returning the modified `changes` list.
2. Add a call in `_call_openai()` after the existing chain, with a comment referencing the issue number.
3. Log filtered items: `print(f"\n  [filter-NN] ...")`.
4. Add a row to the table above with the issue number, description, and method name.
