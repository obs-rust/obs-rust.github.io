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
from models import (CorpusFile, DisclosureArchives, Manifest, McpSchemaFile, PublishedFile, ReplayInline,  # noqa: E402
                    WsProtocol)

ROOT = Path(__file__).resolve().parent.parent
EXPECTED = ["index.html", "404.html", "websocket/index.html", "examples/index.html", "ai/index.html",
            "mcp/index.html", "llms.txt", "llms-ctx.txt", "llms-full.txt", "ai/corpus.json",
            "websocket/protocol.json", "mcp/schema.json", "mcp/server.json", "mcp/index.md",
            "sitemap.xml", "robots.txt", "CNAME", "security/index.html", "security/advisories.json"]
BUDGET_KB = {"llms-ctx.txt": 300, "assets/fonts": 160, "index.html": 120}
# Words in the home copy that contain digits but are names, not figures.
DIGIT_OK = {"v5", "10m", "10-minute", "c++", "404", "sha256sums"}


# DESIGN.md §6: the type scale and radii, as tokens in site.css (--t-*, --r-*); pages name them, never a literal.
SCALE = (12, 13, 15, 17, 19, 22, 30, 40, 52, 72, 96)
RADII = {"r-ctl": "4px", "r-plate": "6px", "r-light": "50%"}
SIZED_UNIT = re.compile(r"(?<![\w-])\d*\.?\d+(?:px|em|rem|vw|vh|ch|%)")


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
        cards = set(re.findall(r'<details class="tool"[^>]*><summary id="([a-z_]+)"', (site / "mcp/index.html").read_text()))
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
        bad_url = [x.id for x in c.chunks if not x.url.startswith("https://")]
        if bad_url:
            errs.append(f"corpus.json: {len(bad_url)} chunk urls are not absolute, e.g. {bad_url[0]}")
        no_anchor = [x.id for x in c.chunks if x.kind == "prose" and "#" not in x.url]
        if no_anchor:
            errs.append(f"corpus.json: {len(no_anchor)} prose chunk urls have no #anchor, e.g. {no_anchor[0]}")
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
    errs.extend(check_finish(site))
    # every download link carries a full SHA-256 (DESIGN.md P0 #5)
    n_dl = home.count('class="sha"')
    if n_dl == 0 or n_dl != len(re.findall(r'<li><a href="https://github.com/obs-rust/obs-studio/releases/download/', home)):
        errs.append(f"index.html: {n_dl} SHA-256 lines do not match the download links")

    # stable and beta channels, each with 3+ hashed files; limits quoted with a README receipt (P0 #5, #8)
    chans = re.findall(r'<(?:div|details) class="chan" id="([a-z]+)">(.*?)(?=<(?:div|details) class="chan"|<div class="limits)', home, re.S)
    if {c for c, _ in chans} != {"stable", "beta"}:
        errs.append(f"index.html: download channels are {[c for c, _ in chans]}, want stable and beta")
    for name, body in chans:
        if body.count('class="sha"') < 3:
            errs.append(f"index.html: {name} channel lists fewer than 3 hashed files")
    if len(re.findall(r'href="https://github.com/obs-rust/obs-studio/blob/[0-9a-f]{40}/README.md#L\d+"', home)) < 3:
        errs.append("index.html: fewer than 3 limits with a commit-pinned README receipt")

    # nothing broken on any page (DESIGN.md P0 #17a): static guards for what the Chromium probe measures
    css_sources = [(site / "assets/site.css").read_text()] + [
        m for page in site.rglob("*.html") for m in re.findall(r"<style>(.*?)</style>", page.read_text(), re.S)]
    for css in css_sources:
        for m in re.finditer(r"(?:font:\s*(?:\d{3}\s+)?|font-size:\s*)(\d+(?:\.\d+)?)px", css):
            if float(m[1]) < 12:
                errs.append(f"css: font size {m[1]}px under the 12 px floor: {m[0]!r}")
    if ":focus-visible" not in (site / "assets/site.css").read_text():
        errs.append("site.css: no :focus-visible style")
    for page in sorted(site.rglob("*.html")):
        text = page.read_text()
        rel = page.relative_to(site)
        if len(re.findall(r"<h1[\s>]", text)) != 1:
            errs.append(f"{rel}: not exactly one h1")
        levels = [int(x) for x in re.findall(r"<h([1-6])[\s>]", re.sub(r"<script.*?</script>", "", text, flags=re.S))]
        for prev, cur in zip(levels, levels[1:]):
            if cur > prev + 1:
                errs.append(f"{rel}: heading skips h{prev} -> h{cur}")
                break
        for m in re.finditer(r"(.{0,40})<table\b", text, re.S):
            if not re.search(r'class="(tw|tblwrap)"[^>]*>\s*$', m[1]):
                errs.append(f"{rel}: a <table> outside a scroll wrapper (.tw)")
                break

    errs.extend(check_one_system(site))
    errs.extend(check_object_first(site))
    errs.extend(check_replay(site))
    errs.extend(check_security(site))

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


def check_one_system(site: Path) -> list[str]:
    """S1 (DESIGN.md §6, backlog #26): one type scale, one set of radii, one measure, as tokens."""
    errs: list[str] = []
    css = (site / "assets/site.css").read_text()
    tokens = {int(a): int(b) for a, b in re.findall(r"--t-(\d+):\s*(\d+)px", css)}
    if set(tokens) != set(SCALE) or any(a != b for a, b in tokens.items()):
        errs.append(f"site.css: --t-* tokens {sorted(tokens.items())} are not the scale {list(SCALE)}")
    for name, value in RADII.items():
        if not re.search(rf"--{name}:\s*{re.escape(value)}[;}}]", css):
            errs.append(f"site.css: no --{name}:{value} token")
    if not re.search(r"--measure:\s*40em", css) or not re.search(r"(?:^|})\s*p,\s*li\{max-width:var\(--measure\)", css, re.M):
        errs.append("site.css: body text is not held to --measure (40em) by a p,li rule")
    sources = [("assets/site.css", css)]
    for page in sorted(site.rglob("*.html")):
        rel = str(page.relative_to(site))
        text = re.sub(r"<script.*?</script>", "", page.read_text(), flags=re.S)
        sources += [(rel, m) for m in re.findall(r"<style>(.*?)</style>", text, re.S)]
        sources += [(f"{rel} style=", m) for m in re.findall(r'\sstyle="([^"]*)"', text)]
        if rel != "404.html" and re.search(r"(?:^|[},\s])h1[^{}]*\{[^}]*font", "".join(re.findall(r"<style>(.*?)</style>", text, re.S))):
            errs.append(f"{rel}: the page restyles h1; h1 is one rule in site.css")
    for rel, src in sources:
        for m in re.finditer(r"(?<![\w-])font(?:-size)?\s*:\s*([^;}\"]+)", src):
            value = re.sub(r"/\s*\S+", "", m[1])  # drop the line-height of a font shorthand
            if SIZED_UNIT.search(value) or ("var(--t-" not in value and value.strip() != "inherit"):
                errs.append(f"{rel}: font size is not a --t-* token: {m[0].strip()!r}")
        for m in re.finditer(r"border(?:-(?:top|bottom)-(?:left|right))?-radius\s*:\s*([^;}\"]+)", src):
            parts = re.findall(r"var\([^)]*\)|\S+", m[1].strip())
            if any(part != "0" and not part.startswith("var(--r-") for part in parts):
                errs.append(f"{rel}: radius is not a --r-* token: {m[0].strip()!r}")
    return errs


# DESIGN.md §6, §8, backlog #28: the second capture, the social card, no orphan assets, four motions
CARD = "assets/social-card.png"
SHOT = re.compile(r'<img src="/assets/gpu-usage-label-hw\.png"[^>]*>\s*<img class="i2" src="/assets/gpu-usage-label-sw\.png"'
                  r'.*?href="https://github\.com/obs-rust/obs-studio/blob/[0-9a-f]{40}/docs/gpu-status\.md#L\d+"', re.S)


def png_size(data: bytes) -> tuple[int, int]:
    """Width and height from a PNG's IHDR chunk, (0, 0) if it is not a PNG."""
    if data[:8] != b"\x89PNG\r\n\x1a\n" or data[12:16] != b"IHDR":
        return 0, 0
    return int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")


def check_finish(site: Path) -> list[str]:
    """S3: two real pictures with receipts on /, a 1200x630 og:image under 200 KB on every page, every shipped
    asset referenced, and motion only as §6 allows (one transition rule, at most 3 @keyframes, 1 repeating)."""
    errs: list[str] = []
    home = (site / "index.html").read_text() if (site / "index.html").is_file() else ""
    for name in ("gpu-usage-label-hw.png", "gpu-usage-label-sw.png"):
        shot = site / "assets" / name
        if not shot.is_file() or shot.stat().st_size > 120_000:
            errs.append(f"assets/{name} missing or over 120 KB")
    if "mockup" in home.lower():
        errs.append("index.html: a picture on / is labelled a mockup; D1 wants captures of the running program")
    if not SHOT.search(home):
        errs.append("index.html: the GPU status captures lack their receipt pinned to a commit and line")
    card = site / CARD
    data = card.read_bytes() if card.is_file() else b""
    if png_size(data) != (1200, 630) or len(data) > 200_000:
        errs.append(f"{CARD}: {png_size(data)} and {len(data)} bytes, want a 1200x630 PNG under 200 KB")
    pages = sorted(site.rglob("*.html"))
    for page in pages:
        text = page.read_text()
        for prop, want in (("og:image", f"https://obs-rust.com/{CARD}"), ("og:image:width", "1200"),
                           ("og:image:height", "630")):
            if f'<meta property="{prop}" content="{want}">' not in text:
                errs.append(f"{page.relative_to(site)}: {prop} is not {want}")
        if "@keyframes" in text:
            errs.append(f"{page.relative_to(site)}: its own @keyframes; motion lives in site.css")
    refs = "".join(p.read_text() for p in pages) + "".join(p.read_text() for p in (site / "assets").rglob("*.css"))
    for f in sorted((site / "assets").rglob("*")):
        if f.is_file() and f"/assets/{f.relative_to(site / 'assets')}" not in refs:
            errs.append(f"assets/{f.relative_to(site / 'assets')}: shipped but nothing references it")
    css = (site / "assets/site.css").read_text()
    shared = re.search(r"(?:^|})\s*a,button,summary[^{]*\{transition:([^}]*)\}", css, re.M)
    durations = [float(x) for x in re.findall(r"(\d*\.?\d+)s\b", shared[1])] if shared else []
    if not durations or any(not 0.12 <= d <= 0.18 for d in durations):
        errs.append("site.css: no shared a,button,summary transition of 120 to 180 ms")
    if css.count("@keyframes") > 3 or css.count("infinite") > 1:
        errs.append(f"site.css: {css.count('@keyframes')} @keyframes (at most 3), {css.count('infinite')} infinite (at most 1)")
    if not re.search(r"prefers-reduced-motion:\s*reduce\)\{\*,\*::before,\*::after\{animation:none!important;"
                     r"transition:none!important\}", css):
        errs.append("site.css: motion is not switched off under prefers-reduced-motion")
    return errs


# DESIGN.md §5: the one object each page opens on
OBJECT_PAGES = ("index.html", "websocket/index.html", "examples/index.html", "ai/index.html", "mcp/index.html",
                "security/index.html")
HASH_OPENER = re.compile(r"addEventListener\(['\"]hashchange['\"]")


def opened(text: str, cls: str) -> bool:
    """Whether any <details class="cls"> carries the open attribute (attribute values stripped first)."""
    for attrs in re.findall(rf'<details class="{cls}"((?:\s+[\w-]+(?:="[^"]*")?)*)\s*>', text):
        if re.search(r"\sopen(?:\s|=|$)", re.sub(r'="[^"]*"', "", attrs)):
            return True
    return False


def check_object_first(site: Path) -> list[str]:
    """S2 (DESIGN.md §5, §8, backlog #27): each page marks one object; long references are closed entries whose
    summary carries the anchor, and a #Name link opens its entry."""
    errs: list[str] = []
    for rel in OBJECT_PAGES:
        f = site / rel
        n = len(re.findall(r"<[a-z]+\b[^>]*\sdata-object[\s>=]", f.read_text())) if f.is_file() else 0
        if n != 1:
            errs.append(f"{rel}: {n} elements marked data-object, want exactly 1")
    ws, mcp = site / "websocket/index.html", site / "mcp/index.html"
    if ws.is_file() and (site / "websocket/protocol.json").is_file():
        text = ws.read_text()
        proto = WsProtocol.model_validate_json((site / "websocket/protocol.json").read_text())
        names = [r.requestType for r in proto.requests] + [e.eventType for e in proto.events] + [x.enumType for x in proto.enums]
        anchored = set(re.findall(r'<details class="it"[^>]*><summary id="([A-Za-z]+)">', text))
        missing = [x for x in names if x not in anchored]
        if missing:
            errs.append(f"websocket: {len(missing)} entries are not a <details> whose summary carries the id, e.g. {missing[0]}")
        if opened(text, "it"):
            errs.append("websocket: a reference entry is open by default")
    if mcp.is_file() and opened(mcp.read_text(), "tool"):
        errs.append("mcp: a tool entry is open by default")
    for f in (ws, mcp):
        if f.is_file() and not HASH_OPENER.search(f.read_text()):
            errs.append(f"{f.relative_to(site)}: no hashchange handler to open the entry a #Name link points at")
    exf = site / "examples/index.html"
    if exf.is_file():
        obj = re.search(r"<(\w+)\b[^>]*\sdata-object[\s>=][^>]*>(.*?)</pre>", exf.read_text(), re.S)
        if obj is None or "<h2" in obj[2]:
            errs.append("examples: the data-object must be the code plate (a <pre> before any <h2>), not the prose block")
    for f in sorted(site.rglob("*.html")):
        if "runs unchanged against" in f.read_text():
            errs.append(f"{f.relative_to(site)}: claims examples 'run unchanged against' both OBS builds; say what is so per example")
    home = (site / "index.html").read_text() if (site / "index.html").is_file() else ""
    if '<div class="chan" id="stable">' not in home or '<details class="chan" id="beta">' not in home:
        errs.append("index.html: the stable files must stay open and the beta files close")
    return errs


REPLAY_OPS = (0, 2, 6, 7)  # Hello, Identified, Request, RequestResponse: what S4 looks for in #log
REPLAY_DATA = re.compile(r'<script type="application/json" id="replay-data">(.*?)</script>', re.S)


def check_replay(site: Path) -> list[str]:
    """S4 (DESIGN.md §9, backlog #29): /websocket/ inlines a scripted transcript that holds ops 0, 2, 6 and 7,
    labelled "scripted" with an obs-studio-rust-v* tag, never "recorded"."""
    f = site / "websocket/index.html"
    if not f.is_file():
        return []
    text = f.read_text()
    m = REPLAY_DATA.search(text)
    if m is None:
        return ["websocket: no inlined replay transcript (<script id=\"replay-data\">)"]
    rp = ReplayInline.model_validate_json(m.group(1))
    errs: list[str] = []
    ops = {r.op for r in rp.rows}
    if lack := [o for o in REPLAY_OPS if o not in ops]:
        errs.append(f"websocket: the replay transcript lacks ops {' '.join(map(str, lack))}")
    if not rp.tag.startswith("obs-studio-rust-v"):
        errs.append(f"websocket: the replay names {rp.tag!r}, not an obs-studio-rust-v* release")
    con = text[text.find('id="console"'):]
    con = con[:con.find("</section>")]
    if not re.search(r"scripted[^<\n]*" + re.escape(rp.tag), con):
        errs.append("websocket: the console does not label the replay scripted with its release tag")
    if re.search(r"\brecorded\b", con, re.I):
        errs.append("websocket: the console calls the scripted replay recorded")
    return errs


GHSA = re.compile(r"GHSA(?:-[23456789cfghjmpqrvwx]{4}){3}", re.I)
TEXT_SUFFIXES = {".html", ".txt", ".md", ".json", ".jsonl", ".xml", ".css", ".js"}
SECRET_NAME = re.compile(r"(?:^|[._-])(?:pass|password|passwd|pwd|secret|key)(?:$|[._-])|\.(?:pass|pwd|key|pem)$", re.I)
SECRET_TEXT = re.compile(r"\b(?:pass(?:word|phrase)?|pwd)\b\s*(?::|=|\bis\b)\s*[`'\"]?[A-Za-z0-9+/!#$%&*@^_~-]{8,}", re.I)
PRIVATE_NAMES = re.compile(r"(?:^|/)(?:README|manifest)[^/]*$|\.(?:pdf|patch)$", re.I)


def check_security(site: Path) -> list[str]:
    """/security/ publishes encrypted archives and aggregates only: each zip is byte-identical to
    security/archives.json, nothing from the private repository sits beside it, no file of the site names a GHSA
    id that is not in the published list, and nothing that looks like a password ships."""
    errs: list[str] = []
    page = site / "security/index.html"
    listing = site / "security/advisories.json"
    if not page.is_file() or not listing.is_file():
        return ["security: /security/ or /security/advisories.json is missing"]
    html = page.read_text()
    data = DisclosureArchives.model_validate_json((ROOT / "security/archives.json").read_bytes())
    zips = site / "security/archives"
    shipped = {p.name for p in zips.iterdir()} if zips.is_dir() else set[str]()
    if stray := sorted(shipped - {a.file for a in data.archives}):
        errs.append(f"security: files beside the archives that archives.json does not list: {stray}")
    for a in data.archives:
        f = zips / a.file
        body = f.read_bytes() if f.is_file() else b""
        if len(body) != a.size or hashlib.sha256(body).hexdigest() != a.sha256:
            errs.append(f"security: /security/archives/{a.file} is missing or differs from archives.json")
        if f'href="/security/archives/{a.file}"' not in html or a.sha256 not in html:
            errs.append(f"security: the page lacks the download link or SHA-256 of archive {a.number}")
    for f in sorted((site / "security").rglob("*")):
        rel = str(f.relative_to(site))
        if f.is_file() and PRIVATE_NAMES.search(rel):
            errs.append(f"security: {rel} looks like private-repository material (README, manifest, PDF, patch)")
    allowed = {p.ghsa_id.upper() for p in PublishedFile.model_validate_json(listing.read_bytes()).published}
    for f in sorted(site.rglob("*")):
        if not f.is_file():
            continue
        rel = str(f.relative_to(site))
        if SECRET_NAME.search(f.name):
            errs.append(f"security: {rel} is named like a secret")
        if f.suffix not in TEXT_SUFFIXES:
            continue
        text = f.read_text(errors="replace")
        if bad := sorted({g.upper() for g in GHSA.findall(text)} - allowed):
            errs.append(f"security: {rel} names {len(bad)} GHSA id(s) that are not published")
        if rel.startswith("security/") and SECRET_TEXT.search(text):
            errs.append(f"security: {rel} holds something that reads like a password")
    if SECRET_TEXT.search((ROOT / "security/archives.json").read_text()):
        errs.append("security: security/archives.json holds something that reads like a password")
    return errs


if __name__ == "__main__":
    sys.exit(main())
