#!/usr/bin/env python3
"""Fill template.html with academy-map.json -> a single self-contained navigator page.

usage: build_page.py MAP TEMPLATE OUT_HTML
"""
import json
import sys
from pathlib import Path


def main(map_p, template_p, out_p):
    data = json.loads(Path(map_p).read_text())
    run = Path(map_p).with_name("run.json")
    if run.exists():
        data.update(json.loads(run.read_text()))
    # compact, and make it safe inside <script>: no "</" sequences
    blob = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = Path(template_p).read_text().replace("__DATA__", blob, 1)
    Path(out_p).parent.mkdir(parents=True, exist_ok=True)
    Path(out_p).write_text(html)
    print(f"wrote {out_p} ({len(html) // 1024} KB)")


if __name__ == "__main__":
    main(*sys.argv[1:])
