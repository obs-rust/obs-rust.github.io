"""AI corpus v2 (DESIGN.md §7): tiers, structure-aware chunks, typed chunks, llms.txt v2.

A doc is {"group", "path", "text", "url", "title", "slug", "site_url"}.
A chunk is {"id", "doc", "group", "tier", "kind", "breadcrumb", "url", "source", "text",
            "chars", "tokens_est", "sha256"}; "text" opens with its breadcrumb so it stands alone.
"""

from __future__ import annotations

import hashlib
import json
import re

SCHEMA_VERSION = 2
MIN_CHARS, TARGET_MAX, HARD_MAX = 300, 2000, 2400
ARCHIVE = re.compile(r"(\d{4}-\d{2}-\d{2}|-\d{3,}\.md$|retrospective|handoff|hall-of-fame|audit)")
CORE_PATHS = {"README.md", "AGENTS.md", "CONTRIBUTING.md", "SECURITY.md", "mcp/reference.md",
              "obs-websocket/docs/generated/protocol.md", "docs/rust-port/mcp.md", "docs/rust-port/control-api.md"}
# Docs fully represented by typed chunks: their prose is not chunked a second time.
TYPED_DOCS = {"obs-websocket/reference.md", "mcp/reference.md", "docs/features.md"}


def tier(path: str) -> str:
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


def _record(cid: str, doc: dict, kind: str, crumb: list[str], url: str, source: str, body: str) -> dict:
    head = " › ".join(c for c in crumb if c)
    text = f"[{head}]\n{body.strip()}" if head else body.strip()
    return {"id": cid, "doc": doc["slug"], "group": doc["group"], "tier": doc["tier"], "kind": kind,
            "breadcrumb": crumb, "url": url, "source": source, "text": text, "chars": len(text),
            "tokens_est": tokens_est(text), "sha256": hashlib.sha256(text.encode()).hexdigest()}


# ---------------------------------------------------------------- prose
def _sections(text: str) -> list[tuple[list[str], str]]:
    """Split markdown on headings outside fences; return (heading path, body) in order."""
    out, path, buf, fence = [], [], [], False
    for line in text.splitlines():
        if re.match(r"^\s*(```|~~~)", line):
            fence = not fence
        m = None if fence else re.match(r"^(#{1,4})\s+(.+?)\s*#*\s*$", line)
        if m:
            if "\n".join(buf).strip():
                out.append((list(path), "\n".join(buf)))
            lvl = len(m[1])
            path = path[: lvl - 1] + [""] * max(0, lvl - 1 - len(path))
            path = path[: lvl - 1] + [re.sub(r"`|\*\*", "", m[2]).strip()]
            buf = []
        else:
            buf.append(line)
    if "\n".join(buf).strip():
        out.append((list(path), "\n".join(buf)))
    return out


def _blocks(body: str) -> list[str]:
    """Paragraph blocks; a fenced block or a table is one unbreakable block."""
    blocks, cur, fence = [], [], False
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
    out, cur = [], ""
    for p in parts:
        if cur and len(cur) + len(p) > TARGET_MAX:
            out.append(cur)
            cur = ""
        cur += p if not cur else ("" if p.startswith(("\n", " ")) else " ") + p
    if cur:
        out.append(cur)
    final = []
    for o in out:  # a list item or line can still be too long: fall back to sentences, then lines
        if len(o) > HARD_MAX and o is not block:
            final += _split_long(o)
        elif len(o) > HARD_MAX:
            final += [o[i:i + TARGET_MAX] for i in range(0, len(o), TARGET_MAX)]
        else:
            final.append(o)
    return final


def prose_chunks(doc: dict, title: str) -> list[dict]:
    secs = _sections(doc["text"])
    # merge tiny sections into the previous one (sibling or parent)
    merged: list[tuple[list[str], str]] = []
    for path, body in secs:
        if merged and len(body.strip()) < MIN_CHARS:
            ppath, pbody = merged[-1]
            hdr = "#" * max(1, len([p for p in path if p])) + " " + (path[-1] if path else "")
            merged[-1] = (ppath, pbody.rstrip() + "\n\n" + (hdr + "\n" if path else "") + body.strip())
        else:
            merged.append((path, body))
    # a short opening section has nothing before it: fold it forward into the next one
    while len(merged) > 1 and len(merged[0][1].strip()) < MIN_CHARS:
        (p0, b0), (p1, b1) = merged[0], merged[1]
        hdr = "#" * max(1, len([p for p in p1 if p])) + " " + (p1[-1] if p1 else "")
        merged[:2] = [(p0, b0.rstrip() + "\n\n" + hdr + "\n" + b1.strip())]
    out, seen = [], {}
    for path, body in merged:
        pieces, cur = [], ""
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
        base = f"{doc['slug']}#{slug('-'.join(p for p in path if p)) or 'top'}"
        for i, piece in enumerate(pieces):
            cid = base if i == 0 else f"{base}~{i + 1}"
            n = seen.get(cid, 0)
            seen[cid] = n + 1
            if n:
                cid += f"-{n + 1}"
            out.append(_record(cid, doc, "prose", [title] + [p for p in path if p and p != title],
                               doc["site_url"], doc["source"], piece))
    return out


# ---------------------------------------------------------------- typed
def ws_chunks(doc: dict, proto: dict, site: str) -> list[dict]:
    out = []
    for r in proto["requests"]:
        lines = [f"Request {r['requestType']}: {r['description']}",
                 f"Category {r['category']}; since {r['initialVersion']}; complexity {r['complexity']}/5"
                 + ("; DEPRECATED" if r["deprecated"] else "") + "."]
        for label, fs in (("Request fields", r["requestFields"]), ("Response fields", r["responseFields"])):
            if fs:
                lines.append(label + ":")
                lines += [f"- {f['valueName']} ({f['valueType']}{', optional' if f.get('valueOptional') else ''}): "
                          f"{f['valueDescription']}" for f in fs]
        out.append(_record(f"ws:request:{r['requestType']}", doc, "ws-request",
                           ["obs-websocket v5", "Requests", r["category"], r["requestType"]],
                           f"{site}/websocket/#{r['requestType']}", doc["source"], "\n".join(lines)))
    for e in proto["events"]:
        lines = [f"Event {e['eventType']}: {e['description']}",
                 f"Category {e['category']}; subscription {e['eventSubscription']}; since {e['initialVersion']}."]
        lines += [f"- {f['valueName']} ({f['valueType']}): {f['valueDescription']}" for f in e["dataFields"]]
        out.append(_record(f"ws:event:{e['eventType']}", doc, "ws-event",
                           ["obs-websocket v5", "Events", e["category"], e["eventType"]],
                           f"{site}/websocket/#{e['eventType']}", doc["source"], "\n".join(lines)))
    for en in proto["enums"]:
        lines = [f"Enum {en['enumType']}:"] + [f"- {i['enumIdentifier']} = {i['enumValue']}: {i['description']}"
                                                for i in en["enumIdentifiers"]]
        out.append(_record(f"ws:enum:{en['enumType']}", doc, "ws-enum", ["obs-websocket v5", "Enums", en["enumType"]],
                           f"{site}/websocket/#{en['enumType']}", doc["source"], "\n".join(lines)))
    return out


def mcp_chunks(doc: dict, surface: dict, site: str, fields_rows) -> list[dict]:
    out = []
    for t in surface["tools"]:
        lines = [f"MCP tool {t['name']}: {t['description']}", f"Annotations: {json.dumps(t['annotations'])}"]
        for label, s in (("Arguments", t["inputSchema"]), ("Returns", t["outputSchema"])):
            rows = fields_rows(s, s)
            if rows:
                lines.append(label + ":")
                lines += [f"- {r['name']} ({r['type']}{', required' if r['required'] else ''}): {r['description']}"
                          for r in rows]
        out.append(_record(f"mcp:tool:{t['name']}", doc, "mcp-tool", ["MCP server", "Tools", t["name"]],
                           f"{site}/mcp/#{t['name']}", doc["source"], "\n".join(lines)))
    for r in surface["resources"]:
        out.append(_record(f"mcp:resource:{r['uri']}", doc, "mcp-resource", ["MCP server", "Resources", r["uri"]],
                           f"{site}/mcp/#resources", doc["source"],
                           f"MCP resource {r['uri']} ({r['mimeType']}): {r['description']}"))
    # the narrative part of the MCP page (setup, errors, sessions) stays as prose
    narrative = doc["text"].split("\n## See tools")[0]
    tail = doc["text"].split("\n## Resources", 1)[-1] if "\n## Resources" in doc["text"] else ""
    out += prose_chunks({**doc, "text": narrative + "\n## Resources" + tail}, "MCP server")
    return out


def ledger_chunks(doc: dict, items: list[dict]) -> list[dict]:
    out, seen = [], set()
    md_link = re.compile(r"\[([^\]]+)\]\([^)]+\)")
    for it in items:
        txt = md_link.sub(r"\1", it["text"])
        pr = re.search(r"/pull/(\d+)\)", it["text"])
        key = f"ledger:{pr[1]}" if pr else f"ledger:{slug(txt[:50])}"
        while key in seen:
            key += "+"
        seen.add(key)
        kind = "ledger-fix" if it["section"] == "Fixed upstream bugs" else "ledger-entry"
        out.append(_record(key, doc, kind, ["Features ledger", it["section"], it["area"]],
                           doc["site_url"], doc["source"], txt))
    return out


# ---------------------------------------------------------------- llms.txt v2
LLMS_SECTIONS = [
    ("Start here", lambda d: d["path"] in {"README.md", "AGENTS.md", "obs-websocket/docs/generated/protocol.md"}),
    ("Install and use", lambda d: d["path"] in {"docs/features.md", "docs/gpu-status.md", "SECURITY.md"}),
    ("Control OBS", lambda d: d["group"] in {"websocket", "mcp"} or d["path"] in {"docs/rust-port/mcp.md",
                                                                                   "docs/rust-port/control-api.md"}),
    ("Extend OBS", lambda d: d["group"] == "libobs-api" and d["path"].rsplit("/", 1)[-1] in {
        "plugins.rst", "scripting.rst", "reference-sources.rst", "reference-outputs.rst", "reference-encoders.rst",
        "reference-services.rst", "reference-frontend-api.rst", "graphics.rst", "reference-core.rst", "frontends.rst"}),
    ("Contribute", lambda d: d["path"] in {"CONTRIBUTING.md", "BUILD.md", "docs/rust-port/coordination.md",
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


def llms_txt(docs: list[dict], header: list[str], site: str, feeds: list[tuple[str, str, int]],
             extra: dict[str, list[str]]) -> str:
    out = list(header)
    out.append("## Feeds")
    out += [f"- [{name}]({site}{path}): {size / 1024:.0f} KB, ~{size // 4 // 1000}k tokens" for name, path, size in feeds]
    out.append("")
    used = set()
    for name, pred in LLMS_SECTIONS:
        out.append(f"## {name}")
        out += extra.get(name, [])
        for d in docs:
            if d["path"] not in used and pred(d):
                used.add(d["path"])
                summ = SUMMARIES.get(d["path"]) or first_sentence(d["text"]) or d["title"]
                out.append(f"- [{d['title']}]({site}{d['site_url']}): {summ}")
        out.append("")
    out.append("## Optional")
    rest = [d for d in docs if d["path"] not in used]
    by_tier = {}
    for d in rest:
        by_tier.setdefault(d["tier"], []).append(d)
    for t in ("core", "process", "reference", "archive"):
        if by_tier.get(t):
            out.append(f"- {t.capitalize()} docs ({len(by_tier[t])}): " + ", ".join(
                f"[{d['title']}]({site}{d['site_url']})" for d in by_tier[t]))
    out.append("")
    return "\n".join(out)
