"""Site documents for agents (DESIGN.md P0 #2): site/download.md, site/examples.md, site/control.md,
the task router, and /ai/manifest.json.

The three documents are core corpus docs: they enter llms-ctx.txt and corpus.json like any upstream
document, so an agent with only llms.txt can install, copy a checked example and choose an API.
"""

from __future__ import annotations

import hashlib
import html
import re
from dataclasses import dataclass, field
from collections.abc import Callable
from html.parser import HTMLParser
from pathlib import Path

from models import Channel, DownloadGroup, Manifest, ManifestDoc, RouterRow, Tier

SITE = "https://obs-rust.com"


# ---------------------------------------------------------------- HTML -> markdown (our own templates only)
@dataclass(slots=True)
class _MdState:
    out: list[str] = field(default_factory=lambda: [])
    buf: list[str] = field(default_factory=lambda: [])
    skip_tag: str | None = None
    skip_depth: int = 0
    lang: str = ""
    table_rows: list[str] = field(default_factory=lambda: [])
    card_href: str | None = None
    card_part: str = ""
    card_title: list[str] = field(default_factory=lambda: [])
    card_desc: list[str] = field(default_factory=lambda: [])
    in_pre: bool = False
    href: str | None = None
    link_text: list[str] = field(default_factory=lambda: [])
    tab_labels: list[str] = field(default_factory=lambda: [])
    in_tab_button: bool = False
    tab_button_text: list[str] = field(default_factory=lambda: [])
    div_classes: list[str] = field(default_factory=lambda: [])


LANGS = {"rust": "rust", "python": "python", "javascript": "js", "js": "js", "lua": "lua", "c": "c", "c++": "cpp"}


class _HtmlToMd(HTMLParser):
    """Converts the subset our page templates use: headings, paragraphs, lists, links, code, pre,
    tab sets (each pane is labelled with its tab) and `.dep` install lines."""

    SKIP = {"script", "style", "nav", "footer", "head", "svg"}
    BLOCK_END = {"p", "li", "h1", "h2", "h3", "h4"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.s = _MdState()

    def _flush(self, prefix: str = "") -> None:
        text = " ".join("".join(self.s.buf).split())
        self.s.buf.clear()
        if text:
            self.s.out.append(prefix + text)

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        a = {k: v or "" for k, v in attrs}
        cls = a.get("class", "")
        if self.s.skip_tag is not None:
            self.s.skip_depth += tag == self.s.skip_tag
            return
        if tag in self.SKIP or (tag == "span" and "eyebrow" in cls.split()):
            self.s.skip_tag, self.s.skip_depth = tag, 1
            return
        if self.s.card_href is not None:
            if tag in ("h3", "p"):
                self.s.card_part = tag
            elif tag == "span":
                self.s.skip_tag, self.s.skip_depth = "span", 1
            return
        if tag == "a" and "card" in cls.split():
            self._flush()
            self.s.card_href, self.s.card_part = a.get("href", ""), ""
            self.s.card_title.clear()
            self.s.card_desc.clear()
            return
        if tag == "pre":
            self._flush()
            self.s.in_pre = True
        elif tag == "button" and a.get("role") == "tab":
            self.s.in_tab_button = True
            self.s.tab_button_text.clear()
        elif tag == "div":
            self.s.div_classes.append(cls)
            if "pane" in cls.split() and self.s.tab_labels:
                self._flush()
                label = self.s.tab_labels.pop(0)
                self.s.lang = LANGS.get(label.lower(), "")
                self.s.out.append(f"**{label}**")
            elif "dep" in cls.split():
                self._flush()
                self.s.buf.append("Install: `")
        elif tag == "a" and not self.s.in_pre:
            self.s.href = a.get("href", "")
            self.s.link_text.clear()
        elif tag == "code" and not self.s.in_pre:
            self.s.buf.append("`")
        elif tag in ("td", "th"):
            self.s.buf.append(" | ")

    def handle_endtag(self, tag: str) -> None:
        if self.s.skip_tag is not None:
            self.s.skip_depth -= tag == self.s.skip_tag
            if self.s.skip_depth == 0:
                self.s.skip_tag = None
            return
        if self.s.card_href is not None:
            if tag == "a":
                href = self.s.card_href if self.s.card_href.startswith("http") else SITE + self.s.card_href
                title = " ".join("".join(self.s.card_title).split())
                desc = " ".join("".join(self.s.card_desc).split())
                self.s.out.append(f"- [{title}]({href})" + (f": {desc}" if desc else ""))
                self.s.card_href = None
            elif tag in ("h3", "p"):
                self.s.card_part = ""
            return
        if tag == "pre":
            self.s.out.append(f"```{self.s.lang}\n" + "".join(self.s.buf).strip("\n") + "\n```")
            self.s.buf.clear()
            self.s.in_pre = False
            self.s.lang = ""
        elif tag == "button" and self.s.in_tab_button:
            self.s.in_tab_button = False
            self.s.tab_labels.append(" ".join("".join(self.s.tab_button_text).split()))
        elif tag == "div":
            cls = self.s.div_classes.pop() if self.s.div_classes else ""
            if "dep" in cls.split():
                self.s.buf.append("`")
                self._flush()
        elif tag == "a" and self.s.href is not None:
            text = " ".join("".join(self.s.link_text).split())
            href = self.s.href if self.s.href.startswith(("http", "mailto:")) else SITE + self.s.href
            self.s.buf.append(f"[{text}]({href})" if text else "")
            self.s.href = None
        elif tag == "code" and not self.s.in_pre:
            self.s.buf.append("`")
        elif tag == "tr":
            cells = " ".join("".join(self.s.buf).split())
            self.s.buf.clear()
            self.s.table_rows.append(cells.lstrip("| ").join(("| ", " |")))
        elif tag == "table":
            rows = self.s.table_rows
            if rows:
                sep = "|" + "---|" * rows[0].count(" | ") + "---|"
                self.s.out.append("\n".join([rows[0], sep, *rows[1:]]))
            self.s.table_rows = []
        elif tag in ("h1", "h2", "h3", "h4"):
            self._flush("#" * (int(tag[1]) + 1) + " ")
        elif tag in self.BLOCK_END:
            self._flush("- " if tag == "li" else "")

    def handle_data(self, data: str) -> None:
        if self.s.skip_tag is not None:
            return
        if self.s.card_href is not None:
            if self.s.card_part == "h3":
                self.s.card_title.append(data)
            elif self.s.card_part == "p":
                self.s.card_desc.append(data)
        elif self.s.in_tab_button:
            self.s.tab_button_text.append(data)
        elif self.s.href is not None:
            self.s.link_text.append(data)
        else:
            self.s.buf.append(data)

    def markdown(self) -> str:
        self._flush()
        return "\n\n".join(x for x in self.s.out if x.strip()) + "\n"


def html_to_md(page_html: str) -> str:
    m = re.search(r"<main[^>]*>(.*)</main>", page_html, re.S)
    p = _HtmlToMd()
    p.feed(m[1] if m else page_html)
    return p.markdown()


# ---------------------------------------------------------------- the three documents
def readme_section(readme: str, heading: str) -> str:
    """The README's top-level `# heading` section, up to the next top-level heading."""
    m = re.search(rf"^# {re.escape(heading)}\n(.*?)(?=^# |\Z)", readme, re.M | re.S)
    if not m:
        raise SystemExit(f"sitedocs: README has no '# {heading}' section")
    return re.sub(r"^## ", "### ", m[1].strip(), flags=re.M)


def download_md(chans: list[Channel], groups: tuple[DownloadGroup, ...], readme: str,
                human_size: Callable[[int], str]) -> str:
    out = ["# Download OBS Studio Rust", "",
           "Two channels. **Stable** is recommended; **Beta** is the newest build from master. Verify a download "
           "with `sha256sum <file>` (Linux), `shasum -a 256 <file>` (macOS) or `Get-FileHash <file>` "
           "(Windows PowerShell); it must equal the SHA-256 listed.", ""]
    for ch in chans:
        out += [f"## {ch.name}: {ch.rel.name or ch.rel.tag_name}", "",
                f"Tag `{ch.rel.tag_name}`, published {(ch.rel.published_at or '')[:10]}. {ch.note} "
                f"Release page: {ch.rel.html_url}", ""]
        for g in groups:
            rows: list[str] = []
            for opt in g.options:
                asset = next((x for x in ch.rel.assets if x.name.endswith(opt.suffix)), None)
                if asset is None:
                    continue
                rows.append(f"| {opt.label} | [{asset.name}]({asset.browser_download_url}) | "
                            f"{human_size(asset.size)} | `{ch.sums.by_name[asset.name]}` |")
            out += [f"### {g.os_name} ({g.arch})", "", "| Package | File | Size | SHA-256 |", "|---|---|---|---|",
                    *rows, ""]
    out += ["## Install notes (from the project README)", "", readme_section(readme, "Install"), ""]
    return "\n".join(out)


def control_md(n_requests: int, n_events: int, n_enums: int, n_tools: int, n_ro: int) -> str:
    return f"""# Control OBS Studio Rust from code: WebSocket or MCP

OBS Studio Rust can be driven two ways: obs-websocket from any machine that can reach OBS, or the MCP server
on the OBS machine itself (Linux).

## Choose

| You are writing | Use | Why |
|---|---|---|
| A tool, bot, overlay, Stream Deck action or any existing obs-websocket client | **obs-websocket v5** | The standard OBS remote-control protocol: {n_requests} requests, {n_events} events, {n_enums} enums. Existing clients work unchanged. |
| An AI agent that should operate OBS through typed tools | **MCP server** | {n_tools} typed tools with JSON Schema arguments and results; {n_ro} are read-only. Errors are typed (`ToolError`) and `wait_for` blocks on a condition instead of polling. |

## obs-websocket v5

- Connect to `ws://<host>:4455`: the OBS machine itself or any host that can reach it (the port is set in
  Tools → WebSocket Server Settings). A WebSocket client may run remotely.
- Handshake: the server sends `Hello` (op 0); you reply `Identify` (op 1) with `rpcVersion: 1` and, if a
  password is set, `authentication = base64(sha256(base64(sha256(password + salt)) + challenge))`; the server
  answers `Identified` (op 2). Then send `Request` (op 6) messages and read `RequestResponse` (op 7).
- First request: `{{"op":6,"d":{{"requestType":"GetVersion","requestId":"1"}}}}`.
- Full reference: {SITE}/websocket/ (browsable, with a live console),
  {SITE}/websocket/protocol.json (machine-readable spec),
  {SITE}/ai/docs/obs-websocket-reference.md (markdown, one section per request).
- Client libraries and runnable snippets: {SITE}/ai/docs/site-examples.md.

## MCP server

- Linux only for now: the server is built from an obs-studio checkout and runs on Linux. It is local: it runs on
  the OBS machine, next to the agent.
- The server speaks JSON-RPC over stdio (MCP protocol 2025-06-18). Client config, requirements and
  example sessions: {SITE}/mcp/index.md.
- Tool list without starting the server: {SITE}/mcp/schema.json (tools/list + resources/list + ToolError).
- A read-only allowlist for cautious clients: {SITE}/mcp/read-only-allowlist.json.
"""


def examples_md(template_html: str) -> str:
    """From src/examples.html: <main> holds no placeholders, so the raw template converts directly."""
    body = html_to_md(template_html)
    return ("# Examples: drive OBS Studio Rust from code\n\n"
            f"Generated from {SITE}/examples/. Every snippet targets obs-websocket v5 on `ws://localhost:4455` "
            "unless it says MCP.\n\n" + body)


# ---------------------------------------------------------------- router and manifest
ROUTER: tuple[tuple[str, str], ...] = (
    ("Install and verify the download", "/ai/docs/site-download.md"),
    ("Choose WebSocket or MCP and connect", "/ai/docs/site-control.md"),
    ("Copy a working client snippet", "/ai/docs/site-examples.md"),
    ("Look up an obs-websocket request, event or enum", "/ai/docs/obs-websocket-reference.md"),
    ("Machine-readable obs-websocket spec", "/websocket/protocol.json"),
    ("Control OBS from an agent (MCP)", "/mcp/index.md"),
    ("MCP tools/list without starting the server", "/mcp/schema.json"),
    ("Write a native plugin (libobs C API)", "/ai/docs/docs-sphinx-plugins.md"),
    ("Contribute to the port", "/ai/docs/agents.md"),
    ("Everything core in one context window", "/llms-ctx.txt"),
    ("Retrieval: typed chunks with breadcrumbs", "/ai/corpus.json"),
    ("Every document with its SHA-256", "/ai/manifest.json"),
)


def router_rows(out: Path) -> list[RouterRow]:
    rows: list[RouterRow] = []
    for task, path in ROUTER:
        f = out / path.lstrip("/")
        if not f.is_file():
            raise SystemExit(f"router: {path} is not in the built site")
        rows.append(RouterRow(task=task, path=path, bytes=f.stat().st_size))
    return rows


def router_llms(rows: list[RouterRow]) -> list[str]:
    return ["## Router", "Task → the one file to fetch first (exact size in bytes).", ""] + [
        f"- {r.task}: [{r.path}]({SITE}{r.path}) ({r.bytes} bytes)" for r in rows] + [""]


def router_html(rows: list[RouterRow]) -> str:
    return "".join(
        f'<tr><td>{html.escape(r.task)}</td><td><a href="{html.escape(r.path)}"><code>{html.escape(r.path)}</code></a>'
        f'</td><td class="n">{r.bytes / 1024:.1f} KB</td></tr>' for r in rows)


def manifest(docs: list[ManifestDoc], generated: str, obs_sha: str, ws_sha: str) -> Manifest:
    return Manifest(schema_version=1, generated=generated, obs_studio_commit=obs_sha, obs_websocket_commit=ws_sha,
                    docs=docs)


def manifest_doc(out: Path, slug: str, path: str, title: str, tier: Tier, group: str, source: str) -> ManifestDoc:
    f = out / "ai" / "docs" / f"{slug}.md"
    data = f.read_bytes()
    return ManifestDoc(slug=slug, path=path, title=title, tier=tier, group=group, url=f"{SITE}/ai/docs/{slug}.md",
                       source=source, bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
