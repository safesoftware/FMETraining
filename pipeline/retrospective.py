#!/usr/bin/env python3
"""
Retrospective analysis for FME Training Automation runs.

Compares suggested edits from an edit-plans artifact against the actual changes
made in the target version folder, classifying each suggestion as:
  - accepted  : suggested_text (or close variant) found in target content
  - rejected  : original_text unchanged in target content
  - reworded  : section was changed but not to the suggested text
  - not_updated : target lesson file does not exist (course not updated)
  - na        : original_text not found in source (stale suggestion)

Also detects "missed" changes — actual edits in the target that the tool never
suggested — for both text sections and screenshots.

Usage:
    python pipeline/retrospective.py --run-id 20260317T155430-28a8
    python pipeline/retrospective.py --run-id <id> --source-version 2024.2 --target-version 2026.1

Output:
    - Markdown summary table printed to stdout
    - artifacts/retrospective-{run_id}.json written to disk
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from difflib import SequenceMatcher
from pathlib import Path

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("Error: beautifulsoup4 is required. Run: pip install beautifulsoup4")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ACCEPTED_THRESHOLD = 0.82    # similarity to suggested_text → accepted
REJECTED_THRESHOLD = 0.90    # similarity to original_text  → rejected
DECORATIVE_IMAGES = {"safe_note.png", "safe_tip.png", "safe_warning.png"}

BASE_DIR = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Text utilities
# ---------------------------------------------------------------------------

def normalize(text: str) -> str:
    """Decode HTML entities and collapse whitespace."""
    import html as html_module
    return " ".join(html_module.unescape(text).split())


def get_full_text(html_content: str) -> str:
    """Extract and normalize all plain text from an HTML document."""
    soup = BeautifulSoup(html_content, "lxml")
    return normalize(soup.get_text(separator=" "))


def split_by_headings(html_content: str) -> dict[str, str]:
    """
    Split HTML into sections keyed by heading text.
    Returns {normalized_heading: normalized_section_text}
    """
    soup = BeautifulSoup(html_content, "lxml")
    headings = [(normalize(h.get_text()), h) for h in soup.find_all(["h2", "h3"])]

    if not headings:
        return {"__body__": get_full_text(html_content)}

    full_text = soup.get_text(separator="\n")
    sections = {}
    prev_search_pos = 0

    for i, (h_text, _) in enumerate(headings):
        if not h_text.split():
            continue
        h_pos = full_text.find(h_text.split()[0], prev_search_pos)  # rough anchor
        if h_pos == -1:
            h_pos = prev_search_pos

        section_start = h_pos + len(h_text)

        if i + 1 < len(headings):
            next_words = headings[i + 1][0].split()
            if next_words:
                next_anchor = next_words[0]
                next_pos = full_text.find(next_anchor, section_start)
                section_end = next_pos if next_pos != -1 else len(full_text)
            else:
                section_end = len(full_text)
        else:
            section_end = len(full_text)

        sections[h_text] = normalize(full_text[section_start:section_end])
        prev_search_pos = section_start

    return sections


def text_contains(haystack: str, needle: str) -> tuple[bool, float]:
    """
    Check if needle appears in haystack, returning (found, similarity_score).
    First tries exact substring; falls back to SequenceMatcher ratio.
    """
    h = normalize(haystack)
    n = normalize(needle)

    if not n:
        return False, 0.0

    if n in h:
        return True, 1.0

    # Fuzzy: compare needle against a sliding window of the same length (±30%)
    n_len = len(n)
    if n_len > len(h):
        ratio = SequenceMatcher(None, n, h).ratio()
        return ratio >= ACCEPTED_THRESHOLD, ratio

    best = 0.0
    step = max(10, n_len // 8)
    slack = n_len // 4
    for i in range(0, len(h) - n_len + 1, step):
        window = h[i : i + n_len + slack]
        r = SequenceMatcher(None, n, window).ratio()
        if r > best:
            best = r
        if best >= ACCEPTED_THRESHOLD:
            return True, best

    return best >= ACCEPTED_THRESHOLD, best


def get_images(html_content: str) -> list[str]:
    """Return list of non-decorative image src values in document order."""
    soup = BeautifulSoup(html_content, "lxml")
    return [
        img.get("src", "")
        for img in soup.find_all("img")
        if not any(img.get("src", "").endswith(d) for d in DECORATIVE_IMAGES)
    ]


# ---------------------------------------------------------------------------
# Path mapping
# ---------------------------------------------------------------------------

def map_to_target(lesson_dir: str, source_version: str, target_version: str) -> str:
    """
    Derive the target lesson directory path from the source lesson_dir.
    Replaces all occurrences of source_version with target_version.
    """
    return lesson_dir.replace(source_version, target_version)


# ---------------------------------------------------------------------------
# Per-change classification
# ---------------------------------------------------------------------------

def classify_change(change: dict, source_text: str, target_text: str) -> dict:
    """Classify a single suggested change against source and target full texts."""
    original = change.get("original_text", "")
    suggested = change.get("suggested_text", "")
    change_type = change.get("type", "change")

    result = {
        "change_id": change["change_id"],
        "type": change_type,
        "heading": change.get("heading", ""),
        "issue_keys": change.get("issue_keys", []),
        "classification": None,
        "similarity_to_suggested": 0.0,
        "similarity_to_original": 0.0,
        "notes": "",
    }

    # For 'add' type there may be no original_text
    if not original and change_type == "add":
        found, sim = text_contains(target_text, suggested)
        result["similarity_to_suggested"] = round(sim, 3)
        result["classification"] = "accepted" if found else "rejected"
        return result

    # Sanity check: does original_text appear in source?
    orig_in_source, orig_source_sim = text_contains(source_text, original)
    result["similarity_to_original"] = round(orig_source_sim, 3)

    if not orig_in_source:
        result["classification"] = "na"
        result["notes"] = "original_text not found in source HTML"
        return result

    # Does original_text still appear unchanged in target?
    orig_in_target, _ = text_contains(target_text, original)

    # Does suggested_text appear in target?
    sugg_in_target, sugg_sim = text_contains(target_text, suggested)
    result["similarity_to_suggested"] = round(sugg_sim, 3)

    if sugg_in_target:
        result["classification"] = "accepted"
    elif orig_in_target:
        result["classification"] = "rejected"
    else:
        result["classification"] = "reworded"

    return result


# ---------------------------------------------------------------------------
# Missed-change detection
# ---------------------------------------------------------------------------

def find_missed_text_changes(
    source_sections: dict[str, str],
    target_sections: dict[str, str],
    suggested_headings: set[str],
) -> list[dict]:
    """
    Identify sections that changed between source and target but were not
    covered by any suggestion (i.e. false negatives / missed changes).
    """
    missed = []
    for heading, src_text in source_sections.items():
        tgt_text = target_sections.get(heading, "")
        if not tgt_text:
            continue  # section missing in target — don't flag as missed

        # Check if the section changed meaningfully
        sim = SequenceMatcher(None, src_text, tgt_text).ratio()
        if sim >= REJECTED_THRESHOLD:
            continue  # essentially unchanged

        # Changed — was it covered by a suggestion?
        normalized_heading = normalize(heading)
        covered = any(
            normalized_heading in normalize(sh) or normalize(sh) in normalized_heading
            for sh in suggested_headings
        )
        if not covered:
            missed.append({
                "heading": heading,
                "source_snippet": src_text[:200],
                "target_snippet": tgt_text[:200],
                "similarity": round(sim, 3),
                "notes": "Section changed in target but not covered by any suggestion",
            })

    # Check for new headings in target not in source
    for heading in target_sections:
        if heading not in source_sections:
            covered = any(
                normalize(heading) in normalize(sh) or normalize(sh) in normalize(heading)
                for sh in suggested_headings
            )
            if not covered and target_sections[heading].strip():
                missed.append({
                    "heading": heading,
                    "source_snippet": "(section not in source)",
                    "target_snippet": target_sections[heading][:200],
                    "similarity": 0.0,
                    "notes": "New section in target not suggested by tool",
                })

    return missed


def find_missed_screenshots(
    source_images: list[str],
    target_images: list[str],
    suggested_srcs: set[str],
) -> list[dict]:
    """
    Find images that were replaced in the target but not flagged in screenshot_updates.
    Matched by position (nth image in source vs nth image in target).
    """
    missed = []
    n = min(len(source_images), len(target_images))

    for i in range(n):
        src_img = source_images[i]
        tgt_img = target_images[i]
        if src_img == tgt_img:
            continue  # unchanged

        # Image was replaced — was it suggested?
        if src_img not in suggested_srcs:
            missed.append({
                "src": src_img,
                "target_src": tgt_img,
                "notes": "Image replaced in target but not flagged in screenshot_updates",
            })

    # New images in target beyond what source had
    for i in range(n, len(target_images)):
        missed.append({
            "src": "(new image)",
            "target_src": target_images[i],
            "notes": "New image in target not present in source",
        })

    return missed


# ---------------------------------------------------------------------------
# Lesson analysis
# ---------------------------------------------------------------------------

def analyze_lesson(lesson: dict, source_version: str, target_version: str) -> dict:
    """Analyze a single lesson entry from the edit-plans JSON."""
    lesson_id = lesson["lesson_id"]
    lesson_name = lesson["lesson_name"]
    course = lesson.get("course_canonical", "")
    learning_path = lesson.get("learning_path", "")
    lesson_dir = lesson["lesson_dir"]

    source_path = BASE_DIR / lesson_dir / "index.html"
    target_dir = map_to_target(lesson_dir, source_version, target_version)
    target_path = BASE_DIR / target_dir / "index.html"

    # --- Load HTML ---
    if not source_path.exists():
        # Fall back to embedded HTML from the run artifact
        source_html = lesson.get("lesson_html", "")
    else:
        source_html = source_path.read_text(encoding="utf-8")

    target_exists = target_path.exists()

    result = {
        "lesson_id": lesson_id,
        "lesson_name": lesson_name,
        "course": course,
        "learning_path": learning_path,
        "source_path": str(source_path.relative_to(BASE_DIR)),
        "target_path": str(target_path.relative_to(BASE_DIR)),
        "target_path_found": target_exists,
        "changes": [],
        "screenshot_updates": [],
        "missed_changes": [],
        "missed_screenshots": [],
        "summary": {
            "text_accepted": 0,
            "text_rejected": 0,
            "text_reworded": 0,
            "text_not_updated": 0,
            "text_na": 0,
            "screenshot_accepted": 0,
            "screenshot_rejected": 0,
            "screenshot_not_updated": 0,
            "screenshot_na": 0,
            "missed_text": 0,
            "missed_screenshots": 0,
        },
    }

    changes = lesson.get("changes", [])
    screenshot_updates = lesson.get("screenshot_updates", [])

    # --- Not updated ---
    if not target_exists:
        for change in changes:
            result["changes"].append({
                "change_id": change["change_id"],
                "type": change.get("type", "change"),
                "heading": change.get("heading", ""),
                "issue_keys": change.get("issue_keys", []),
                "classification": "not_updated",
                "similarity_to_suggested": 0.0,
                "similarity_to_original": 0.0,
                "notes": "Target lesson file not found",
            })
            result["summary"]["text_not_updated"] += 1
        for su in screenshot_updates:
            result["screenshot_updates"].append({
                "src": su.get("src", ""),
                "classification": "not_updated",
            })
            result["summary"]["screenshot_not_updated"] += 1
        return result

    target_html = target_path.read_text(encoding="utf-8")

    source_text = get_full_text(source_html)
    target_text = get_full_text(target_html)
    source_sections = split_by_headings(source_html)
    target_sections = split_by_headings(target_html)
    source_images = get_images(source_html)
    target_images = get_images(target_html)
    suggested_srcs = {su.get("src", "") for su in screenshot_updates}

    # --- Classify text changes ---
    suggested_headings = {c.get("heading", "") for c in changes}
    for change in changes:
        classified = classify_change(change, source_text, target_text)
        result["changes"].append(classified)
        cls = classified["classification"]
        result["summary"][f"text_{cls}"] = result["summary"].get(f"text_{cls}", 0) + 1

    # --- Classify screenshot updates ---
    for su in screenshot_updates:
        src = su.get("src", "")
        # Find the corresponding position in source images
        if src in source_images:
            idx = source_images.index(src)
            if idx < len(target_images) and target_images[idx] != src:
                classification = "accepted"
            else:
                classification = "rejected"
        else:
            classification = "na"
        result["screenshot_updates"].append({"src": src, "classification": classification})
        result["summary"][f"screenshot_{classification}"] = (
            result["summary"].get(f"screenshot_{classification}", 0) + 1
        )

    # --- Missed text changes ---
    result["missed_changes"] = find_missed_text_changes(
        source_sections, target_sections, suggested_headings
    )
    result["summary"]["missed_text"] = len(result["missed_changes"])

    # --- Missed screenshots ---
    result["missed_screenshots"] = find_missed_screenshots(
        source_images, target_images, suggested_srcs
    )
    result["summary"]["missed_screenshots"] = len(result["missed_screenshots"])

    return result


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------

def compute_overall(lessons_results: list[dict]) -> dict:
    totals = {
        "total_lessons": len(lessons_results),
        "total_text_suggestions": 0,
        "text_accepted": 0,
        "text_rejected": 0,
        "text_reworded": 0,
        "text_not_updated": 0,
        "text_na": 0,
        "total_screenshot_suggestions": 0,
        "screenshot_accepted": 0,
        "screenshot_rejected": 0,
        "screenshot_not_updated": 0,
        "screenshot_na": 0,
        "missed_text": 0,
        "missed_screenshots": 0,
    }
    for lr in lessons_results:
        s = lr["summary"]
        totals["total_text_suggestions"] += len(lr["changes"])
        totals["total_screenshot_suggestions"] += len(lr["screenshot_updates"])
        for key in ("text_accepted", "text_rejected", "text_reworded", "text_not_updated", "text_na",
                    "screenshot_accepted", "screenshot_rejected", "screenshot_not_updated", "screenshot_na"):
            totals[key] += s.get(key, 0)
        totals["missed_text"] += s.get("missed_text", 0)
        totals["missed_screenshots"] += s.get("missed_screenshots", 0)

    txt_scoreable = totals["text_accepted"] + totals["text_rejected"] + totals["text_reworded"]
    totals["text_accept_rate"] = round(totals["text_accepted"] / txt_scoreable, 3) if txt_scoreable else 0.0

    ss_scoreable = totals["screenshot_accepted"] + totals["screenshot_rejected"]
    totals["screenshot_accept_rate"] = (
        round(totals["screenshot_accepted"] / ss_scoreable, 3) if ss_scoreable else 0.0
    )
    return totals


def _lesson_combined(s: dict) -> dict:
    """
    Combine text and screenshot stats into a single set of counts.
    Denominator = accepted + rejected + reworded + missed (excludes na/not_updated,
    which are tool-quality issues rather than coverage outcomes).
    """
    acc = s["text_accepted"] + s["screenshot_accepted"]
    rej = s["text_rejected"] + s["screenshot_rejected"]
    rwd = s["text_reworded"]  # screenshots can't be reworded
    msd = s["missed_text"] + s["missed_screenshots"]
    total = acc + rej + rwd + msd  # denominator
    return {"acc": acc, "rej": rej, "rwd": rwd, "msd": msd, "total": total}


def _pct(num: int, denom: int) -> str:
    return f"{num/denom:.0%}" if denom else "—"


def print_summary_table(lessons_results: list[dict], overall: dict) -> None:
    L = 30   # lesson name width
    C = 24   # course width
    P = 18   # learning path width
    W = L + C + P + 55
    print()
    print("=" * W)
    print("RETROSPECTIVE SUMMARY")
    print("=" * W)

    hdr1 = (
        f"{'Lesson':<{L}} {'Course':<{C}} {'Learning Path':<{P}}"
        f" {'Tot':>4}  {'Acc':>4} {'Acc%':>5}  {'Rej':>4} {'Rej%':>5}"
        f"  {'Rwd':>4} {'Rwd%':>5}  {'Msd':>4} {'Msd%':>5}"
    )
    print(hdr1)
    print("-" * W)

    for lr in lessons_results:
        c = _lesson_combined(lr["summary"])
        print(
            f"{lr['lesson_name'][:L-1]:<{L}}"
            f" {lr['course'][:C-1]:<{C}}"
            f" {lr.get('learning_path','')[:P-1]:<{P}}"
            f" {c['total']:>4}"
            f"  {c['acc']:>4} {_pct(c['acc'],c['total']):>5}"
            f"  {c['rej']:>4} {_pct(c['rej'],c['total']):>5}"
            f"  {c['rwd']:>4} {_pct(c['rwd'],c['total']):>5}"
            f"  {c['msd']:>4} {_pct(c['msd'],c['total']):>5}"
        )

    print("-" * W)
    # Overall totals
    oa = overall["text_accepted"] + overall["screenshot_accepted"]
    or_ = overall["text_rejected"] + overall["screenshot_rejected"]
    orw = overall["text_reworded"]
    om = overall["missed_text"] + overall["missed_screenshots"]
    ot = oa + or_ + orw + om
    print(
        f"{'TOTAL':<{L}} {'':^{C}} {'':^{P}}"
        f" {ot:>4}"
        f"  {oa:>4} {_pct(oa,ot):>5}"
        f"  {or_:>4} {_pct(or_,ot):>5}"
        f"  {orw:>4} {_pct(orw,ot):>5}"
        f"  {om:>4} {_pct(om,ot):>5}"
    )
    print()
    na_txt = overall["text_na"] + overall["screenshot_na"]
    nu_txt = overall["text_not_updated"] + overall["screenshot_not_updated"]
    print(
        f"Excluded from denominator: {na_txt} stale suggestions (original_text not in source), "
        f"{nu_txt} not-updated (target lesson missing)."
    )
    print(
        "Acc=accepted, Rej=rejected, Rwd=reworded (text only), "
        "Msd=missed (changes made that tool never suggested, text+screenshots)."
    )
    print()


def print_detail(lessons_results: list[dict]) -> None:
    print("=" * 110)
    print("PER-CHANGE DETAIL")
    print("=" * 110)

    STATUS_ICONS = {
        "accepted": "✓",
        "rejected": "✗",
        "reworded": "~",
        "not_updated": "-",
        "na": "?",
    }

    for lr in lessons_results:
        if not lr["changes"] and not lr["missed_changes"] and not lr["missed_screenshots"]:
            continue

        print(f"\n[{lr['lesson_name']}]  ({lr['course']})")

        for c in lr["changes"]:
            icon = STATUS_ICONS.get(c["classification"], "?")
            print(
                f"  {icon} [{c['classification'].upper():>11}] {c['heading'][:60]}"
                f"  (id={c['change_id']}, issues={','.join(c['issue_keys'])})"
            )
            if c.get("notes"):
                print(f"       NOTE: {c['notes']}")

        for su in lr["screenshot_updates"]:
            icon = STATUS_ICONS.get(su["classification"], "?")
            print(f"  {icon} [{su['classification'].upper():>11}] 📷 {su['src']}")

        for mc in lr["missed_changes"]:
            print(f"  ! [      MISSED] {mc['heading'][:60]}  (sim={mc['similarity']})")
            print(f"       SRC: {mc['source_snippet'][:80]}")
            print(f"       TGT: {mc['target_snippet'][:80]}")

        for ms in lr["missed_screenshots"]:
            print(f"  ! [MISSED SCRSH] 📷 {ms['src']} → {ms['target_src']}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Retrospective analysis for a training automation run")
    parser.add_argument("--run-id", required=True, help="Run ID (e.g. 20260317T155430-28a8)")
    parser.add_argument("--source-version", default="2024.2", help="Source content version (default: 2024.2)")
    parser.add_argument("--target-version", default="2026.1", help="Target content version (default: 2026.1)")
    parser.add_argument("--no-detail", action="store_true", help="Skip per-change detail output")
    args = parser.parse_args()

    edit_plans_path = BASE_DIR / "artifacts" / f"edit-plans-{args.run_id}.json"
    if not edit_plans_path.exists():
        print(f"Error: edit-plans file not found: {edit_plans_path}")
        sys.exit(1)

    print(f"Loading edit plans from {edit_plans_path.name} ...")
    with open(edit_plans_path, encoding="utf-8") as f:
        edit_plans = json.load(f)

    lessons = edit_plans.get("lessons", [])
    print(f"Analyzing {len(lessons)} lessons ({args.source_version} → {args.target_version}) ...")

    lessons_results = []
    for i, lesson in enumerate(lessons, 1):
        sys.stdout.write(f"\r  [{i}/{len(lessons)}] {lesson['lesson_name'][:50]:<50}")
        sys.stdout.flush()
        lessons_results.append(analyze_lesson(lesson, args.source_version, args.target_version))
    print()

    overall = compute_overall(lessons_results)

    print_summary_table(lessons_results, overall)

    if not args.no_detail:
        print_detail(lessons_results)

    # Write JSON output
    output = {
        "run_id": args.run_id,
        "source_version": args.source_version,
        "target_version": args.target_version,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lessons": lessons_results,
        "overall": overall,
    }

    out_path = BASE_DIR / "artifacts" / f"retrospective-{args.run_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    print(f"Results written to {out_path.relative_to(BASE_DIR)}")


if __name__ == "__main__":
    main()
