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
import base64
import hashlib
import html as _html_module
import json
import re
import time
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

from openai import AsyncOpenAI
from tqdm.asyncio import tqdm as atqdm

from pipeline import config
from pipeline.utils import edit_plans_path, recommendations_path


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
            "required": ["rename_pairs", "changes", "screenshot_updates"],
            "additionalProperties": False,
            "properties": {
                "rename_pairs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["old", "new", "issue_keys"],
                        "additionalProperties": False,
                        "properties": {
                            "old": {"type": "string"},
                            "new": {"type": "string"},
                            "issue_keys": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
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
                        "required": ["src", "explanation", "issue_keys", "alt_text"],
                        "additionalProperties": False,
                        "properties": {
                            "src": {"type": "string"},
                            "explanation": {"type": "string"},
                            "issue_keys": {
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "alt_text": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                        },
                    },
                },
            },
        },
    },
}

# Images that are decorative and must never be sent to the vision model
_DECORATIVE_IMAGES = {"safe_note.png", "safe_tip.png", "safe_warning.png"}

# Structured output schema for per-image vision screenshot review (issue 73)
_VISION_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "screenshot_vision_review",
        "strict": True,
        "schema": {
            "type": "object",
            "required": ["needs_update", "relevant_issue_keys", "explanation"],
            "additionalProperties": False,
            "properties": {
                "needs_update": {"type": "boolean"},
                "relevant_issue_keys": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "explanation": {"type": "string"},
            },
        },
    },
}


# ---------------------------------------------------------------------------
# Vision screenshot verification helpers (issue 73)
# ---------------------------------------------------------------------------

def _extract_lesson_images(lesson_html: str) -> list[dict]:
    """Return [{src, alt}] for all non-decorative local images in the lesson HTML."""
    results: list[dict] = []
    seen: set[str] = set()
    for m in re.finditer(r"<img[^>]+>", lesson_html):
        tag = m.group()
        src_m = re.search(r'src=["\']([^"\']+)["\']', tag)
        alt_m = re.search(r'alt=["\']([^"\']*)["\']', tag)
        if not src_m:
            continue
        src = src_m.group(1)
        if not src.startswith("images/"):
            continue
        if Path(src).name in _DECORATIVE_IMAGES:
            continue
        if src in seen:
            continue
        seen.add(src)
        results.append({"src": src, "alt": alt_m.group(1) if alt_m else ""})
    return results


async def _vision_verify_one(
    client: AsyncOpenAI,
    sem: asyncio.Semaphore,
    img_path: Path,
    src: str,
    issues: list[dict],
    existing_updates: list[dict],
) -> dict:
    """Ask the vision model whether a single screenshot is affected by any Jira issue.

    Returns {"src", "needs_update", "relevant_issue_keys", "explanation"}.
    On error returns needs_update=False so the image is not incorrectly promoted.
    """
    async with sem:
        try:
            img_bytes = img_path.read_bytes()
        except OSError as exc:
            print(f"\n  [vision] Cannot read {img_path.name}: {exc}")
            return {"src": src, "needs_update": False, "relevant_issue_keys": [], "explanation": ""}

        img_data = base64.standard_b64encode(img_bytes).decode()
        ext = img_path.suffix.lstrip(".")

        issues_text = "\n".join(
            f"- {i.get('issue_key', '')}: {i.get('issue_summary', '')[:200]}"
            for i in issues
        )
        existing_flag = next((u for u in existing_updates if u.get("src") == src), None)
        flag_note = (
            f"Text analysis already flagged this image: {existing_flag['explanation']}"
            if existing_flag
            else "Text analysis did NOT flag this image."
        )

        prompt_text = (
            "You are reviewing an FME training screenshot to determine if it needs to be retaken "
            "due to recent UI changes.\n\n"
            f"Recent FME UI changes (Jira issues):\n{issues_text}\n\n"
            f"{flag_note}\n\n"
            "Does this screenshot show any UI element that would look visibly different after "
            "these changes? Name the specific UI element if so. Be conservative — only flag "
            "images where the change is clearly visible in this screenshot."
        )

        try:
            response = await client.chat.completions.create(
                model=config.EDIT_SUGGESTIONS_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt_text},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/{ext};base64,{img_data}",
                            "detail": "low",
                        }},
                    ],
                }],
                response_format=_VISION_RESPONSE_SCHEMA,
                temperature=0.1,
                max_tokens=200,
            )
            result = json.loads(response.choices[0].message.content)
            return {
                "src": src,
                "needs_update": result.get("needs_update", False),
                "relevant_issue_keys": result.get("relevant_issue_keys", []),
                "explanation": result.get("explanation", ""),
            }
        except Exception as exc:
            print(f"\n  [vision] API call failed for {img_path.name}: {exc}")
            return {"src": src, "needs_update": False, "relevant_issue_keys": [], "explanation": ""}


async def _vision_verify_screenshots(
    client: AsyncOpenAI,
    lesson_dir: str,
    lesson_html: str,
    screenshot_updates: list[dict],
    group: list[dict],
    lesson_id: str,
) -> list[dict]:
    """Vision-verify screenshot flags for a lesson (issue 73).

    For each non-decorative image found on disk:
    - If vision confirms a text flag → keep it (source stays "text")
    - If vision finds a new flag → add it with source="vision"
    - If vision disputes a text flag → remove it (false positive)
    Text-flagged images that can't be found on disk are kept unchanged.
    """
    images = _extract_lesson_images(lesson_html)
    if not images:
        return screenshot_updates

    lesson_path = config.REPO_ROOT / lesson_dir
    sem = asyncio.Semaphore(config.ALT_TEXT_MAX_CONCURRENT)

    # Separate images we can verify (exist on disk) from those we cannot
    verifiable = [(img, lesson_path / img["src"]) for img in images if (lesson_path / img["src"]).exists()]
    unverifiable_srcs = {img["src"] for img in images if not (lesson_path / img["src"]).exists()}

    if not verifiable:
        return screenshot_updates

    # Run vision check for all verifiable images concurrently
    vision_results = await asyncio.gather(*[
        _vision_verify_one(client, sem, img_path, img["src"], group, screenshot_updates)
        for img, img_path in verifiable
    ])

    text_by_src = {u["src"]: u for u in screenshot_updates}
    merged: list[dict] = []
    confirmed = removed = added = 0

    for vr in vision_results:
        src = vr["src"]
        if vr["needs_update"]:
            if src in text_by_src:
                merged.append(text_by_src[src])  # source="text" already set
                confirmed += 1
            else:
                merged.append({
                    "src": src,
                    "explanation": vr["explanation"],
                    "issue_keys": vr["relevant_issue_keys"],
                    "alt_text": None,
                    "source": "vision",
                })
                added += 1
        elif src in text_by_src:
            removed += 1

    # Preserve text flags for images we couldn't verify
    for su in screenshot_updates:
        if su.get("src") in unverifiable_srcs:
            merged.append(su)

    if confirmed or removed or added:
        print(f"\n  [vision] {lesson_id}: {confirmed} confirmed, {removed} removed, {added} added")

    return merged


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_edit_suggestions(
    run_id: str,
    recommendations: dict,
    output_dir: Path,
    dry_run: bool = False,
    to_version: str = "",
    descriptions: dict[str, str] | None = None,
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
        descriptions:    Optional in-memory mapping of issue_key -> description.
                         Supplied by the orchestrator; descriptions are never
                         persisted to disk. If None or empty, prompts include
                         only the assessment summary/justification.

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

    # Use in-memory descriptions provided by the orchestrator. The on-disk
    # changelog is metadata-only (no descriptions) — see pipeline/jira_api.py.
    issue_descriptions: dict[str, str] = {
        k: v.strip() for k, v in (descriptions or {}).items() if v and v.strip()
    }
    if issue_descriptions:
        print(f"  Using descriptions for {len(issue_descriptions)} Jira issues (in-memory).")

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

            # Post-processing: strip HTML tags from suggested_text for 'change' type (issue 65)
            for ch in filtered_changes:
                if ch.get("type") == "change" and ch.get("suggested_text"):
                    ch["suggested_text"] = re.sub(r"<[^>]+>", "", ch["suggested_text"]).strip()

            # Post-processing: apply explicit rename pairs to every occurrence in the HTML
            filtered_changes = _apply_rename_pairs(
                parsed.get("rename_pairs", []), filtered_changes, lesson_html, lesson_id
            )

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
            # Tag text-based suggestions with their source (issue 73)
            for su in screenshot_updates:
                su["source"] = "text"

            # Optional vision-verification pass: confirm/remove/add screenshot flags (issue 73)
            if config.ENABLE_VISION_SCREENSHOT_REVIEW:
                lesson_dir = first.get("lesson_dir", "")
                if lesson_dir:
                    screenshot_updates = await _vision_verify_screenshots(
                        client, lesson_dir, lesson_html, screenshot_updates, group, lesson_id
                    )

            # Post-processing: remove changes whose original_text is not in lesson HTML (issue 74)
            filtered_changes = _filter_stale_original_text(
                filtered_changes, lesson_html, lesson_id
            )

            # Post-processing: suppress FMEENGINE-only changes in fully conceptual lessons (issue 72)
            filtered_changes = _filter_fmeengine_no_ui(
                filtered_changes, lesson_html, lesson_id
            )

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
                "rename_pairs": parsed.get("rename_pairs", []),
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


def _apply_rename_pairs(
    rename_pairs: list[dict],
    changes: list[dict],
    lesson_html: str,
    lesson_id: str,
) -> list[dict]:
    """
    For each rename pair extracted by the LLM, find every occurrence of the
    old term in the lesson HTML and generate a change entry if not already
    covered by an existing change.
    """
    if not rename_pairs:
        return changes

    new_changes: list[dict] = []
    existing_covered: set[tuple[str, str]] = set()
    for c in changes:
        if c.get("type") == "change":
            existing_covered.add((c.get("original_text", ""), c.get("suggested_text", "")))

    added_count = 0
    for pair in rename_pairs:
        old_term = (pair.get("old") or "").strip()
        new_term = (pair.get("new") or "").strip()
        issue_keys = pair.get("issue_keys", [])
        if not old_term or not new_term or old_term == new_term:
            continue

        for m in re.finditer(re.escape(old_term), lesson_html):
            # Skip occurrences inside tag attributes
            pre = lesson_html[:m.start()]
            if pre.rfind("<") > pre.rfind(">"):
                continue

            # Skip if already covered by an existing change containing this exact term
            already_covered = any(
                old_term in c.get("original_text", "") and new_term in c.get("suggested_text", "")
                for c in changes + new_changes
            )
            if already_covered:
                # Only skip once per pair — allow multiple occurrences through
                # by checking position coverage instead
                pass

            # Check if this position is covered by any existing change's span
            covered = False
            for c in changes + new_changes:
                c_orig = c.get("original_text", "")
                if old_term not in c_orig:
                    continue
                cm = re.search(re.escape(c_orig), lesson_html)
                if cm and cm.start() <= m.start() < cm.end():
                    covered = True
                    break
            if covered:
                continue

            change_id = hashlib.md5(
                f"{lesson_id}:pair:{old_term}:{m.start()}".encode()
            ).hexdigest()[:8]
            new_changes.append({
                "change_id": change_id,
                "type": "change",
                "heading": "",
                "original_text": old_term,
                "suggested_text": new_term,
                "explanation": (
                    f'"{old_term}" renamed to "{new_term}" '
                    f"(auto-generated from rename pair in {', '.join(issue_keys) or 'Jira issue'})."
                ),
                "issue_keys": issue_keys,
            })
            added_count += 1

    if added_count:
        print(f"\n  [rename-pairs] Auto-added {added_count} change(s) for {lesson_id}")

    return changes + new_changes


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

    # Pre-populate seen_pairs with any short-form term already present as a
    # standalone original_text (e.g. added by _apply_rename_pairs). These are
    # already fully expanded — propagation would only create duplicates.
    seen_pairs: set[tuple[str, str]] = set()
    for c in changes:
        if c.get("type") == "change":
            o = re.sub(r"<[^>]+>", "", c.get("original_text", "")).strip()
            s = c.get("suggested_text", "").strip()
            if o and s and len(o) <= 80:
                seen_pairs.add((o, s))

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
        if not plain_orig or plain_orig == plain_sugg or len(plain_orig) < 3:
            continue

        # For sentence-level changes (too long to repeat), try to extract the
        # core rename pair so it can be propagated to headings and other short
        # occurrences (e.g. "Visual Preview" → "Data Preview" from a sentence).
        if len(plain_orig) > 80:
            extracted_orig, extracted_sugg = _extract_rename_pair(plain_orig, plain_sugg)
            if not extracted_orig or not extracted_sugg or extracted_orig == extracted_sugg:
                continue
            if not (3 <= len(extracted_orig) <= 80):
                continue
            plain_orig, plain_sugg = extracted_orig, extracted_sugg

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

def _heading_before(html: str, pos: int) -> str:
    """Return text of the nearest h2/h3 heading before pos in html, or '' if none found."""
    snippet = html[:pos]
    matches = list(re.finditer(r"<h[23][^>]*>([^<]+)</h[23]>", snippet, re.IGNORECASE))
    if matches:
        return matches[-1].group(1).strip()
    return ""


_NEW_FOR_FME_TAIL_RE = re.compile(r"new for fme\s*$", re.IGNORECASE)


def _is_in_new_for_fme_note(html: str, pos: int) -> bool:
    """True if html[pos:] is the version number inside a 'New for FME X.Y' marker.

    "New for FME X.Y" notes are historical markers that record when a feature
    was introduced — they must not be retroactively bumped on every training
    refresh. This walks back from `pos`, strips tags from a short window, and
    checks whether the trailing text reads 'new for fme ' (case-insensitive).
    Tag stripping handles the editorial template's bold/star markup variations,
    e.g. <strong>⭐ New for FME 2025.0:</strong>.
    """
    window_start = max(0, pos - 80)
    window = html[window_start:pos]
    text_before = re.sub(r"<[^>]+>", " ", window)
    text_before = re.sub(r"\s+", " ", text_before).rstrip()
    return _NEW_FOR_FME_TAIL_RE.search(text_before) is not None


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
    Skips occurrences inside "New for FME X.Y" historical markers, and drops any
    LLM-generated single-version-bump change targeting such a marker.
    """
    if not from_version or not to_version or from_version == to_version:
        return changes

    # Defensive: drop any LLM-generated change whose original_text equals
    # from_version and whose match in the lesson HTML sits inside a
    # "New for FME" note. Such a change slips past the position-coverage
    # check below because it looks like a legitimate single-version bump.
    def _targets_new_for_fme_note(c: dict) -> bool:
        if c.get("type") != "change":
            return False
        if c.get("original_text") != from_version or c.get("suggested_text") != to_version:
            return False
        for match in re.finditer(re.escape(from_version), lesson_html):
            pre = lesson_html[:match.start()]
            if pre.rfind("<") > pre.rfind(">"):
                continue
            if _is_in_new_for_fme_note(lesson_html, match.start()):
                return True
        return False

    filtered_existing = [c for c in changes if not _targets_new_for_fme_note(c)]
    dropped = len(changes) - len(filtered_existing)
    if dropped:
        print(
            f"  [version-strings] Dropped {dropped} LLM change(s) targeting "
            f"'New for FME' note(s) for {lesson_id}"
        )

    new_changes: list[dict] = []

    # Find positions of from_version in text content (not tag attributes,
    # and not inside a "New for FME X.Y" historical marker).
    all_positions: list[int] = []
    for m in re.finditer(re.escape(from_version), lesson_html):
        pre = lesson_html[:m.start()]
        if pre.rfind("<") > pre.rfind(">"):
            continue  # inside a tag attribute
        if _is_in_new_for_fme_note(lesson_html, m.start()):
            continue  # historical marker — never retroactively bump
        all_positions.append(m.start())

    if not all_positions:
        return filtered_existing

    # Determine which positions are already covered by existing changes
    # (same sequential-replace logic as _propagate_renames)
    uncovered = list(all_positions)
    for c in filtered_existing:
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

    # Note quarterly scheme if applicable (no 2026.0 — releases start at .1)
    to_major = to_version.split(".")[0] if to_version else ""
    to_minor = to_version.split(".")[1] if to_version and "." in to_version else ""
    quarterly_note = (
        f" Note: FME {to_major} uses a quarterly release model (no {to_major}.0 release)."
        if to_major.isdigit() and int(to_major) >= 2026 and to_minor != "0"
        else ""
    )

    for pos in uncovered:
        new_change_id = hashlib.md5(
            f"{lesson_id}:version:{from_version}:{pos}".encode()
        ).hexdigest()[:8]
        new_changes.append({
            "change_id": new_change_id,
            "type": "change",
            "heading": _heading_before(lesson_html, pos),
            "original_text": from_version,
            "suggested_text": to_version,
            "explanation": (
                f"Version string \"{from_version}\" should be updated to \"{to_version}\""
                f"{quarterly_note} (auto-detected; not covered by any LLM-generated change)."
            ),
            "issue_keys": [],
        })

    if new_changes:
        print(f"\n  [version-strings] Auto-added {len(new_changes)} change(s) for {lesson_id}")

    return filtered_existing + new_changes


# ---------------------------------------------------------------------------
# Post-processing helpers (issues 74, 72)
# ---------------------------------------------------------------------------


def _normalize_html_text(t: str) -> str:
    """Decode HTML entities and collapse whitespace for substring matching."""
    return " ".join(_html_module.unescape(t).split())


def _filter_stale_original_text(
    changes: list[dict],
    lesson_html: str,
    lesson_id: str,
) -> list[dict]:
    """
    Remove changes whose original_text cannot be found in the lesson HTML.
    Applies only to 'change' and 'delete' types — 'add' has no original_text.
    Issue #74.
    """
    norm_html = _normalize_html_text(lesson_html)
    valid: list[dict] = []
    for change in changes:
        orig = change.get("original_text", "")
        if change.get("type") in ("change", "delete") and orig:
            if _normalize_html_text(orig) not in norm_html:
                print(
                    f"\n  [filter-74] Dropping change {change.get('change_id', '')} "
                    f"in {lesson_id}: original_text not found: {orig[:60]!r}"
                )
                continue
        valid.append(change)
    return valid


def _filter_fmeengine_no_ui(
    changes: list[dict],
    lesson_html: str,
    lesson_id: str,
) -> list[dict]:
    """
    Narrow fallback filter for FMEENGINE-only changes in fully conceptual lessons.

    A change is removed only when ALL three conditions hold:
    1. Every key in change['issue_keys'] starts with 'FMEENGINE-'
    2. The change heading is not an exercise step (not matched by EXERCISE_STEP_PATTERN)
    3. The lesson has no instructional headings at all (pure conceptual lesson)

    Issue #72. The primary fix is the prompt rule in EDIT_SUGGESTIONS.md; this is
    a narrow code-level fallback for cases the prompt rule misses.
    """
    has_instructional = bool(config.EXERCISE_STEP_PATTERN.search(lesson_html))
    if has_instructional:
        return changes  # lesson has exercise steps — don't suppress anything here

    valid: list[dict] = []
    for change in changes:
        keys = change.get("issue_keys", [])
        if keys and all(k.startswith("FMEENGINE-") for k in keys):
            heading = change.get("heading", "")
            if not config.EXERCISE_STEP_PATTERN.match(heading):
                print(
                    f"\n  [filter-72] Dropping FMEENGINE-only change "
                    f"{change.get('change_id', '')} in {lesson_id} "
                    f"(conceptual lesson, no UI context): {heading!r}"
                )
                continue
        valid.append(change)
    return valid


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
