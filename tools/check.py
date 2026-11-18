#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["pydantic>=2.7"]
# ///
"""Gate for a built site (DESIGN.md backlog P0 #2). Usage: uv run tools/check.py [_site]

Exits non-zero on: missing expected files, leftover {{placeholders}}, broken internal links,
any third-party origin loaded by a page, budget overruns, hand-typed numbers in the home page
copy, or MCP reference drift.
"""

from __future__ import annotations

import hashlib
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from models import CorpusFile, Manifest, McpSchemaFile, WsProtocol  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = ["index.html", "404.html", "websocket/index.html", "examples/index.html", "ai/index.html",
            "mcp/index.html", "llms.txt", "llms-ctx.txt", "llms-full.txt", "ai/corpus.json",
            "websocket/protocol.json", "mcp/schema.json", "mcp/server.json", "mcp/index.md",
            "sitemap.xml", "robots.txt", "CNAME"]
BUDGET_KB = {"llms-ctx.txt": 300, "assets/fonts": 160, "index.html": 120}
# Words in the home copy that contain digits but are names, not figures.
DIGIT_OK = {"v5", "10m", "10-minute", "c++", "404"}


LOAD_RELS = {"stylesheet", "preload", "icon", "modulepreload", "preconnect"}


def attr(attrs: list[tuple[str, str | None]], name: str) -> str:
    """An HTML attribute's value, "" when absent or valueless (the last one wins, as in dict(attrs))."""
    found = ""
    for k, v in attrs:
        if k == name:
            found = v or ""
    return found


class Refs(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.loads: list[str] = []
        self.links: list[str] = []
        self.text: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        src, href = attr(attrs, "src"), attr(attrs, "href")
        if tag in ("style", "script"):
            self._skip += 1
            if tag == "script" and src:
                self.loads.append(src)
        if tag in ("img", "iframe", "source", "video", "audio") and src:
            self.loads.append(src)
        if tag == "link" and href and set(attr(attrs, "rel").split()) & LOAD_RELS:
            self.loads.append(href)
        if tag == "a" and href:
            self.links.append(href)
        for v in (src, href):
            if tag != "a" and v.startswith("/"):
                self.links.append(v)

    def handle_endtag(self, tag: str) -> None:
        if tag in ("style", "script"):
            self._skip -= 1

    def handle_data(self, data: str) -> None:
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
        tools = {t.name for t in McpSchemaFile.model_validate_json((site / "mcp/schema.json").read_text()).tools}
        cards = set(re.findall(r'<article class="tool" id="([a-z_]+)"', (site / "mcp/index.html").read_text()))
        if tools != cards:
            errs.append(f"mcp: reference cards differ from schema.json: {sorted(tools ^ cards)}")
        for t in tools:
            if not (site / f"mcp/tools/{t}.json").exists():
                errs.append(f"mcp: missing /mcp/tools/{t}.json")

    # llms.txt link hygiene
    llms = (site / "llms.txt").read_text() if (site / "llms.txt").exists() else ""
    n_links = len(re.findall(r"^- \[", llms, re.M))
    if n_links > 80:
        errs.append(f"llms.txt has {n_links} links (> 80)")
    for m in re.finditer(r"^- \[[^\]]+\]\([^)]+\): (.*)$", llms, re.M):
        if re.fullmatch(r"[\w./-]+\.(md|rst)", m[1].strip()):
            errs.append(f"llms.txt: description is a file path: {m[1]}")

    # corpus v2: schema, unique ids, one typed chunk per protocol item, prose chunk sizes
    cj = site / "ai/corpus.json"
    if cj.exists():
        c = CorpusFile.model_validate_json(cj.read_text())
        if c.schema_version != 2:
            errs.append("corpus.json: schema_version != 2")
        ids = [x.id for x in c.chunks]
        if len(ids) != len(set(ids)):
            errs.append("corpus.json: duplicate chunk ids")
        proto = WsProtocol.model_validate_json((site / "websocket/protocol.json").read_text())
        expected = {"ws-request": {f"ws:request:{r.requestType}" for r in proto.requests},
                    "ws-event": {f"ws:event:{e.eventType}" for e in proto.events},
                    "ws-enum": {f"ws:enum:{en.enumType}" for en in proto.enums}}
        for kind, want in expected.items():
            got = {x.id for x in c.chunks if x.kind == kind}
            if want != got:
                errs.append(f"corpus.json: {kind} chunks differ from protocol.json: {sorted(want ^ got)[:5]}")
        for x in c.chunks:
            if x.kind == "prose" and x.chars > 2400 and "```" not in x.text and "\n|" not in x.text:
                errs.append(f"corpus.json: prose chunk {x.id} is {x.chars} chars (> 2400)")

    # hero is the real application, no invented scenes or animation loops (DESIGN.md P0 #3)
    home = (site / "index.html").read_text()
    for banned in ("Starting Soon", "BRB"):
        if banned in home:
            errs.append(f"index.html: invented scene name {banned!r} is back")
    for page in site.rglob("*.html"):
        if "requestAnimationFrame" in page.read_text():
            errs.append(f"{page.relative_to(site)}: requestAnimationFrame in a shipped page")
    hero = site / "assets/main-window.webp"
    if not hero.is_file() or hero.stat().st_size > 120_000:
        errs.append("assets/main-window.webp missing or over 120 KB")
    # every download link carries a full SHA-256 (DESIGN.md P0 #5)
    n_dl = home.count('class="sha"')
    if n_dl == 0 or n_dl != len(re.findall(r'<li><a href="https://github.com/obs-rust/obs-studio/releases/download/', home)):
        errs.append(f"index.html: {n_dl} SHA-256 lines do not match the download links")

    # agent router and manifest (DESIGN.md P0 #2)
    llms_text = (site / "llms.txt").read_text()
    router = re.findall(r"^- ([^:\n]+): \[(/[^\]]+)\]\(https://obs-rust\.com(/[^)]+)\) \((\d+) bytes\)$",
                        llms_text.split("## Feeds")[0], re.M)
    if len(router) < 8:
        errs.append(f"llms.txt: router has {len(router)} rows (< 8)")
    for task, label, path, size in router:
        f = site / path.lstrip("/")
        if label != path or not f.is_file():
            errs.append(f"router: {task}: {path} does not resolve")
        elif f.stat().st_size != int(size):
            errs.append(f"router: {path} is {f.stat().st_size} bytes, router says {size}")
    if "obs-rust.com/ai/docs/site-download.md" not in llms_text.split("## Feeds")[0]:
        errs.append("router: the download row does not point at obs-rust.com")
    man = Manifest.model_validate_json((site / "ai/manifest.json").read_bytes())
    on_disk = {p.name for p in (site / "ai/docs").glob("*.md")}
    listed = {f"{d.slug}.md" for d in man.docs}
    if on_disk != listed:
        errs.append(f"manifest.json: lists differ from /ai/docs: {sorted(on_disk ^ listed)[:5]}")
    for d in man.docs:
        f = site / "ai/docs" / f"{d.slug}.md"
        if f.is_file() and hashlib.sha256(f.read_bytes()).hexdigest() != d.sha256:
            errs.append(f"manifest.json: sha256 mismatch for {d.slug}.md")
    ctx = (site / "llms-ctx.txt").read_text()
    for need in ("site/download.md", "site/control.md", "site/examples.md"):
        if f"<!-- ===== {need} |" not in ctx:
            errs.append(f"llms-ctx.txt: missing {need}")

    for e in errs:
        print("FAIL", e)
    print(f"check: {len(errs)} problem(s) in {site}")
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
