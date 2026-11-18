"""AI corpus v2 (DESIGN.md §7): tiers, structure-aware chunks, typed chunks, llms.txt v2.

A doc is models.Doc; a chunk is models.Chunk, whose "text" opens with its breadcrumb so it
stands alone.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import re
from collections.abc import Callable

from models import Chunk, ChunkKind, Doc, FieldRow, Feed, JsonSchema, LedgerItem, Surface, Tier, WsProtocol

SCHEMA_VERSION = 2
MIN_CHARS, TARGET_MAX, HARD_MAX = 300, 2000, 2400
ARCHIVE = re.compile(r"(\d{4}-\d{2}-\d{2}|-\d{3,}\.md$|retrospective|handoff|hall-of-fame|audit)")
CORE_PATHS = {"README.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md", "mcp/reference.md", "CODESTYLE.md",
              "CONSTITUTION.md", "site/download.md", "site/control.md", "site/examples.md",
              "obs-websocket/docs/generated/protocol.md", "docs/rust-port/mcp.md", "docs/rust-port/control-api.md"}
# Docs fully represented by typed chunks: their prose is not chunked a second time.
TYPED_DOCS = {"obs-websocket/reference.md", "mcp/reference.md", "docs/features.md"}


def tier(path: str) -> Tier:
    if path in CORE_PATHS:
        return "core"
    if ARCHIVE.search(path.rsplit("/", 1)[-1]):
        return "archive"
    if path.startswith(("docs/sphinx/", "obs-websocket/")) or path in {"BUILD.md", "docs/features.md"}:
        return "reference"
    return "process"


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")[:80]


def tokens_est(s: str) -> int:
    return max(1, round(len(s) / 4))


def _record(cid: str, doc: Doc, kind: ChunkKind, crumb: list[str], url: str, source: str, body: str) -> Chunk:
    head = " › ".join(c for c in crumb if c)
    text = f"[{head}]\n{body.strip()}" if head else body.strip()
    return Chunk(id=cid, doc=doc.slug, group=doc.group, tier=doc.tier, kind=kind, breadcrumb=crumb, url=url,
                 source=source, text=text, chars=len(text), tokens_est=tokens_est(text),
                 sha256=hashlib.sha256(text.encode()).hexdigest())


# ---------------------------------------------------------------- prose
def gh_anchor(heading: str) -> str:
    """GitHub's markdown heading anchor (before de-duplication)."""
    t = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", heading)
    t = re.sub(r"<[^>]+>", "", t).strip().lower()
    t = re.sub(r"[^\w\- ]", "", t)
    return t.replace(" ", "-")


def _sections(text: str, rst: bool = False) -> list[tuple[list[str], str, str]]:
    """Split markdown on headings outside fences; return (heading path, body, anchor) in order. Anchors
    are counted over every heading (h1-h6) in document order, as GitHub de-duplicates them; GitHub's
    RST renderer uses the same slug rule but does not add duplicate suffixes."""
    out: list[tuple[list[str], str, str]] = []
    path: list[str] = []
    buf: list[str] = []
    anchor = "top"
    used: dict[str, int] = {}
    fence = False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
        h = None if fence else re.match(r"^(#{1,6})\s+(.+?)\s*#*\s*$", line)
        m = h if h and len(h[1]) <= 4 else None
        if h:
            base = gh_anchor(h[2])
            n = used.get(base, 0)
            used[base] = n + 1
            this_anchor = base if (n == 0 or rst) else f"{base}-{n}"
        else:
            this_anchor = anchor
        if m:
            if "\n".join(buf).strip():
                out.append((list(path), "\n".join(buf), anchor))
            lvl = len(m[1])
            path = path[: lvl - 1] + [""] * max(0, lvl - 1 - len(path))
            path = path[: lvl - 1] + [re.sub(r"`|\*\*", "", m[2]).strip()]
            anchor = this_anchor or "top"
            buf = []
        else:
            buf.append(line)
    if "\n".join(buf).strip():
        out.append((list(path), "\n".join(buf), anchor))
    return out


_MD_IMAGE_LINK = re.compile(r"\[!\[[^\]]*\]\([^)]*\)\]\([^)]*\)")
_MD_IMAGE = re.compile(r"!\[[^\]]*\]\([^)]*\)")
_HTML_TAG = re.compile(r"</?(?:p|img|div|picture|source|br|a|sub|sup|span|center|kbd|details|summary)\b[^>]*>", re.I)


def strip_markup(text: str) -> str:
    """Drop badges, images and HTML tags from prose outside code fences; keep the words."""
    out: list[str] = []
    for i, part in enumerate(re.split(r"(```.*?```)", text, flags=re.S)):
        if i % 2:
            out.append(part)
            continue
        part = _MD_IMAGE_LINK.sub("", part)
        part = _MD_IMAGE.sub("", part)
        part = _HTML_TAG.sub("", part)
        out.append(re.sub(r"\n{3,}", "\n\n", part))
    return "".join(out)


def anchored_url(doc: Doc, anchor: str, site: str) -> str:
    """Absolute URL of a prose section: the GitHub source pinned to the commit when the doc lives
    there, else the doc's page on this site; always with a fragment."""
    # GitHub-hosted docs: the pinned source renders the anchor; this site's own docs: their markdown twin
    base = doc.source if doc.source.startswith("https://github.com/") else site + doc.site_url
    return f"{base.split('#')[0]}#{anchor}"


def _blocks(body: str) -> list[str]:
    """Paragraph blocks; a fenced block or a table is one unbreakable block."""
    blocks: list[str] = []
    cur: list[str] = []
    fence = False
    for line in body.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
        if not fence and not line.strip():
            if cur:
                blocks.append("\n".join(cur))
                cur = []
            continue
        cur.append(line)
    if cur:
        blocks.append("\n".join(cur))
    return blocks


def _split_long(block: str) -> list[str]:
    if len(block) <= HARD_MAX or block.lstrip().startswith(("```", "~~~", "|")):
        return [block]
    parts = re.split(r"(?m)^(?=\s*[-*] |\s*\d+\. )", block) if re.search(r"(?m)^\s*[-*] ", block) else \
        re.split(r"(?<=[.!?])\s+", block)
    out: list[str] = []
    cur = ""
    for p in parts:
        if cur and len(cur) + len(p) > TARGET_MAX:
            out.append(cur)
            cur = ""
        cur += p if not cur else ("" if p.startswith(("\n", " ")) else " ") + p
    if cur:
        out.append(cur)
    final: list[str] = []
    for o in out:  # a list item or line can still be too long: fall back to sentences, then lines
        if len(o) > HARD_MAX and o is not block:
            final += _split_long(o)
        elif len(o) > HARD_MAX:
            final += [o[i:i + TARGET_MAX] for i in range(0, len(o), TARGET_MAX)]
        else:
            final.append(o)
    return final


def prose_chunks(doc: Doc, title: str, site: str = "https://obs-rust.com") -> list[Chunk]:
    secs = _sections(strip_markup(doc.text), rst=doc.path.endswith(".rst"))
    # merge tiny sections into the previous one (sibling or parent)
    merged: list[tuple[list[str], str, str]] = []
    for path, body, anc in secs:
        if merged and len(body.strip()) < MIN_CHARS:
            ppath, pbody, panc = merged[-1]
            hdr = "#" * max(1, len([p for p in path if p])) + " " + (path[-1] if path else "")
            merged[-1] = (ppath, pbody.rstrip() + "\n\n" + (hdr + "\n" if path else "") + body.strip(), panc)
        else:
            merged.append((path, body, anc))
    # a short opening section has nothing before it: fold it forward into the next one
    while len(merged) > 1 and len(merged[0][1].strip()) < MIN_CHARS:
        (p0, b0, a0), (p1, b1, _a1) = merged[0], merged[1]
        hdr = "#" * max(1, len([p for p in p1 if p])) + " " + (p1[-1] if p1 else "")
        merged[:2] = [(p0, b0.rstrip() + "\n\n" + hdr + "\n" + b1.strip(), a0)]
    out: list[Chunk] = []
    seen: dict[str, int] = {}
    for path, body, anc in merged:
        pieces: list[str] = []
        cur = ""
        for b in _blocks(body):
            for piece in _split_long(b):
                if cur and len(cur) + len(piece) > TARGET_MAX:
                    pieces.append(cur)
                    cur = ""
                cur += ("\n\n" if cur else "") + piece
        if cur.strip():
            if pieces and len(cur) < MIN_CHARS and len(pieces[-1]) + len(cur) <= HARD_MAX:
                pieces[-1] += "\n\n" + cur
            else:
                pieces.append(cur)
        base = f"{doc.slug}#{slug('-'.join(p for p in path if p)) or 'top'}"
        for i, piece in enumerate(pieces):
            cid = base if i == 0 else f"{base}~{i + 1}"
            n = seen.get(cid, 0)
            seen[cid] = n + 1
            if n:
                cid += f"-{n + 1}"
            out.append(_record(cid, doc, "prose", [title] + [p for p in path if p and p != title],
                               anchored_url(doc, anc, site), doc.source, piece))
    return out


# ---------------------------------------------------------------- typed
def ws_chunks(doc: Doc, proto: WsProtocol, site: str) -> list[Chunk]:
    out: list[Chunk] = []
    for r in proto.requests:
        lines = [f"Request {r.requestType}: {r.description}",
                 f"Category {r.category}; since {r.initialVersion}; complexity {r.complexity}/5"
                 + ("; DEPRECATED" if r.deprecated else "") + "."]
        for label, fs in (("Request fields", r.requestFields), ("Response fields", r.responseFields)):
            if fs:
                lines.append(label + ":")
                lines += [f"- {f.valueName} ({f.valueType}{', optional' if f.valueOptional else ''}): "
                          f"{f.valueDescription}" for f in fs]
        out.append(_record(f"ws:request:{r.requestType}", doc, "ws-request",
                           ["obs-websocket v5", "Requests", r.category, r.requestType],
                           f"{site}/websocket/#{r.requestType}", doc.source, "\n".join(lines)))
    for e in proto.events:
        lines = [f"Event {e.eventType}: {e.description}",
                 f"Category {e.category}; subscription {e.eventSubscription}; since {e.initialVersion}."]
        lines += [f"- {f.valueName} ({f.valueType}): {f.valueDescription}" for f in e.dataFields]
        out.append(_record(f"ws:event:{e.eventType}", doc, "ws-event",
                           ["obs-websocket v5", "Events", e.category, e.eventType],
                           f"{site}/websocket/#{e.eventType}", doc.source, "\n".join(lines)))
    for en in proto.enums:
        lines = [f"Enum {en.enumType}:"] + [f"- {i.enumIdentifier} = {i.enumValue}: {i.description}"
                                            for i in en.enumIdentifiers]
        out.append(_record(f"ws:enum:{en.enumType}", doc, "ws-enum", ["obs-websocket v5", "Enums", en.enumType],
                           f"{site}/websocket/#{en.enumType}", doc.source, "\n".join(lines)))
    return out


FieldsRows = Callable[[JsonSchema, JsonSchema], list[FieldRow]]


def mcp_chunks(doc: Doc, surface: Surface, site: str, fields_rows: FieldsRows) -> list[Chunk]:
    out: list[Chunk] = []
    for t in surface.tools:
        lines = [f"MCP tool {t.name}: {t.description}",
                 f"Annotations: {json.dumps(t.annotations.model_dump(mode='json'))}"]
        for label, s in (("Arguments", t.inputSchema), ("Returns", t.outputSchema)):
            rows = fields_rows(s, s)
            if rows:
                lines.append(label + ":")
                lines += [f"- {r.name} ({r.type}{', required' if r.required else ''}): {r.description}"
                          for r in rows]
        out.append(_record(f"mcp:tool:{t.name}", doc, "mcp-tool", ["MCP server", "Tools", t.name],
                           f"{site}/mcp/#{t.name}", doc.source, "\n".join(lines)))
    for r in surface.resources:
        out.append(_record(f"mcp:resource:{r.uri}", doc, "mcp-resource", ["MCP server", "Resources", r.uri],
                           f"{site}/mcp/#resources", doc.source,
                           f"MCP resource {r.uri} ({r.mimeType}): {r.description}"))
    # the narrative part of the MCP page (setup, errors, sessions) stays as prose
    narrative = doc.text.split("\n## See tools")[0]
    tail = doc.text.split("\n## Resources", 1)[-1] if "\n## Resources" in doc.text else ""
    out += prose_chunks(dataclasses.replace(doc, text=narrative + "\n## Resources" + tail), "MCP server")
    return out


def ledger_chunks(doc: Doc, items: list[LedgerItem]) -> list[Chunk]:
    out: list[Chunk] = []
    seen: set[str] = set()
    md_link = re.compile(r"\[([^\]]+)\]\([^)]+\)")
    for it in items:
        txt = md_link.sub(r"\1", it.text)
        pr = re.search(r"/pull/(\d+)\)", it.text)
        key = f"ledger:{pr[1]}" if pr else f"ledger:{slug(txt[:50])}"
        while key in seen:
            key += "+"
        seen.add(key)
        kind: ChunkKind = "ledger-fix" if it.section == "Fixed upstream bugs" else "ledger-entry"
        url = (f"https://github.com/obs-rust/obs-studio/pull/{pr[1]}" if pr
               else anchored_url(doc, gh_anchor(it.area or it.section) or "top", "https://obs-rust.com"))
        out.append(_record(key, doc, kind, ["Features ledger", it.section, it.area], url, doc.source, txt))
    return out


# ---------------------------------------------------------------- llms.txt v2
LLMS_SECTIONS: list[tuple[str, Callable[[Doc], bool]]] = [
    ("Start here", lambda d: d.path in {"site/download.md", "site/control.md", "README.md", "AGENTS.md",
                                        "obs-websocket/docs/generated/protocol.md"}),
    ("Install and use", lambda d: d.path in {"docs/features.md", "docs/gpu-status.md", "SECURITY.md"}),
    ("Control OBS", lambda d: d.group in {"websocket", "mcp"} or d.path in {"site/examples.md", "docs/rust-port/mcp.md",
                                                                             "docs/rust-port/control-api.md"}),
    ("Extend OBS", lambda d: d.group == "libobs-api" and d.path.rsplit("/", 1)[-1] in {
        "plugins.rst", "scripting.rst", "reference-sources.rst", "reference-outputs.rst", "reference-encoders.rst",
        "reference-services.rst", "reference-frontend-api.rst", "graphics.rst", "reference-core.rst", "frontends.rst"}),
    ("Contribute", lambda d: d.path in {"CONTRIBUTING.md", "CONSTITUTION.md", "CODESTYLE.md", "BUILD.md", "docs/rust-port/coordination.md",
                                            "docs/rust-port/testing-policy.md", "docs/ci-tooling.md",
                                            "docs/knowledge/index.md", "docs/rust-port/naming.md"}),
]


SUMMARIES = {
    "obs-websocket/reference.md": "Every obs-websocket v5 request, event and enum with its fields, generated from "
                                  "protocol.json.",
    "mcp/reference.md": "Every MCP tool with arguments, returns and annotations, plus resources, errors and example "
                        "sessions, generated from the server's schema.",
}


def first_sentence(text: str, limit: int = 160) -> str:
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    for para in re.split(r"\n\s*\n", body):
        p = para.strip()
        if not p or p.startswith(("#", "<", "|", "[!", "!", "-", "*", ">", "..", ":", "=")) or len(p) < 30:
            continue
        p = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", " ".join(p.split()))
        p = re.sub(r"`|\*\*|(?<!\w)_|_(?!\w)", "", p)
        s = re.split(r"(?<=[.!?])\s", p)[0]
        return s if len(s) <= limit else s[: limit - 1].rsplit(" ", 1)[0] + "…"
    return ""


def llms_txt(docs: list[Doc], header: list[str], site: str, feeds: list[Feed],
             extra: dict[str, list[str]]) -> str:
    out = list(header)
    out.append("## Feeds")
    out += [f"- [{f.name}]({site}{f.path}): {f.size / 1024:.0f} KB, ~{f.size // 4 // 1000}k tokens" for f in feeds]
    out.append("")
    used: set[str] = set()
    for name, pred in LLMS_SECTIONS:
        out.append(f"## {name}")
        out += extra.get(name, [])
        for d in docs:
            if d.path not in used and pred(d):
                used.add(d.path)
                summ = SUMMARIES.get(d.path) or first_sentence(d.text) or d.title
                out.append(f"- [{d.title}]({site}{d.site_url}): {summ}")
        out.append("")
    out.append("## Optional")
    rest = [d for d in docs if d.path not in used]
    by_tier: dict[Tier, list[Doc]] = {}
    for d in rest:
        by_tier.setdefault(d.tier, []).append(d)
    tiers: tuple[Tier, ...] = ("core", "process", "reference", "archive")
    for t in tiers:
        if by_tier.get(t):
            out.append(f"- {t.capitalize()} docs ({len(by_tier[t])}): " + ", ".join(
                f"[{d.title}]({site}{d.site_url})" for d in by_tier[t]))
    out.append("")
    return "\n".join(out)
