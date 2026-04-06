"""
Step 6: Edit Plan Generation.

For each lesson with medium or high update_likelihood assessments, aggregates
all relevant Jira issues and makes a single LLM call to produce specific
text-level edit suggestions.

Writes artifacts/edit-plans-{RUN_ID}.json.
Supports incremental mode: skips lessons already present in the output file.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from openai import AsyncOpenAI
from tqdm.asyncio import tqdm as atqdm

from pipeline import config
from pipeline.utils import changelog_path, edit_plans_path, recommendations_path


# ---------------------------------------------------------------------------
# Structured output JSON schema for OpenAI
# ---------------------------------------------------------------------------

_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "lesson_edit_plan",
        "strict": True,
        "schema": {
            "type": "object",
            "required": ["changes", "screenshot_updates"],
            "additionalProperties": False,
            "properties": {
                "changes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": [
                            "change_id",
                            "type",
                            "heading",
                            "original_text",
                            "suggested_text",
                            "explanation",
                            "issue_keys",
                        ],
                        "additionalProperties": False,
                        "properties": {
                            "change_id": {"type": "string"},
                            "type": {
                                "type": "string",
                                "enum": ["change", "add", "delete"],
                            },
                            "heading": {"type": "string"},
                            "original_text": {"type": "string"},
                            "suggested_text": {"type": "string"},
                            "explanation": {"type": "string"},
                            "issue_keys": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
                "screenshot_updates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["src", "explanation", "issue_keys"],
                        "additionalProperties": False,
                        "properties": {
                            "src": {"type": "string"},
                            "explanation": {"type": "string"},
                            "issue_keys": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_edit_suggestions(
    run_id: str,
    recommendations: dict,
    output_dir: Path,
    dry_run: bool = False,
    to_version: str = "",
) -> dict:
    """
    Generate edit plans for all lessons with medium/high assessments.

    Args:
        run_id:          Current run ID.
        recommendations: Recommendations dict from Step 3-4.
        output_dir:      Artifacts directory.
        dry_run:         If True, print counts but make no API calls.
        to_version:      The target FME version from the job config (e.g. "2026.1").
                         Must be provided; the pipeline validates this before calling here.

    Returns:
        The edit plans dict.
    """
    print("\n[Step 6] Generating edit suggestions...")

    if not to_version:
        raise ValueError(
            "to_version is required for edit suggestions. "
            "Ensure update-job.json contains 'to_version'."
        )

    if not config.EDIT_SUGGESTIONS_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Edit suggestions prompt not found: {config.EDIT_SUGGESTIONS_PROMPT_PATH}. "
            "Ensure prompts/EDIT_SUGGESTIONS.md exists."
        )
    template = config.EDIT_SUGGESTIONS_PROMPT_PATH.read_text(encoding="utf-8")

    assessments = recommendations.get("assessments", [])

    # Filter to medium+high only
    relevant = [
        a for a in assessments
        if a.get("update_likelihood") in ("medium", "high")
    ]

    # Group by lesson_id
    lessons: dict[str, list[dict]] = {}
    for a in relevant:
        lid = a["lesson_id"]
        lessons.setdefault(lid, []).append(a)

    total_lessons = len(lessons)
    total_issues = len(relevant)

    print(f"  Medium/high assessments: {total_issues}")
    print(f"  Unique lessons to process: {total_lessons}")

    # Estimate cost (gpt-4o defaults for Step 6)
    approx_input = total_lessons * 13_000
    approx_output = total_lessons * 800
    mini_cost = (approx_input / 1_000_000 * 0.15) + (approx_output / 1_000_000 * 0.60)
    gpt4o_cost = (approx_input / 1_000_000 * 2.50) + (approx_output / 1_000_000 * 10.0)
    print(f"  Estimated cost: ~${mini_cost:.2f} (gpt-4o-mini) / ~${gpt4o_cost:.2f} (gpt-4o)")
    print(f"  Model: {config.EDIT_SUGGESTIONS_MODEL}")

    if dry_run:
        print("  [dry-run] Skipping API calls.")
        return {
            "run_id": run_id,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "model": config.EDIT_SUGGESTIONS_MODEL,
            "total_lessons": total_lessons,
            "completed_lessons": 0,
            "lessons": [],
        }

    # Load Jira issue descriptions from the changelog for richer prompt context
    issue_descriptions: dict[str, str] = {}
    cl_path = changelog_path(run_id, output_dir)
    if cl_path.exists():
        try:
            with open(cl_path, encoding="utf-8") as f:
                cl_data = json.load(f)
            for issue in cl_data.get("issues", []):
                key = issue.get("issue_key") or issue.get("key", "")
                desc = (issue.get("description") or "").strip()
                if key and desc:
                    issue_descriptions[key] = desc
            print(f"  Loaded descriptions for {len(issue_descriptions)} Jira issues.")
        except Exception as e:
            print(f"  WARNING: could not load changelog for descriptions: {e}")

    out_path = edit_plans_path(run_id, output_dir)
    existing_plans, skip_set = _load_existing(out_path)

    skipped = len(skip_set)
    lessons_to_run = {
        lid: group
        for lid, group in lessons.items()
        if lid not in skip_set
    }

    if skipped:
        print(f"  Resuming: {skipped} lessons already processed, {len(lessons_to_run)} remaining.")

    new_plans = asyncio.run(
        _plan_all(lessons_to_run, template, out_path, existing_plans, issue_descriptions, to_version)
    )

    all_plans = existing_plans + new_plans

    result = {
        "run_id": run_id,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "model": config.EDIT_SUGGESTIONS_MODEL,
        "total_lessons": total_lessons,
        "completed_lessons": len(all_plans),
        "lessons": all_plans,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"  Edit plans written: {out_path.name}")
    return result


# ---------------------------------------------------------------------------
# Async loop
# ---------------------------------------------------------------------------

async def _plan_all(
    lessons: dict[str, list[dict]],
    template: str,
    out_path: Path,
    existing: list[dict],
    issue_descriptions: dict[str, str],
    to_version: str = "",
) -> list[dict]:
    if not lessons:
        return []

    client = AsyncOpenAI(api_key=config.get_openai_api_key())
    semaphore = asyncio.Semaphore(config.OPENAI_MAX_CONCURRENT)
    results: list[dict] = []
    flush_buffer: list[dict] = list(existing)

    async def plan_one(lesson_id: str, group: list[dict]) -> dict | None:
        async with semaphore:
            prompt = _build_prompt(lesson_id, group, template, issue_descriptions, to_version)
            if prompt is None:
                return None
            return await _call_openai(client, lesson_id, group, prompt)

    tasks = [plan_one(lid, group) for lid, group in lessons.items()]

    with atqdm(total=len(tasks), desc="Generating edit plans", unit="lesson") as pbar:
        for coro in asyncio.as_completed(tasks):
            result = await coro
            pbar.update(1)
            if result is not None:
                results.append(result)
                flush_buffer.append(result)
                if len(results) % config.ASSESSMENT_FLUSH_INTERVAL == 0:
                    _flush_partial(out_path, flush_buffer)

    _flush_partial(out_path, flush_buffer)
    return results


async def _call_openai(
    client: AsyncOpenAI,
    lesson_id: str,
    group: list[dict],
    prompt: str,
) -> dict | None:
    max_retries = 3
    first = group[0]

    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=config.EDIT_SUGGESTIONS_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format=_RESPONSE_SCHEMA,
                temperature=0.1,
            )
            raw = response.choices[0].message.content
            parsed = json.loads(raw)

            # Post-processing: filter out 'add' changes whose suggested_text
            # is already present in the lesson HTML (issue 33)
            lesson_html = first.get("_lesson_html", "")
            lesson_html_lower = lesson_html.lower()
            filtered_changes = []
            for change in parsed.get("changes", []):
                if change.get("type") == "add":
                    sugg = (change.get("suggested_text") or "").strip()
                    if sugg and sugg.lower() in lesson_html_lower:
                        print(f"\n  [filter] Skipping already-present 'add' in {lesson_id}: {sugg[:60]!r}")
                        continue
                filtered_changes.append(change)

            # Post-processing: propagate rename pairs to all occurrences (issues 51/56)
            filtered_changes = _propagate_renames(filtered_changes, lesson_html, lesson_id)

            # Post-processing: ensure FROM_VERSION → TO_VERSION changes exist (issue 56)
            from_version = first.get("version", "")
            to_version = first.get("_to_version", "")
            filtered_changes = _ensure_version_changes(
                filtered_changes, lesson_html, lesson_id, from_version, to_version
            )

            # Post-processing: filter safe_note.png from screenshot updates (issue 57)
            screenshot_updates = [
                su for su in parsed.get("screenshot_updates", [])
                if "safe_note.png" not in (su.get("src") or "")
            ]

            # Assign stable change_ids based on lesson+index
            for i, change in enumerate(filtered_changes):
                change["change_id"] = hashlib.md5(
                    f"{lesson_id}:change:{i}".encode()
                ).hexdigest()[:8]

            return {
                "lesson_id": lesson_id,
                "lesson_dir": first.get("lesson_dir", ""),
                "lesson_name": first.get("lesson_name", ""),
                "course_canonical": first.get("course_canonical", ""),
                "learning_path": first.get("learning_path", ""),
                "version": first.get("version", ""),
                "product": first.get("product", []),
                "issues_addressed": [a["issue_key"] for a in group],
                "lesson_html": first.get("_lesson_html", ""),
                "changes": filtered_changes,
                "screenshot_updates": screenshot_updates,
                "generated_at": datetime.now(tz=timezone.utc).isoformat(),
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
            }

        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                print(f"\n  ERROR generating edit plan for {lesson_id}: {e}")
                return None

    return None


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

_MAX_DESCRIPTION_CHARS = 1200


def _build_prompt(
    lesson_id: str,
    group: list[dict],
    template: str,
    issue_descriptions: dict[str, str] | None = None,
    to_version: str = "",
) -> str | None:
    """Build the EDIT_SUGGESTIONS prompt for a lesson group."""
    first = group[0]

    # Load lesson HTML from disk
    lesson_dir = first.get("lesson_dir", "")
    if not lesson_dir:
        print(f"  WARNING: no lesson_dir for {lesson_id}, skipping.")
        return None

    html_path = config.REPO_ROOT / lesson_dir / "index.html"
    if not html_path.exists():
        print(f"  WARNING: lesson HTML not found at {html_path}, skipping.")
        return None

    lesson_html = html_path.read_text(encoding="utf-8")

    # Store on the first assessment so _call_openai can access them
    first["_lesson_html"] = lesson_html
    first["_to_version"] = to_version

    # Build issues list
    issue_descriptions = issue_descriptions or {}
    issues_parts = []
    for a in group:
        key = a["issue_key"]
        desc = issue_descriptions.get(key, "")
        if len(desc) > _MAX_DESCRIPTION_CHARS:
            desc = desc[:_MAX_DESCRIPTION_CHARS] + "…"
        desc_block = f"\n- **Jira Description**: {desc}" if desc else ""
        issues_parts.append(
            f"### {key}: {a.get('issue_summary', '')}\n"
            f"- **Update likelihood**: {a.get('update_likelihood', '')}\n"
            f"- **Assessment**: {a.get('justification', '')}"
            f"{desc_block}"
        )
    issues_list = "\n\n".join(issues_parts)

    # Truncate HTML if very large (keep first 30,000 chars to stay within context)
    if len(lesson_html) > 30_000:
        lesson_html = lesson_html[:30_000] + "\n<!-- [truncated] -->"

    editorial_guidelines = ""
    if config.EDITORIAL_GUIDELINES_PATH.exists():
        editorial_guidelines = config.EDITORIAL_GUIDELINES_PATH.read_text(encoding="utf-8")

    substitutions = {
        "LESSON_NAME": first.get("lesson_name", ""),
        "COURSE_CANONICAL": first.get("course_canonical", ""),
        "LEARNING_PATH": first.get("learning_path", ""),
        "FROM_VERSION": first.get("version", ""),
        "TO_VERSION": first["_to_version"],
        "LESSON_HTML": lesson_html,
        "ISSUES_LIST": issues_list,
        "EDITORIAL_GUIDELINES": editorial_guidelines,
        "SECTION_CLASSIFICATION": _build_section_classification(lesson_html),
    }

    prompt = template
    for key, value in substitutions.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)
    return prompt


def _build_section_classification(lesson_html: str) -> str:
    """
    Parse lesson HTML headings and classify each as conceptual or instructional.

    Instructional: numbered exercise-step headings (e.g. "1) Start Workbench")
                   and the Resources heading.
    Conceptual:    all other headings.
    """

    class _HeadingParser(HTMLParser):
        def __init__(self) -> None:
            super().__init__()
            self.headings: list[str] = []
            self._tag: str | None = None
            self._buf: list[str] = []

        def handle_starttag(self, tag: str, attrs: list) -> None:
            if tag in ("h2", "h3"):
                self._tag = tag
                self._buf = []

        def handle_endtag(self, tag: str) -> None:
            if tag == self._tag and tag in ("h2", "h3"):
                self.headings.append("".join(self._buf).strip())
                self._tag = None

        def handle_data(self, data: str) -> None:
            if self._tag:
                self._buf.append(data)

        def handle_entityref(self, name: str) -> None:
            if self._tag:
                import html as _html
                self._buf.append(_html.unescape(f"&{name};"))

        def handle_charref(self, name: str) -> None:
            if self._tag:
                import html as _html
                self._buf.append(_html.unescape(f"&#{name};"))

    parser = _HeadingParser()
    parser.feed(lesson_html)

    if not parser.headings:
        return ""

    conceptual: list[str] = []
    instructional: list[str] = []

    for heading in parser.headings:
        if (
            config.EXERCISE_STEP_PATTERN.match(heading)
            or heading.strip().lower() == "resources"
        ):
            instructional.append(heading)
        else:
            conceptual.append(heading)

    if not instructional:
        return (
            "This lesson has **no exercise steps**. It may explain general concepts, "
            "FME UI features, or both — read the section bodies to judge. "
            "Before suggesting any change to any section, verify that the specific "
            "transformer, dialog, parameter, or UI element named in the Jira issue "
            "is explicitly mentioned in that section's text. "
            "Do not suggest changes based on section topic alone."
        )

    parts: list[str] = []
    parts.append(
        "**Exercise steps** (clearly instructional — update if the specific changed "
        "item is relevant):\n"
        + "\n".join(f"- {h}" for h in instructional)
    )
    parts.append(
        "**Non-exercise sections** (may be conceptual or UI-focused — read the "
        "section body before suggesting changes. Only suggest a change if the "
        "specific transformer, dialog, parameter, or UI element named in the Jira "
        "issue is explicitly present in that section's text):\n"
        + "\n".join(f"- {h}" for h in conceptual)
    )

    return "\n\n".join(parts)



# ---------------------------------------------------------------------------
# Rename propagation post-processing (issue 56/fix-1)
# ---------------------------------------------------------------------------

def _extract_rename_pair(plain_orig: str, plain_sugg: str) -> tuple[str, str]:
    """
    Find the single diverging substring between two similar strings.
    Returns (old_term, new_term), or ("", "") if no clean pair is found.
    """
    # Common prefix
    prefix_len = 0
    for i in range(min(len(plain_orig), len(plain_sugg))):
        if plain_orig[i] == plain_sugg[i]:
            prefix_len += 1
        else:
            break

    # Common suffix (must not overlap the prefix)
    suffix_len = 0
    max_suffix = min(len(plain_orig), len(plain_sugg)) - prefix_len
    for i in range(1, max_suffix + 1):
        if plain_orig[-i] == plain_sugg[-i]:
            suffix_len += 1
        else:
            break

    old_term = plain_orig[prefix_len: len(plain_orig) - suffix_len if suffix_len else len(plain_orig)].strip()
    new_term = plain_sugg[prefix_len: len(plain_sugg) - suffix_len if suffix_len else len(plain_sugg)].strip()
    return old_term, new_term


def _propagate_renames(
    changes: list[dict],
    lesson_html: str,
    lesson_id: str,
) -> list[dict]:
    """
    For each 'change' edit, search the lesson HTML for additional occurrences
    of the same original_text not already covered by an existing change.
    Auto-generates changes for any missed occurrences.
    """
    import re

    seen_pairs: set[tuple[str, str]] = set()
    new_changes: list[dict] = []

    for change in changes:
        if change.get("type") != "change":
            continue

        orig = change.get("original_text", "")
        sugg = change.get("suggested_text", "")
        if not orig or not sugg:
            continue

        # Strip HTML tags to get the plain search term
        plain_orig = re.sub(r"<[^>]+>", "", orig).strip()
        plain_sugg = sugg.strip()
        if not plain_orig or plain_orig == plain_sugg:
            continue

        # Skip sentences — long text is unique by nature and won't repeat
        if len(plain_orig) > 80:
            continue

        # Only process each (orig, sugg) pair once even if multiple LLM changes
        # encode the same rename
        if (plain_orig, plain_sugg) in seen_pairs:
            continue
        seen_pairs.add((plain_orig, plain_sugg))

        # Find all occurrences of plain_orig in lesson HTML (not inside tag attributes)
        all_positions: list[int] = []
        for m in re.finditer(re.escape(plain_orig), lesson_html):
            pre = lesson_html[:m.start()]
            if pre.rfind("<") > pre.rfind(">"):
                continue  # inside a tag attribute
            all_positions.append(m.start())

        if not all_positions:
            continue

        # Determine which positions are already covered by existing changes.
        # Each covering change removes at most one uncovered occurrence from the list
        # (matching report.html's sequential string.replace behaviour).
        uncovered = list(all_positions)
        for c in changes:
            c_orig = c.get("original_text", "")
            c_sugg = c.get("suggested_text", "")
            if plain_orig not in c_orig or plain_sugg not in c_sugg:
                continue
            m = re.search(re.escape(c_orig), lesson_html)
            if not m:
                continue
            # Remove the earliest uncovered position within this change's span
            for i, pos in enumerate(uncovered):
                if m.start() <= pos < m.end():
                    uncovered.pop(i)
                    break

        for pos in uncovered:
            new_change_id = hashlib.md5(
                f"{lesson_id}:rename:{plain_orig}:{pos}".encode()
            ).hexdigest()[:8]

            new_changes.append({
                "change_id": new_change_id,
                "type": "change",
                "heading": change.get("heading", ""),
                "original_text": plain_orig,
                "suggested_text": plain_sugg,
                "explanation": (
                    f"Additional occurrence of \"{plain_orig}\" → \"{plain_sugg}\" "
                    f"(auto-detected; same rename as change {change['change_id']}). "
                    f"{change.get('explanation', '')}"
                ),
                "issue_keys": change.get("issue_keys", []),
            })

    if new_changes:
        print(f"\n  [rename-propagation] Auto-added {len(new_changes)} change(s) for {lesson_id}")

    return changes + new_changes


# ---------------------------------------------------------------------------
# Version string post-processing (issue 56)
# ---------------------------------------------------------------------------

def _ensure_version_changes(
    changes: list[dict],
    lesson_html: str,
    lesson_id: str,
    from_version: str,
    to_version: str,
) -> list[dict]:
    """
    Scan lesson HTML for any occurrence of from_version in text content that is
    not already covered by an existing change, and auto-generate a change for it.
    """
    import re

    if not from_version or not to_version or from_version == to_version:
        return changes

    new_changes: list[dict] = []

    # Find positions of from_version in text content (not tag attributes)
    all_positions: list[int] = []
    for m in re.finditer(re.escape(from_version), lesson_html):
        pre = lesson_html[:m.start()]
        if pre.rfind("<") > pre.rfind(">"):
            continue  # inside a tag attribute
        all_positions.append(m.start())

    if not all_positions:
        return changes

    # Determine which positions are already covered by existing changes
    # (same sequential-replace logic as _propagate_renames)
    uncovered = list(all_positions)
    for c in changes:
        c_orig = c.get("original_text", "")
        c_sugg = c.get("suggested_text", "")
        if from_version not in c_orig or to_version not in c_sugg:
            continue
        m = re.search(re.escape(c_orig), lesson_html)
        if not m:
            continue
        for i, pos in enumerate(uncovered):
            if m.start() <= pos < m.end():
                uncovered.pop(i)
                break

    for pos in uncovered:
        new_change_id = hashlib.md5(
            f"{lesson_id}:version:{from_version}:{pos}".encode()
        ).hexdigest()[:8]
        new_changes.append({
            "change_id": new_change_id,
            "type": "change",
            "heading": "",
            "original_text": from_version,
            "suggested_text": to_version,
            "explanation": (
                f"Version string \"{from_version}\" should be updated to \"{to_version}\" "
                f"(auto-detected; not covered by any LLM-generated change)."
            ),
            "issue_keys": [],
        })

    if new_changes:
        print(f"\n  [version-strings] Auto-added {len(new_changes)} change(s) for {lesson_id}")

    return changes + new_changes


# ---------------------------------------------------------------------------
# Incremental helpers
# ---------------------------------------------------------------------------

def _load_existing(out_path: Path) -> tuple[list[dict], set[str]]:
    if not out_path.exists():
        return [], set()
    try:
        with open(out_path, encoding="utf-8") as f:
            data = json.load(f)
        plans = data.get("lessons", [])
        skip_set = {p["lesson_id"] for p in plans}
        return plans, skip_set
    except Exception:
        return [], set()


def _flush_partial(out_path: Path, plans: list[dict]) -> None:
    partial = {
        "run_id": "partial",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "model": config.EDIT_SUGGESTIONS_MODEL,
        "total_lessons": len(plans),
        "completed_lessons": len(plans),
        "lessons": plans,
    }
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(partial, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
