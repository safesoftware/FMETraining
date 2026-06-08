"""
Steps 3+4: Prompt Building and OpenAI Assessment.

For each (lesson, jira_issue) pair, builds a prompt from the ASSESSMENT.md
template and calls the OpenAI API with structured output to assess whether
the lesson requires an update.

Writes artifacts/update-recommendations-{RUN_ID}.json.
Supports incremental mode: skips pairs already present in the output file.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from openai import AsyncOpenAI
from tqdm.asyncio import tqdm as atqdm

from pipeline import config
from pipeline.utils import recommendations_path


# ---------------------------------------------------------------------------
# Structured output JSON schema for OpenAI
# ---------------------------------------------------------------------------

_RESPONSE_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "lesson_assessment",
        "strict": True,
        "schema": {
            "type": "object",
            "required": [
                "update_likelihood",
                "justification",
                "impacts_exercise",
                "affected_headings",
                "screenshots_need_retaking",
                "affected_screenshots",
            ],
            "additionalProperties": False,
            "properties": {
                "update_likelihood": {
                    "type": "string",
                    "enum": ["none", "low", "medium", "high"],
                },
                "justification": {"type": "string"},
                "impacts_exercise": {"type": "boolean"},
                "affected_headings": {
                    "type": "array",
                    "items": {"type": "string"},
                },
                "screenshots_need_retaking": {"type": "boolean"},
                "affected_screenshots": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["src", "explanation"],
                        "additionalProperties": False,
                        "properties": {
                            "src": {"type": "string"},
                            "explanation": {"type": "string"},
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

def run_assessment(
    run_id: str,
    manifest: dict,
    changelog: dict,
    output_dir: Path,
    descriptions: dict[str, str] | None = None,
    dry_run: bool = False,
) -> dict:
    """
    Assess all (lesson, issue) pairs and write the recommendations JSON.

    Args:
        run_id:       Current run ID.
        manifest:     Manifest dict from Step 1.
        changelog:    Changelog dict from Step 2 (issue dicts may or may not
                      carry 'description' — see ``descriptions``).
        output_dir:   Artifacts directory.
        descriptions: Optional in-memory mapping of issue_key -> description.
                      When the changelog was loaded from the slim disk artifact
                      (resume mode), descriptions are not embedded in the
                      issue dicts and must be supplied here. The pipeline
                      orchestrator builds and threads this dict; it is never
                      persisted to disk.
        dry_run:      If True, print pair counts but make no API calls.

    Returns:
        The recommendations dict.
    """
    print("\n[Steps 3+4] Running LLM assessment...")

    # Load prompt template
    if not config.ASSESSMENT_PROMPT_PATH.exists():
        raise FileNotFoundError(
            f"Prompt template not found: {config.ASSESSMENT_PROMPT_PATH}. "
            "Ensure prompts/ASSESSMENT.md exists."
        )
    template = config.ASSESSMENT_PROMPT_PATH.read_text(encoding="utf-8")

    lessons = manifest.get("lessons", [])
    issues = changelog.get("issues", [])
    to_version = str(manifest.get("job", {}).get("to_version", ""))

    # Build all pairs, filtering by product-project relevance.
    # Skip (lesson, issue) pairs where the issue's Jira project is known to cover
    # only products that this lesson does not teach (e.g. FMEFLOW issues vs. fme_form lessons).
    all_pairs = [
        (lesson, issue)
        for lesson in lessons
        for issue in issues
        if _is_relevant_pair(lesson, issue)
    ]
    total_pairs = len(all_pairs)

    print(f"  Lessons: {len(lessons)}")
    print(f"  Issues:  {len(issues)}")
    print(f"  Total pairs: {total_pairs:,} (after product-project filtering)")

    # Estimate cost
    approx_input_tokens = total_pairs * 1500
    approx_output_tokens = total_pairs * 150
    mini_cost = (approx_input_tokens / 1_000_000 * 0.15) + (approx_output_tokens / 1_000_000 * 0.60)
    gpt4o_cost = (approx_input_tokens / 1_000_000 * 2.50) + (approx_output_tokens / 1_000_000 * 10.0)
    print(f"  Estimated cost: ~${mini_cost:.2f} (gpt-4o-mini) / ~${gpt4o_cost:.2f} (gpt-4o)")
    print(f"  Model: {config.OPENAI_MODEL}")

    if dry_run:
        print("  [dry-run] Skipping API calls.")
        return {
            "run_id": run_id,
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "model": config.OPENAI_MODEL,
            "total_pairs": total_pairs,
            "completed_pairs": 0,
            "skipped_pairs": 0,
            "assessments": [],
        }

    # Load existing results for incremental mode
    out_path = recommendations_path(run_id, output_dir)
    existing_assessments, skip_set = _load_existing(out_path)

    skipped = len(skip_set)
    pairs_to_run = [
        (lesson, issue)
        for lesson, issue in all_pairs
        if (lesson["lesson_id"], issue["issue_key"]) not in skip_set
    ]

    if skipped:
        print(f"  Resuming: {skipped:,} pairs already assessed, {len(pairs_to_run):,} remaining.")

    # Run async assessment
    new_assessments = asyncio.run(
        _assess_all(
            pairs_to_run, template, to_version, out_path, existing_assessments,
            descriptions or {},
        )
    )

    all_assessments = existing_assessments + new_assessments

    recommendations = {
        "run_id": run_id,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "model": config.OPENAI_MODEL,
        "total_pairs": total_pairs,
        "completed_pairs": len(all_assessments),
        "skipped_pairs": skipped,
        "assessments": all_assessments,
    }

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(recommendations, f, indent=2, ensure_ascii=False)

    print(f"  Recommendations written: {out_path.name}")
    return recommendations


# ---------------------------------------------------------------------------
# Async assessment loop
# ---------------------------------------------------------------------------

async def _assess_all(
    pairs: list[tuple[dict, dict]],
    template: str,
    to_version: str,
    out_path: Path,
    existing: list[dict],
    descriptions: dict[str, str],
) -> list[dict]:
    """Run all pairs through the OpenAI API with concurrency control."""
    if not pairs:
        return []

    client = AsyncOpenAI(api_key=config.get_openai_api_key())
    semaphore = asyncio.Semaphore(config.OPENAI_MAX_CONCURRENT)
    results: list[dict] = []
    flush_buffer: list[dict] = list(existing)  # Start with existing for flush

    async def assess_one(lesson: dict, issue: dict) -> dict | None:
        async with semaphore:
            prompt = _build_prompt(lesson, issue, template, to_version, descriptions)
            result = await _call_openai(client, lesson, issue, prompt)
            return result

    tasks = [assess_one(lesson, issue) for lesson, issue in pairs]

    with atqdm(total=len(tasks), desc="Assessing pairs", unit="pair") as pbar:
        for coro in asyncio.as_completed(tasks):
            result = await coro
            pbar.update(1)
            if result is not None:
                results.append(result)
                flush_buffer.append(result)

                # Flush to disk periodically
                if len(results) % config.ASSESSMENT_FLUSH_INTERVAL == 0:
                    _flush_partial(out_path, flush_buffer)

    # Final flush
    _flush_partial(out_path, flush_buffer)
    return results


async def _call_openai(
    client: AsyncOpenAI,
    lesson: dict,
    issue: dict,
    prompt: str,
) -> dict | None:
    """Make a single OpenAI API call and return an assessment dict."""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=config.OPENAI_MODEL,
                messages=[{"role": "user", "content": prompt}],
                response_format=_RESPONSE_SCHEMA,
                temperature=0.1,
            )
            raw = response.choices[0].message.content
            parsed = json.loads(raw)

            rec_id = hashlib.md5(
                f"{lesson['lesson_id']}:{issue['issue_key']}".encode()
            ).hexdigest()[:8]

            lesson_dir = str(Path(lesson["path"]).parent).replace("\\", "/")

            return {
                "rec_id": rec_id,
                "lesson_id": lesson["lesson_id"],
                "lesson_dir": lesson_dir,
                "lesson_name": lesson["lesson_name"],
                "course_canonical": lesson["course_canonical"],
                "learning_path": lesson["learning_path"],
                "version": lesson["version"],
                "product": lesson.get("product", []),
                "issue_key": issue["issue_key"],
                "issue_summary": issue["summary"],
                "issue_type": issue.get("issue_type", ""),
                "issue_status": issue.get("status", ""),
                "affects_versions": issue.get("affects_versions", []),
                "fix_versions": issue.get("fix_versions", []),
                "update_likelihood": parsed["update_likelihood"],
                "justification": parsed["justification"],
                "impacts_exercise": parsed["impacts_exercise"],
                "affected_headings": parsed["affected_headings"],
                "screenshots_need_retaking": parsed["screenshots_need_retaking"],
                "affected_screenshots": parsed["affected_screenshots"],
                "assessed_at": datetime.now(tz=timezone.utc).isoformat(),
                "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
                "completion_tokens": response.usage.completion_tokens if response.usage else None,
            }

        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                print(
                    f"\n  ERROR assessing {lesson['lesson_id']} × {issue['issue_key']}: {e}"
                )
                return None

    return None


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------

def _build_prompt(
    lesson: dict,
    issue: dict,
    template: str,
    to_version: str,
    descriptions: dict[str, str] | None = None,
) -> str:
    """Substitute {{PLACEHOLDER}} variables into the ASSESSMENT.md template."""
    descriptions = descriptions or {}

    def _fmt_headings(headings: list[dict]) -> str:
        if not headings:
            return "(none)"
        lines = []
        for h in headings:
            indent = "  " * (h["level"] - 2)
            lines.append(f"{indent}- [h{h['level']}] {h['text']}")
        return "\n".join(lines)

    def _fmt_steps(steps: list[dict]) -> str:
        if not steps:
            return "(no exercise steps)"
        return "\n".join(f"- Step {s['step_number']}: \"{s['title']}\"" for s in steps)

    def _fmt_ui_strings(strings: list[str]) -> str:
        if not strings:
            return "(none identified)"
        return ", ".join(strings)

    def _fmt_images(images: list[dict]) -> str:
        if not images:
            return "(no images)"
        lines = []
        for img in images:
            step_info = f"step: {img['nearby_step']}" if img.get("nearby_step") else "step: n/a"
            heading_info = img.get("nearby_heading") or "n/a"
            lines.append(
                f"- {img['src']} (alt: \"{img.get('alt', '')}\", "
                f"{step_info}, heading: \"{heading_info}\")"
            )
        return "\n".join(lines)

    # Truncate long issue descriptions. Prefer the ephemeral descriptions dict
    # (sourced from same-process changelog or on-demand fetch); fall back to
    # any description still embedded on the issue dict.
    description = (
        descriptions.get(issue.get("issue_key", ""))
        or issue.get("description")
        or "(no description)"
    )
    if len(description) > 2000:
        description = description[:2000] + "\n[truncated]"

    if config.INCLUDE_FULL_TEXT:
        lesson_text = lesson.get("lesson_text", "")
        lesson_text_section = (
            f"**Full Lesson Text** (use this to verify whether specific items "
            f"are actually present in the lesson):\n\n{lesson_text}"
            if lesson_text else ""
        )
    else:
        lesson_text_section = ""

    substitutions = {
        "LESSON_NAME": lesson.get("lesson_name", ""),
        "COURSE_CANONICAL": lesson.get("course_canonical", ""),
        "LEARNING_PATH": lesson.get("learning_path", ""),
        "PRODUCT": ", ".join(lesson.get("product", [])),
        "FROM_VERSION": lesson.get("version", ""),
        "TO_VERSION": to_version,
        "HEADINGS_LIST": _fmt_headings(lesson.get("headings", [])),
        "EXERCISE_STEPS_LIST": _fmt_steps(lesson.get("exercise_steps", [])),
        "UI_STRINGS_LIST": _fmt_ui_strings(lesson.get("ui_strings", [])),
        "IMAGES_LIST": _fmt_images(lesson.get("images", [])),
        "LESSON_TEXT_SECTION": lesson_text_section,
        "ISSUE_KEY": issue.get("issue_key", ""),
        "ISSUE_SUMMARY": issue.get("summary", ""),
        "ISSUE_TYPE": issue.get("issue_type", ""),
        "ISSUE_STATUS": issue.get("status", ""),
        "AFFECTS_VERSIONS": ", ".join(issue.get("affects_versions", [])),
        "FIX_VERSIONS": ", ".join(issue.get("fix_versions", [])),
        "ISSUE_DESCRIPTION": description,
    }

    prompt = template
    for key, value in substitutions.items():
        prompt = prompt.replace(f"{{{{{key}}}}}", value)
    return prompt


# ---------------------------------------------------------------------------
# Incremental helpers
# ---------------------------------------------------------------------------
# Product-project relevance filter
# ---------------------------------------------------------------------------

def _is_relevant_pair(lesson: dict, issue: dict) -> bool:
    """
    Return True if the issue's Jira project is relevant to the lesson's product(s).

    Uses PROJECT_KEY_TO_PRODUCTS from config. If the project key is not in the
    mapping, it is treated as relevant to all products. If the mapping exists,
    there must be at least one product in common between the lesson and the issue's
    project for the pair to be included.
    """
    project_key = issue.get("project_key", "").strip().upper()
    lesson_products = set(lesson.get("product", []))

    project_products = config.PROJECT_KEY_TO_PRODUCTS.get(project_key)
    if project_products is None:
        # Unknown project — include by default
        return True

    return bool(lesson_products & set(project_products))


# ---------------------------------------------------------------------------

def _load_existing(out_path: Path) -> tuple[list[dict], set[tuple]]:
    """Load existing assessments from disk (for incremental/resume mode)."""
    if not out_path.exists():
        return [], set()
    try:
        with open(out_path, encoding="utf-8") as f:
            data = json.load(f)
        assessments = data.get("assessments", [])
        skip_set = {(a["lesson_id"], a["issue_key"]) for a in assessments}
        return assessments, skip_set
    except Exception:
        return [], set()


def _flush_partial(out_path: Path, assessments: list[dict]) -> None:
    """Write a partial recommendations file to disk (resilient to interruption)."""
    partial = {
        "run_id": "partial",
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "model": config.OPENAI_MODEL,
        "total_pairs": len(assessments),
        "completed_pairs": len(assessments),
        "skipped_pairs": 0,
        "assessments": assessments,
    }
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(partial, f, indent=2, ensure_ascii=False)
    except Exception:
        pass  # Don't interrupt the main loop for flush failures
