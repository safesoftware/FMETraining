#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fnmatch
import json
import re
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from common import dump_json, load_json, slugify

STEP_HEADING_RE = re.compile(r"^\s*(\d+)[\)\.:\-]\s*(.+)$")
UI_TOKEN_RE = re.compile(r"\b([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]*){0,3})\b")


class LessonHTMLParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.in_heading: str | None = None
        self.current_text: list[str] = []
        self.title: str | None = None
        self.headings: list[str] = []
        self.paragraphs: list[str] = []
        self.images: list[dict[str, Any]] = []
        self.current_step_num: int | None = None
        self.current_step_heading: str | None = None
        self.steps: list[dict[str, Any]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = {k: v for k, v in attrs}
        if tag in {"h1", "h2", "h3", "h4"}:
            self.in_heading = tag
            self.current_text = []
        elif tag == "img":
            src = attrs_dict.get("src") or ""
            alt = attrs_dict.get("alt")
            self.images.append({"src": src, "filename": Path(src).name if src else None, "alt": alt})

    def handle_data(self, data: str) -> None:
        if self.in_heading:
            self.current_text.append(data)
        else:
            text = data.strip()
            if text:
                self.paragraphs.append(text)

    def handle_endtag(self, tag: str) -> None:
        if self.in_heading == tag:
            txt = " ".join(t.strip() for t in self.current_text).strip()
            if txt:
                self.headings.append(txt)
                if not self.title:
                    self.title = txt
                m = STEP_HEADING_RE.match(txt)
                if m:
                    self.current_step_num = int(m.group(1))
                    self.current_step_heading = m.group(2).strip()
                    self.steps.append(
                        {"step_number": self.current_step_num, "heading": self.current_step_heading, "text": []}
                    )
            self.in_heading = None
            self.current_text = []

    def finalize_steps(self) -> None:
        idx = -1
        for p in self.paragraphs:
            if STEP_HEADING_RE.match(p):
                continue
            if idx + 1 < len(self.steps):
                self.steps[idx + 1]["text"].append(p)
                if len(self.steps[idx + 1]["text"]) >= 3:
                    idx += 1


def discover_lessons(config: dict[str, Any]) -> list[Path]:
    matches: list[Path] = []
    glob_pattern = config.get("lesson_glob", "**/index.html")
    excludes = config.get("exclude_paths", [])
    for root in config.get("lesson_roots", ["."]):
        for p in Path(root).glob(glob_pattern):
            p_norm = p.as_posix()
            if any(fnmatch.fnmatch(p_norm, ex) for ex in excludes):
                continue
            if p.is_file():
                matches.append(p)
    return sorted(set(matches))


def extract_ui_strings(headings: list[str], paragraphs: list[str]) -> list[str]:
    candidates: set[str] = set()
    for block in headings + paragraphs[:80]:
        for m in UI_TOKEN_RE.findall(block):
            if len(m) > 2 and any(c.isupper() for c in m):
                candidates.add(m.strip())
    return sorted(candidates)[:100]


def build_manifest_record(path: Path) -> dict[str, Any]:
    parser = LessonHTMLParser()
    text = path.read_text(encoding="utf-8", errors="ignore")
    parser.feed(text)
    parser.finalize_steps()

    image_refs = []
    for idx, img in enumerate(parser.images):
        nearby_caption = parser.paragraphs[idx] if idx < len(parser.paragraphs) else None
        image_refs.append(
            {
                "filename": img.get("filename"),
                "src": img.get("src"),
                "caption": nearby_caption,
                "step_number": parser.steps[idx]["step_number"] if idx < len(parser.steps) else None,
            }
        )

    title = parser.title or path.parent.name
    return {
        "lesson_id": slugify(path.parent.as_posix()),
        "lesson_path": path.as_posix(),
        "title": title,
        "headings": parser.headings,
        "exercise_steps": parser.steps,
        "ui_strings": extract_ui_strings(parser.headings, parser.paragraphs),
        "image_references": image_refs,
    }


def validate_manifest(doc: dict[str, Any]) -> None:
    if "lessons" not in doc or not isinstance(doc["lessons"], list):
        raise ValueError("manifest must include lessons[]")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default="tools/config.json")
    ap.add_argument("--out", default="artifacts/lesson_manifest.json")
    ap.add_argument("--limit", type=int)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    config = load_json(args.config)
    lessons = discover_lessons(config)
    if args.limit:
        lessons = lessons[: args.limit]

    records = [build_manifest_record(p) for p in lessons]
    out_doc = {"schema_version": "1.0", "lesson_count": len(records), "lessons": records}
    validate_manifest(out_doc)

    if args.dry_run:
        print(json.dumps({"lessons_found": len(lessons), "sample": [r["lesson_path"] for r in records[:3]]}, indent=2))
        return

    dump_json(args.out, out_doc)
    print(f"Wrote manifest with {len(records)} lessons to {args.out}")


if __name__ == "__main__":
    main()
