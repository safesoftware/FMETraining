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
) -> dict:
    """
    Generate edit plans for all lessons with medium/high assessments.

    Args:
        run_id:          Current run ID.
        recommendations: Recommendations dict from Step 3-4.
        output_dir:      Artifacts directory.
        dry_run:         If True, print counts but make no API calls.

    Returns:
        The edit plans dict.
    """
    print("\n[Step 6] Generating edit suggestions...")

    if not config.EDIT_SUGGESTIONS_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Edit suggestions prompt not found: {config.EDIT_SUGGESTIONS_PROMPT_PATH}. "
            "Ensure prompts/EDIT_SUGGESTIONS.md exists."
        )
    template = config.EDIT_SUGGESTIONS_PROMPT_PATH.read_text(encoding="utf-8")

    assessments = recommendations.get("assessments", [])
    to_version = str(recommendations.get("run_id", ""))  # fallback; real value from manifest
    # Try to get to_version from the first assessment's fix_versions, or just use a placeholder.
    # The actual to_version comes from the job; we pass it via the manifest.
    # For the prompt we will extract it from the assessments themselves if needed.

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
        _plan_all(lessons_to_run, template, out_path, existing_plans)
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
) -> list[dict]:
    if not lessons:
        return []

    client = AsyncOpenAI(api_key=config.get_openai_api_key())
    semaphore = asyncio.Semaphore(config.OPENAI_MAX_CONCURRENT)
    results: list[dict] = []
    flush_buffer: list[dict] = list(existing)

    async def plan_one(lesson_id: str, group: list[dict]) -> dict | None:
        async with semaphore:
            prompt = _build_prompt(lesson_id, group, template)
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

            # Assign stable change_ids based on lesson+index
            for i, change in enumerate(parsed.get("changes", [])):
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
                "changes": parsed.get("changes", []),
                "screenshot_updates": parsed.get("screenshot_updates", []),
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

def _build_prompt(
    lesson_id: str,
    group: list[dict],
    template: str,
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

    # Store on the first assessment so _call_openai can embed it in the output
    first["_lesson_html"] = lesson_html

    # Build issues list
    issues_parts = []
    for a in group:
        issues_parts.append(
            f"### {a['issue_key']}: {a.get('issue_summary', '')}\n"
            f"- **Update likelihood**: {a.get('update_likelihood', '')}\n"
            f"- **Assessment**: {a.get('justification', '')}"
        )
    issues_list = "\n\n".join(issues_parts)

    # Truncate HTML if very large (keep first 30,000 chars to stay within context)
    if len(lesson_html) > 30_000:
        lesson_html = lesson_html[:30_000] + "\n<!-- [truncated] -->"

    substitutions = {
        "LESSON_NAME": first.get("lesson_name", ""),
        "COURSE_CANONICAL": first.get("course_canonical", ""),
        "LEARNING_PATH": first.get("learning_path", ""),
        "FROM_VERSION": first.get("version", ""),
        "TO_VERSION": _infer_to_version(group),
        "LESSON_HTML": lesson_html,
        "ISSUES_LIST": issues_list,
    }

    prompt = template
    for key, value in substitutions.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)
    return prompt


def _infer_to_version(group: list[dict]) -> str:
    """Best-effort: use the most common fix_version across the group."""
    versions: list[str] = []
    for a in group:
        versions.extend(a.get("fix_versions", []))
    if not versions:
        return "the new version"
    # Return the most frequently mentioned version
    return max(set(versions), key=versions.count)


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
