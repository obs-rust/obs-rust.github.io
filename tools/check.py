#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Gate for a built site (DESIGN.md backlog P0 #2). Usage: uv run tools/check.py [_site]

Exits non-zero on: missing expected files, leftover {{placeholders}}, broken internal links,
any third-party origin loaded by a page, budget overruns, hand-typed numbers in the home page
copy, or MCP reference drift.
"""

from __future__ import annotations

import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = ["index.html", "404.html", "websocket/index.html", "examples/index.html", "ai/index.html",
            "mcp/index.html", "llms.txt", "llms-ctx.txt", "llms-full.txt", "ai/corpus.json",
            "websocket/protocol.json", "mcp/schema.json", "mcp/server.json", "mcp/index.md",
            "sitemap.xml", "robots.txt", "CNAME"]
BUDGET_KB = {"llms-ctx.txt": 300, "assets/fonts": 160, "index.html": 120}
# Words in the home copy that contain digits but are names, not figures.
DIGIT_OK = {"v5", "10m", "10-minute", "c++", "404"}


class Refs(HTMLParser):
    def __init__(self):
        super().__init__()
        self.loads, self.links, self.text, self._skip = [], [], [], 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("style", "script"):
            self._skip += 1
            if tag == "script" and a.get("src"):
                self.loads.append(a["src"])
        if tag in ("img", "iframe", "source", "video", "audio") and a.get("src"):
            self.loads.append(a["src"])
        if tag == "link" and a.get("href") and set((a.get("rel") or "").split()) & {"stylesheet", "preload", "icon",
                                                                                    "modulepreload", "preconnect"}:
            self.loads.append(a["href"])
        if tag == "a" and a.get("href"):
            self.links.append(a["href"])
        for k in ("src", "href"):
            if tag != "a" and a.get(k, "").startswith("/"):
                self.links.append(a[k])

    def handle_endtag(self, tag):
        if tag in ("style", "script"):
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self.text.append(data)


def main() -> int:
    site = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "_site").resolve()
    errs: list[str] = []
    for f in EXPECTED:
        if not (site / f).exists():
            errs.append(f"missing expected file: {f}")

    for page in sorted(site.rglob("*.html")):
        rel = page.relative_to(site)
        html = page.read_text()
        if "{{" in html:
            errs.append(f"{rel}: leftover {{{{placeholder}}}}")
        p = Refs()
        p.feed(html)
        for u in p.loads:
            if re.match(r"(https?:)?//", u) and not re.match(r"(https?:)?//(www\.)?obs-rust\.com/", u):
                errs.append(f"{rel}: loads third-party resource {u}")
        for u in p.links:
            if not u.startswith("/") or u.startswith("//"):
                continue
            path = u.split("#")[0].split("?")[0]
            t = site / path.lstrip("/")
            if not (t.exists() or (t / "index.html").exists()):
                errs.append(f"{rel}: broken internal link {u}")
        for m in re.finditer(r"fetch\(['\"](https?://[^'\"]+)", html):
            if "obs-rust.com" not in m[1]:
                errs.append(f"{rel}: fetches third-party {m[1]}")

    for path, kb in BUDGET_KB.items():
        t = site / path
        size = sum(f.stat().st_size for f in t.rglob("*")) if t.is_dir() else (t.stat().st_size if t.exists() else 0)
        if size > kb * 1024:
            errs.append(f"budget: {path} is {size / 1024:.0f} KB > {kb} KB")

    # no hand-typed numbers in the home page copy: figures must come from {{placeholders}}
    src = (ROOT / "src/index.html").read_text()
    src = re.sub(r"\{\{[^}]*\}\}", "", src)
    p = Refs()
    p.feed(src)
    for word in re.findall(r"[\w+.-]*\d[\w+.-]*", " ".join(p.text)):
        if word.lower().strip(".") not in DIGIT_OK:
            errs.append(f"src/index.html: hand-typed figure {word!r}; compute it in tools/build.py")

    # sitemap entries resolve
    sm = (site / "sitemap.xml").read_text() if (site / "sitemap.xml").exists() else ""
    for loc in re.findall(r"<loc>https://obs-rust\.com(/[^<]*)</loc>", sm):
        t = site / loc.lstrip("/")
        if not (t.exists() or (t / "index.html").exists()):
            errs.append(f"sitemap: {loc} does not exist")

    # MCP reference matches the published schema
    if (site / "mcp/schema.json").exists():
        tools = {t["name"] for t in json.loads((site / "mcp/schema.json").read_text())["tools"]}
        cards = set(re.findall(r'<article class="tool" id="([a-z_]+)"', (site / "mcp/index.html").read_text()))
        if tools != cards:
            errs.append(f"mcp: reference cards differ from schema.json: {sorted(tools ^ cards)}")
        for t in tools:
            if not (site / f"mcp/tools/{t}.json").exists():
                errs.append(f"mcp: missing /mcp/tools/{t}.json")

    # llms.txt link hygiene
    llms = (site / "llms.txt").read_text() if (site / "llms.txt").exists() else ""
    n_links = len(re.findall(r"^- \[", llms, re.M))
    if n_links > 130:
        errs.append(f"llms.txt has {n_links} links (> 130)")

    for e in errs:
        print("FAIL", e)
    print(f"check: {len(errs)} problem(s) in {site}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
