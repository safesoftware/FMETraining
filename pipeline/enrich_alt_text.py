"""
Step 7 (optional): Alt Text Enrichment.

Finds lesson screenshots with absent, empty, or generic alt text and generates
descriptive alt text using a multimodal LLM (gpt-4o by default). Results are
written into the edit-plans JSON as an `alt_text_updates` array so they appear
in the report UI for per-image review.

Run after Step 6:
    python pipeline.py --run-id <RUN_ID> --enrich-alt-text

Or as a standalone pass against a version folder:
    python pipeline/enrich_alt_text.py --version 2024.2 --learning-path integrate-spatial-data --dry-run
"""

from __future__ import annotations

import asyncio
import base64
import json
import re
from pathlib import Path
from typing import Optional

from openai import AsyncOpenAI
from tqdm.asyncio import tqdm as atqdm

from pipeline import config
from pipeline.utils import edit_plans_path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DECORATIVE_IMAGES = {"safe_note.png", "safe_tip.png", "safe_warning.png"}

# Alt text is considered generic/absent when it matches one of these (lowercased)
GENERIC_ALT_BLOCKLIST = {"screenshot", "image", "figure", "diagram", "step", ""}

# Alt text with this many words or fewer is a candidate for enrichment
GENERIC_ALT_MAX_WORDS = 5

SYSTEM_PROMPT = (
    "You generate concise, accurate alt text for screenshots in FME (Safe Software) "
    "training lessons. FME is a data integration platform. Your descriptions will be used "
    "to identify which UI element or dialog a screenshot is showing, and whether it needs "
    "updating when FME changes."
)

USER_INSTRUCTION = """\
Describe this screenshot in 10-15 words. Structure your description as:
"[Primary window or dialog] — [specific element, setting, or focus area, if applicable]"

Common FME UI elements include: Canvas, Navigator, Transformer Gallery, Data Preview,
Record Information Window, Bookmarks panel, Log window, Feature Information Window,
Workbench toolbar, Add Transformer dialog, Run dialog, Published Parameters dialog,
Coordinate System Gallery, Connection Management dialog, transformer parameter dialog.

If the screenshot shows workspace output data on the canvas (a map, table, or geometry \
view), describe it as "Canvas — [description of data or geometry visible]".

Use the exact element names above when they match. If the screenshot shows something \
not listed, use a clear descriptive name. Do not start with "A screenshot of".\
"""


# ---------------------------------------------------------------------------
# Image candidate detection
# ---------------------------------------------------------------------------

def _is_candidate_alt(alt: str) -> bool:
    """Return True if alt text is absent, generic, or too short to be useful."""
    stripped = alt.strip()
    lower = stripped.lower()
    if lower in GENERIC_ALT_BLOCKLIST:
        return True
    if len(stripped.split()) <= GENERIC_ALT_MAX_WORDS:
        return True
    return False


def _extract_candidates(html_path: Path) -> list[dict]:
    """Return list of {src, original_alt, img_path} for candidate images in a lesson."""
    content = html_path.read_text(encoding="utf-8", errors="ignore")
    candidates: list[dict] = []
    seen_srcs: set[str] = set()
    for m in re.finditer(r"<img[^>]+>", content):
        tag = m.group()
        src_m = re.search(r'src=["\']([^"\']+)["\']', tag)
        alt_m = re.search(r'alt=["\']([^"\']*)["\']', tag)
        if not src_m:
            continue
        src = src_m.group(1)
        if not src.startswith("images/"):
            continue
        filename = Path(src).name
        if filename in DECORATIVE_IMAGES:
            continue
        if src in seen_srcs:
            continue
        alt = alt_m.group(1) if alt_m else ""
        if not _is_candidate_alt(alt):
            continue
        img_path = html_path.parent / src
        if img_path.exists():
            seen_srcs.add(src)
            candidates.append({"src": src, "original_alt": alt, "img_path": img_path})
    return candidates


# ---------------------------------------------------------------------------
# LLM call
# ---------------------------------------------------------------------------

async def _enrich_image(
    client: AsyncOpenAI,
    sem: asyncio.Semaphore,
    candidate: dict,
) -> Optional[dict]:
    """Call the multimodal LLM to generate alt text for a single image."""
    async with sem:
        img_path: Path = candidate["img_path"]
        try:
            img_bytes = img_path.read_bytes()
        except OSError as e:
            print(f"  WARNING: Cannot read {img_path.name}: {e}")
            return None
        img_data = base64.standard_b64encode(img_bytes).decode()
        ext = img_path.suffix.lstrip(".")
        try:
            resp = await client.chat.completions.create(
                model=config.ALT_TEXT_MODEL,
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": USER_INSTRUCTION},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/{ext};base64,{img_data}",
                            "detail": "low",
                        }},
                    ],
                }],
                max_tokens=80,
            )
            suggested_alt = resp.choices[0].message.content.strip()
            return {
                "src": candidate["src"],
                "original_alt": candidate["original_alt"],
                "suggested_alt": suggested_alt,
                "explanation": (
                    "Alt text is generic or absent; descriptive text improves "
                    "accessibility and screenshot-update accuracy."
                ),
            }
        except Exception as e:
            print(f"  WARNING: Alt text generation failed for {img_path.name}: {e}")
            return None


async def _enrich_lesson(
    client: AsyncOpenAI,
    sem: asyncio.Semaphore,
    html_path: Path,
) -> list[dict]:
    """Enrich all candidate images in one lesson HTML file."""
    candidates = _extract_candidates(html_path)
    if not candidates:
        return []
    results = await asyncio.gather(*[_enrich_image(client, sem, c) for c in candidates])
    return [r for r in results if r is not None]


# ---------------------------------------------------------------------------
# Main entry points
# ---------------------------------------------------------------------------

async def _run(
    *,
    run_id: Optional[str],
    version: Optional[str],
    learning_path: Optional[str],
    dry_run: bool,
) -> None:
    client = AsyncOpenAI(api_key=config.get_openai_api_key())
    sem = asyncio.Semaphore(config.ALT_TEXT_MAX_CONCURRENT)

    # Collect HTML paths
    html_paths: list[Path] = []
    lesson_dirs: dict[Path, str] = {}  # html_path → lesson_dir (for edit-plans merge)

    if run_id:
        plans_path = edit_plans_path(run_id)
        if not plans_path.exists():
            print(f"ERROR: edit-plans file not found: {plans_path}")
            return
        plans_data = json.loads(plans_path.read_text(encoding="utf-8"))
        for lesson in plans_data.get("lessons", []):
            ld = lesson.get("lesson_dir", "")
            if not ld:
                continue
            hp = config.LESSON_CONTENT_ROOT / ld / "index.html"
            if hp.exists():
                html_paths.append(hp)
                lesson_dirs[hp] = ld
    elif version and learning_path:
        base = config.LESSON_CONTENT_ROOT / version / learning_path
        if not base.exists():
            print(f"ERROR: path not found: {base}")
            return
        for hp in sorted(base.rglob("index.html")):
            html_paths.append(hp)
    else:
        print("ERROR: Provide --run-id OR (--version + --learning-path)")
        return

    if not html_paths:
        print("No lesson HTML files found.")
        return

    print(f"Scanning {len(html_paths)} lesson HTML files for alt text candidates...")
    tasks = [_enrich_lesson(client, sem, hp) for hp in html_paths]
    all_results: list[list[dict]] = await atqdm.gather(*tasks, desc="Enriching alt text")

    total = sum(len(r) for r in all_results)
    print(f"\n{total} alt text suggestion(s) generated.")

    if dry_run:
        print("\nDRY RUN — no changes written. Suggestions:")
        for hp, updates in zip(html_paths, all_results):
            if updates:
                print(f"\n  {hp.parent.name}:")
                for u in updates:
                    print(f"    {u['src']}")
                    print(f"      current:   {u['original_alt']!r}")
                    print(f"      suggested: {u['suggested_alt']!r}")
        return

    if not run_id:
        print(
            "\nStandalone mode (no --run-id): suggestions not merged into edit-plans. "
            "Re-run with --run-id to merge, or use --dry-run to preview."
        )
        return

    # Merge into edit-plans JSON
    plans_data = json.loads(plans_path.read_text(encoding="utf-8"))
    update_map: dict[str, list[dict]] = {}
    for hp, updates in zip(html_paths, all_results):
        ld = lesson_dirs.get(hp, "")
        if ld and updates:
            update_map[ld] = updates

    merged_count = 0
    for lesson in plans_data.get("lessons", []):
        ld = lesson.get("lesson_dir", "")
        if ld in update_map:
            lesson["alt_text_updates"] = update_map[ld]
            merged_count += len(update_map[ld])

    plans_path.write_text(json.dumps(plans_data, indent=2, ensure_ascii=False))
    print(f"Merged {merged_count} suggestion(s) into: {plans_path}")


def main(
    *,
    run_id: Optional[str] = None,
    version: Optional[str] = None,
    learning_path: Optional[str] = None,
    dry_run: bool = False,
) -> None:
    asyncio.run(_run(
        run_id=run_id,
        version=version,
        learning_path=learning_path,
        dry_run=dry_run,
    ))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Enrich lesson screenshot alt text using a multimodal LLM.")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--run-id", help="Run ID to read lesson paths from edit-plans JSON")
    parser.add_argument("--version", help="Version folder (e.g. 2024.2), used with --learning-path")
    parser.add_argument("--learning-path", help="Learning path subfolder name")
    parser.add_argument("--dry-run", action="store_true", help="Preview suggestions without writing")
    args = parser.parse_args()

    main(
        run_id=args.run_id,
        version=args.version,
        learning_path=args.learning_path,
        dry_run=args.dry_run,
    )
