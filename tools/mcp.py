"""MCP surface of obs-studio-rust: extraction, validation and rendering for /mcp/.

Source of truth (see .cache design notes merged into DESIGN.md §4):
  * docs/rust-port/control-api.schema.json  input/output schemas + annotations, drift-tested upstream
  * rust/obs-mcp/src/**/*.rs                 descriptions (typed_tool!), resources, protocol version
Everything fails closed: a tool missing a description, a group, or a session call that does not
validate against the real schema stops the build.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

import jsonschema

esc = html.escape
SITE = "https://obs-rust.com"
REPO = "obs-rust/obs-studio"

# Grouped by what an agent is trying to do. Every tool must land in exactly one group.
GROUPS = [
    ("see", "See", "Read the state of OBS without changing anything.",
     ["scenes_list", "scene_get_current", "sources_list", "scene_items_list", "screenshot", "pipeline_dump"]),
    ("compose", "Compose", "Build and change scenes, sources and their layout.",
     ["scene_create", "scene_remove", "scene_set_current", "source_create", "source_remove", "source_set_settings",
      "scene_item_add", "scene_item_set_transform", "scene_item_set_visible"]),
    ("live", "Go live", "Recording, streaming, the virtual camera and the virtual mic.",
     ["record_start", "record_stop", "record_status", "stream_start", "stream_stop", "stream_status",
      "vcam_start", "vcam_stop", "vcam_status", "vmic_status"]),
    ("media", "Media", "Media sources.", ["media_status", "media_restart"]),
    ("measure", "Measure", "Performance counters.", ["stats_get", "stats_reset"]),
    ("wait", "Wait", "Block until a typed condition holds, without sleeping.", ["wait_for"]),
]

IMPL_TOOL = re.compile(
    r'const NAME: &\'static str = "(?P<name>[a-z_]+)";.*?fn description\(&self\) -> &str \{\s*'
    r'(?P<desc>(?:"(?:[^"\\]|\\.)*"\s*)+)\}', re.S)
TYPED_TOOL = re.compile(
    r'typed_tool!\(\s*\w+\s*,\s*"(?P<name>[a-z_]+)"\s*,\s*\w+\s*,\s*\w+\s*,\s*\w+\s*,\s*(?P<kind>\w+)\s*,\s*'
    r'(?P<desc>(?:"(?:[^"\\]|\\.)*"\s*)+)', re.S)


def _rust_str(lits: str) -> str:
    parts = re.findall(r'"((?:[^"\\]|\\.)*)"', lits)
    s = "".join(parts)
    s = re.sub(r"\\\n\s*", "", s)
    return s.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def load_surface(obs: Path) -> dict:
    schema_path = obs / "docs/rust-port/control-api.schema.json"
    src = obs / "rust/obs-mcp/src"
    if not schema_path.exists() or not src.exists():
        raise SystemExit(f"mcp: missing {schema_path} or {src} (sparse checkout must include both)")
    snap = json.loads(schema_path.read_text())
    descs, kinds = {}, {}
    for f in sorted(src.rglob("*.rs")):
        for m in TYPED_TOOL.finditer(f.read_text()):
            descs[m["name"]] = _rust_str(m["desc"]).strip()
            kinds[m["name"]] = m["kind"]
        for m in IMPL_TOOL.finditer(f.read_text()):
            descs.setdefault(m["name"], _rust_str(m["desc"]).strip())
    names = [t["name"] for t in snap["tools"]]
    missing = sorted(set(names) ^ set(descs))
    if missing:
        raise SystemExit(f"mcp: tool set differs between control-api.schema.json and typed_tool! source: {missing}")
    grouped = [n for g in GROUPS for n in g[3]]
    if sorted(grouped) != sorted(names) or len(grouped) != len(set(grouped)):
        raise SystemExit(f"mcp: GROUPS out of date: {sorted(set(names) ^ set(grouped))}")
    tools = []
    for t in snap["tools"]:
        tools.append({"name": t["name"], "description": descs[t["name"]], "inputSchema": t["inputSchema"],
                      "outputSchema": t["outputSchema"], "annotations": t["annotations"]})
    resources = []
    for f in sorted((src / "resources").glob("*.rs")):
        txt = f.read_text()
        got = {k: re.search(rf'fn {k}\(&self\) -> &str \{{\s*"((?:[^"\\]|\\.)*)"', txt) for k in
               ("uri", "name", "description", "mime_type")}
        if all(got.values()):
            resources.append({"uri": got["uri"][1], "name": got["name"][1], "description": got["description"][1],
                              "mimeType": got["mime_type"][1]})
    if not resources:
        raise SystemExit("mcp: no resources extracted")
    disp = (src / "server/dispatch.rs").read_text()
    proto = re.search(r'PROTOCOL_VERSION: &str = "([^"]+)"', disp)
    if not proto:
        raise SystemExit("mcp: PROTOCOL_VERSION not found")
    cargo = obs / "rust/obs-mcp/Cargo.toml"
    ver = re.search(r'^version\s*=\s*"([^"]+)"', cargo.read_text(), re.M) if cargo.exists() else None
    mcp_json = json.loads((obs / ".mcp.json").read_text())
    return {"tools": tools, "resources": resources, "toolError": snap["toolError"], "protocol": proto[1],
            "version": ver[1] if ver else None, "mcp_json": mcp_json}


def placeholder(desc: str) -> bool:
    return desc.endswith("control and inspect OBS directly.")


def badge(a: dict) -> tuple[str, str]:
    if a.get("readOnlyHint"):
        return "cu", "read-only"
    if a.get("idempotentHint"):
        return "", "idempotent"
    return "rust", "changes state"


# ---------------------------------------------------------------- schema rendering
def _resolve(s: dict, root: dict) -> dict:
    if isinstance(s, dict) and "$ref" in s:
        name = s["$ref"].split("/")[-1]
        return {**root.get("$defs", {}).get(name, {}), **{k: v for k, v in s.items() if k != "$ref"}}
    return s


def type_str(s: dict, root: dict) -> str:
    s = _resolve(s, root)
    if "oneOf" in s and all("const" in _resolve(x, root) for x in s["oneOf"]):
        return " | ".join(f'"{_resolve(x, root)["const"]}"' for x in s["oneOf"])
    if "oneOf" in s or "anyOf" in s:
        opts = [_resolve(x, root) for x in s.get("oneOf") or s.get("anyOf")]
        return " | ".join(o.get("title") or o.get("properties", {}).get("type", {}).get("const") or
                          type_str(o, root) for o in opts)
    t = s.get("type", "any")
    t = " | ".join(t) if isinstance(t, list) else t
    if t == "array" and "items" in s:
        return f"array<{type_str(s['items'], root)}>"
    if t == "object" and s.get("title"):
        return s["title"]
    return t


def fields_rows(s: dict, root: dict) -> list[dict]:
    s = _resolve(s, root)
    req = set(s.get("required", []))
    rows = []
    for name, p in (s.get("properties") or {}).items():
        r = _resolve(p, root)
        rows.append({"name": name, "type": type_str(p, root), "required": name in req,
                     "default": r.get("default"), "description": (r.get("description") or "").strip()})
    return rows


def rows_html(rows: list[dict]) -> str:
    if not rows:
        return '<p class="muted none">No arguments.</p>'
    out = []
    for r in rows:
        tags = '<span class="tag haz">required</span>' if r["required"] else ""
        if r["default"] is not None:
            tags += f'<span class="tag">default {esc(json.dumps(r["default"]))}</span>'
        out.append(f'<tr><td><code>{esc(r["name"])}</code>{tags}</td><td class="ty">{esc(r["type"])}</td>'
                   f'<td>{esc(r["description"])}</td></tr>')
    return f'<table class="ft"><tbody>{"".join(out)}</tbody></table>'


def minimal_args(s: dict, root: dict) -> dict:
    s = _resolve(s, root)
    out = {}
    for name in s.get("required", []):
        p = _resolve(s["properties"][name], root)
        if "oneOf" in p:
            p = _resolve(p["oneOf"][0], root)
            if "const" in p:
                out[name] = p["const"]
                continue
            out[name] = minimal_args(p, root)
            continue
        t = p.get("type")
        t = t[0] if isinstance(t, list) else t
        out[name] = {"string": "Scene", "integer": 0, "number": 0, "boolean": True, "object": {},
                     "array": []}.get(t)
    return out


def render_reference(tools: list[dict]) -> tuple[str, str]:
    by = {t["name"]: t for t in tools}
    cards, nav = [], []
    for gid, gname, gdesc, names in GROUPS:
        nav.append(f'<a href="#g-{gid}">{gname} <span>{len(names)}</span></a>')
        items = []
        for n in names:
            t = by[n]
            cls, label = badge(t["annotations"])
            hints = " · ".join(f'{k.replace("Hint", "")}={str(v).lower()}' for k, v in sorted(t["annotations"].items()))
            desc = esc(t["description"])
            if placeholder(t["description"]):
                types = [x for x in (t["inputSchema"].get("description"), t["outputSchema"].get("description")) if x]
                desc = (f'<span class="muted">Upstream description is a placeholder ("{desc}").</span> '
                        + esc(" ".join(types)))
            call = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                               "params": {"name": n, "arguments": minimal_args(t["inputSchema"], t["inputSchema"])}},
                              separators=(",", ":"))
            items.append(
                f'<article class="tool" id="{n}" data-ro="{str(bool(t["annotations"].get("readOnlyHint"))).lower()}" '
                f'data-search="{esc((n + " " + t["description"]).lower())}">'
                f'<header><a class="nm" href="#{n}">{n}</a><span class="tag {cls}">{label}</span>'
                f'<a class="tag" href="/mcp/tools/{n}.json">json</a></header>'
                f'<p>{desc}</p><p class="hints">{esc(hints)}</p>'
                f'<h4>Arguments</h4>{rows_html(fields_rows(t["inputSchema"], t["inputSchema"]))}'
                f'<h4>Returns</h4>{rows_html(fields_rows(t["outputSchema"], t["outputSchema"]))}'
                f'<details><summary>Call it</summary><pre>{esc(call)}</pre></details></article>')
        cards.append(f'<section class="grp" id="g-{gid}"><h3>{gname}</h3><p class="muted">{gdesc}</p>{"".join(items)}</section>')
    return "".join(cards), "".join(nav)


# ---------------------------------------------------------------- sessions
def load_sessions(root: Path, surface: dict) -> list[dict]:
    by = {t["name"]: t for t in surface["tools"]}
    out = []
    for f in sorted((root / "mcp/sessions").glob("*.jsonl")):
        lines = [json.loads(x) for x in f.read_text().splitlines() if x.strip()]
        head, steps = lines[0], lines[1:]
        pending = {}
        for st in steps:
            m = st["msg"]
            if m.get("method") == "tools/call":
                name = m["params"]["name"]
                if name not in by:
                    raise SystemExit(f"{f.name}: unknown tool {name}")
                try:
                    jsonschema.validate(m["params"]["arguments"], by[name]["inputSchema"])
                except jsonschema.ValidationError as e:
                    raise SystemExit(f"{f.name}: {name} arguments invalid: {e.message}")
                pending[m["id"]] = name
            elif "result" in m and m.get("id") in pending:
                res = m["result"]
                name = pending.pop(m["id"])
                schema = surface["toolError"] if res.get("isError") else by[name]["outputSchema"]
                try:
                    jsonschema.validate(res["structuredContent"], schema)
                except jsonschema.ValidationError as e:
                    raise SystemExit(f"{f.name}: {name} result invalid: {e.message}")
                # the server always mirrors structuredContent as a text block (typed.rs)
                res.setdefault("content", [{"type": "text", "text": json.dumps(res["structuredContent"],
                                                                               separators=(",", ":"))}])
                res = {"content": res.pop("content"), **res}
                m["result"] = res
        out.append({"slug": f.stem, **head, "steps": steps})
    return sorted(out, key=lambda x: x.get("order", 99))


def render_transcript(s: dict) -> str:
    rows = []
    for st in s["steps"]:
        if st.get("note"):
            rows.append(f'<div class="why">{esc(st["note"])}</div>')
        who = "a" if st["from"] == "agent" else "s"
        rows.append(f'<div class="msg {who}"><span class="dir">{"→" if who == "a" else "←"}</span><code>'
                    f'{esc(json.dumps(st["msg"], separators=(",", ":")))}</code></div>')
    return f'<div class="tx">{"".join(rows)}</div>'


def render_sessions(sessions: list[dict]) -> str:
    tabs, panes = [], []
    for i, s in enumerate(sessions):
        tabs.append(f'<button role="tab" aria-selected="{str(i == 0).lower()}">{esc(s["title"])}</button>')
        cav = f'<p class="cav">{esc(s["caveat"])}</p>' if s.get("caveat") else ""
        panes.append(f'<div class="pane{" on" if i == 0 else ""}"><p class="sum">{esc(s["summary"])} '
                     f'<a href="/mcp/sessions/{s["slug"]}.jsonl">.jsonl</a></p>{render_transcript(s)}{cav}</div>')
    return f'<div class="tabset"><div class="tabs" role="tablist">{"".join(tabs)}</div>{"".join(panes)}</div>'


# ---------------------------------------------------------------- artifacts
def write_artifacts(out: Path, surface: dict, sessions: list[dict], obs_sha: str, generated: str,
                    schema_dir: Path) -> dict:
    d = out / "mcp"
    (d / "tools").mkdir(parents=True, exist_ok=True)
    (d / "sessions").mkdir(exist_ok=True)
    server = {"name": "obs-mcp", "version": surface["version"], "protocolVersion": surface["protocol"],
              "capabilities": {"tools": {}, "resources": {}}, "transport": ["stdio", "unix-socket"]}
    schema = {"schema_version": 1, "generated": generated,
              "source": {"repo": f"https://github.com/{REPO}", "commit": obs_sha,
                         "paths": ["docs/rust-port/control-api.schema.json", "rust/obs-mcp/src"]},
              "server": server, "tools": surface["tools"], "resources": surface["resources"],
              "resourceTemplates": [], "prompts": [], "toolError": surface["toolError"]}
    (d / "schema.json").write_text(json.dumps(schema, indent=1))
    (d / "tools.json").write_text(json.dumps({"tools": surface["tools"]}, indent=1))
    (d / "resources.json").write_text(json.dumps({"resources": surface["resources"]}, indent=1))
    for t in surface["tools"]:
        (d / "tools" / f"{t['name']}.json").write_text(json.dumps(t, indent=1))
    (d / "mcp.json").write_text(json.dumps(surface["mcp_json"], indent=2) + "\n")
    ro = [f"mcp__obs__{t['name']}" for t in surface["tools"] if t["annotations"].get("readOnlyHint")]
    (d / "read-only-allowlist.json").write_text(json.dumps({"permissions": {"allow": ro}}, indent=2) + "\n")
    for s in sessions:
        (d / "sessions" / f"{s['slug']}.jsonl").write_text(
            "\n".join(json.dumps(st["msg"], separators=(",", ":")) for st in s["steps"]) + "\n")
    reg = {"$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
           "name": "io.github.obs-rust/obs-studio-rust", "title": "OBS Studio Rust",
           "description": "Control a local OBS Studio (Rust): scenes, sources, recording, streaming, screenshots.",
           "version": surface["version"] or "0.1.0", "websiteUrl": f"{SITE}/mcp/",
           "repository": {"url": f"https://github.com/{REPO}", "source": "github", "subfolder": "rust/obs-mcp"}}
    jsonschema.validate(reg, json.loads((schema_dir / "server.schema.json").read_text()))
    (d / "server.json").write_text(json.dumps(reg, indent=2) + "\n")
    n_ro = len(ro)
    n_idem = sum(1 for t in surface["tools"] if not t["annotations"].get("readOnlyHint") and t["annotations"].get("idempotentHint"))
    return {"n_tools": len(surface["tools"]), "n_resources": len(surface["resources"]), "n_ro": n_ro,
            "n_idem": n_idem, "n_mut": len(surface["tools"]) - n_ro - n_idem, "ro_allow": json.dumps(ro),
            "schema_kb": f"{(d / 'schema.json').stat().st_size / 1024:.0f}"}


def corpus_markdown(surface: dict, sessions: list[dict]) -> str:
    """The /mcp/ reference as markdown, for the AI corpus and /mcp/index.md."""
    o = ["# obs-studio-rust MCP server reference (generated)", "",
         f"MCP server `obs-mcp` {surface['version'] or ''}, protocol {surface['protocol']}. Local only: stdio "
         "(`./mcp --mcp`) or a unix socket (`--mcp-listen` / `--mcp-attach`). Built from source with "
         "`./mcp --build` in an obs-studio checkout. Machine-readable: https://obs-rust.com/mcp/schema.json.",
         "", "Client config (Claude Code, Cursor, Claude Desktop):", "```json",
         json.dumps({"mcpServers": {"obs": {"command": "/path/to/obs-studio/mcp", "args": ["--mcp"]}}}), "```", ""]
    by = {t["name"]: t for t in surface["tools"]}
    for gid, gname, gdesc, names in GROUPS:
        o += [f"## {gname} tools", gdesc, ""]
        for n in names:
            t = by[n]
            o += [f"### {n}", t["description"], f"Annotations: {json.dumps(t['annotations'])}"]
            for label, s in (("Arguments", t["inputSchema"]), ("Returns", t["outputSchema"])):
                rows = fields_rows(s, s)
                if rows:
                    o.append(f"{label}:")
                    o += [f"- `{r['name']}` {r['type']}{' (required)' if r['required'] else ''}"
                          f"{' default ' + json.dumps(r['default']) if r['default'] is not None else ''}: {r['description']}"
                          for r in rows]
            o.append("")
    o.append("## Resources")
    o += [f"- `{r['uri']}` ({r['mimeType']}): {r['description']}" for r in surface["resources"]]
    o += ["", "## Errors", "Failed tool calls return `isError: true` with structuredContent "
          "`{code, category, message, retryable}` (ToolError); codes follow obs-websocket v5 status ranges.", ""]
    o.append("## Example sessions")
    for s in sessions:
        o += [f"### {s['title']}", s["summary"], "```"]
        for st in s["steps"]:
            if st.get("note"):
                o.append(f"# {st['note']}")
            o.append(("> " if st["from"] == "agent" else "< ") + json.dumps(st["msg"], separators=(",", ":")))
        o.append("```")
        if s.get("caveat"):
            o.append(s["caveat"])
        o.append("")
    return "\n".join(o)
