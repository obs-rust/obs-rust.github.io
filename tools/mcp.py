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
from pydantic import JsonValue

from models import (
    JSON_SCHEMA,
    AllowlistFile,
    ControlApiSchema,
    FieldRow,
    JsonRpcId,
    JsonRpcResponse,
    JsonSchema,
    McpJson,
    McpResource,
    McpSchemaFile,
    McpServerConfig,
    McpStats,
    McpTool,
    Permissions,
    RegistryRepository,
    RegistryServer,
    ResourcesFile,
    SchemaSource,
    ServerCapabilities,
    ServerInfo,
    Session,
    SessionHead,
    SessionStep,
    Surface,
    TextContent,
    ToolAnnotations,
    ToolCallParams,
    ToolCallRequest,
    ToolCallResult,
    ToolError,
    ToolsFile,
    msg_json,
)

esc = html.escape
SITE = "https://obs-rust.com"
REPO = "obs-rust/obs-studio"

# Grouped by what an agent is trying to do. Every tool must land in exactly one group.
GROUPS: list[tuple[str, str, str, list[str]]] = [
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


def _rs_str_fn(txt: str, fn: str) -> str | None:
    """The string literal returned by `fn <fn>(&self) -> &str { "..." }` in a Rust source."""
    m = re.search(rf'fn {fn}\(&self\) -> &str \{{\s*"((?:[^"\\]|\\.)*)"', txt)
    return m.group(1) if m else None


def load_surface(obs: Path) -> Surface:
    schema_path = obs / "docs/rust-port/control-api.schema.json"
    src = obs / "rust/obs-mcp/src"
    if not schema_path.exists() or not src.exists():
        raise SystemExit(f"mcp: missing {schema_path} or {src} (sparse checkout must include both)")
    snap = ControlApiSchema.model_validate_json(schema_path.read_text())
    descs: dict[str, str] = {}
    for f in sorted(src.rglob("*.rs")):
        for m in TYPED_TOOL.finditer(f.read_text()):
            descs[m.group("name")] = _rust_str(m.group("desc")).strip()
        for m in IMPL_TOOL.finditer(f.read_text()):
            descs.setdefault(m.group("name"), _rust_str(m.group("desc")).strip())
    names = [t.name for t in snap.tools]
    missing = sorted(set(names) ^ set(descs))
    if missing:
        raise SystemExit(f"mcp: tool set differs between control-api.schema.json and typed_tool! source: {missing}")
    grouped = [n for g in GROUPS for n in g[3]]
    if sorted(grouped) != sorted(names) or len(grouped) != len(set(grouped)):
        raise SystemExit(f"mcp: GROUPS out of date: {sorted(set(names) ^ set(grouped))}")
    tools = [McpTool(name=t.name, description=descs[t.name], inputSchema=t.inputSchema,
                     outputSchema=t.outputSchema, annotations=t.annotations) for t in snap.tools]
    resources: list[McpResource] = []
    for f in sorted((src / "resources").glob("*.rs")):
        txt = f.read_text()
        uri, name, description, mime = (_rs_str_fn(txt, k) for k in ("uri", "name", "description", "mime_type"))
        if uri is not None and name is not None and description is not None and mime is not None:
            resources.append(McpResource(uri=uri, name=name, description=description, mimeType=mime))
    if not resources:
        raise SystemExit("mcp: no resources extracted")
    disp = (src / "server/dispatch.rs").read_text()
    proto = re.search(r'PROTOCOL_VERSION: &str = "([^"]+)"', disp)
    if not proto:
        raise SystemExit("mcp: PROTOCOL_VERSION not found")
    cargo = obs / "rust/obs-mcp/Cargo.toml"
    ver = re.search(r'^version\s*=\s*"([^"]+)"', cargo.read_text(), re.M) if cargo.exists() else None
    mcp_json = McpJson.model_validate_json((obs / ".mcp.json").read_text())
    return Surface(tools=tools, resources=resources, tool_error=snap.toolError, protocol=proto.group(1),
                   version=ver.group(1) if ver else None, mcp_json=mcp_json)


def placeholder(desc: str) -> bool:
    return desc.endswith("control and inspect OBS directly.")


def badge(a: ToolAnnotations) -> tuple[str, str]:
    if a.readOnlyHint:
        return "cu", "read-only"
    if a.idempotentHint:
        return "", "idempotent"
    return "rust", "changes state"


# ---------------------------------------------------------------- schema rendering
# JSON Schema bodies are arbitrary, so they stay JsonSchema dicts; these helpers are the only
# place that looks keys up in them, and each returns a narrowed type.
def _get(s: JsonSchema, key: str) -> JsonValue:
    return s.get(key)


def _sub(s: JsonSchema, key: str) -> JsonSchema | None:
    v = s.get(key)
    return v if isinstance(v, dict) else None


def _str(s: JsonSchema, key: str) -> str | None:
    v = s.get(key)
    return v if isinstance(v, str) else None


def _schemas(s: JsonSchema, key: str) -> list[JsonSchema]:
    v = s.get(key)
    return [x for x in v if isinstance(x, dict)] if isinstance(v, list) else []


def _strs(s: JsonSchema, key: str) -> list[str]:
    v = s.get(key)
    return [x for x in v if isinstance(x, str)] if isinstance(v, list) else []


def _props(s: JsonSchema) -> dict[str, JsonSchema]:
    props = _sub(s, "properties") or {}
    return {k: v for k, v in props.items() if isinstance(v, dict)}


def _resolve(s: JsonSchema, root: JsonSchema) -> JsonSchema:
    ref = _str(s, "$ref")
    if ref is None:
        return s
    name = ref.split("/")[-1]
    target = _sub(_sub(root, "$defs") or {}, name) or {}
    return {**target, **{k: v for k, v in s.items() if k != "$ref"}}


def _type_const(s: JsonSchema) -> str | None:
    """The const of a tagged union member's `type` property, e.g. {"type": {"const": "scene"}}."""
    return _str(_sub(_sub(s, "properties") or {}, "type") or {}, "const")


def type_str(s: JsonSchema, root: JsonSchema) -> str:
    s = _resolve(s, root)
    if "oneOf" in s and all("const" in _resolve(x, root) for x in _schemas(s, "oneOf")):
        return " | ".join(f'"{_get(_resolve(x, root), "const")}"' for x in _schemas(s, "oneOf"))
    if "oneOf" in s or "anyOf" in s:
        opts = [_resolve(x, root) for x in (_schemas(s, "oneOf") or _schemas(s, "anyOf"))]
        return " | ".join(_str(o, "title") or _type_const(o) or type_str(o, root) for o in opts)
    tv = _get(s, "type")
    t = " | ".join(_strs(s, "type")) if isinstance(tv, list) else tv if isinstance(tv, str) else "any"
    items = _sub(s, "items")
    if t == "array" and items is not None:
        return f"array<{type_str(items, root)}>"
    title = _str(s, "title")
    if t == "object" and title:
        return title
    return t


def fields_rows(s: JsonSchema, root: JsonSchema) -> list[FieldRow]:
    s = _resolve(s, root)
    req = set(_strs(s, "required"))
    rows: list[FieldRow] = []
    for name, p in _props(s).items():
        r = _resolve(p, root)
        rows.append(FieldRow(name=name, type=type_str(p, root), required=name in req, default=_get(r, "default"),
                             description=(_str(r, "description") or "").strip()))
    return rows


def rows_html(rows: list[FieldRow]) -> str:
    if not rows:
        return '<p class="muted none">No arguments.</p>'
    out: list[str] = []
    for r in rows:
        tags = '<span class="tag haz">required</span>' if r.required else ""
        if r.default is not None:
            tags += f'<span class="tag">default {esc(json.dumps(r.default))}</span>'
        out.append(f'<tr><td><code>{esc(r.name)}</code>{tags}</td><td class="ty">{esc(r.type)}</td>'
                   f'<td>{esc(r.description)}</td></tr>')
    return f'<table class="ft"><tbody>{"".join(out)}</tbody></table>'


def _placeholder_value(json_type: JsonValue) -> JsonValue:
    """A minimal valid value for a JSON Schema primitive type (the first one if it is a list)."""
    t = json_type[0] if isinstance(json_type, list) and json_type else json_type
    match t:
        case "string":
            return "Scene"
        case "integer" | "number":
            return 0
        case "boolean":
            return True
        case "object":
            return {}
        case "array":
            return []
        case _:
            return None


def minimal_args(s: JsonSchema, root: JsonSchema) -> dict[str, JsonValue]:
    s = _resolve(s, root)
    props = _props(s)
    out: dict[str, JsonValue] = {}
    for name in _strs(s, "required"):
        p = _resolve(props[name], root)
        if "oneOf" in p:
            p = _resolve(_schemas(p, "oneOf")[0], root)
            if "const" in p:
                out[name] = _get(p, "const")
                continue
            out[name] = minimal_args(p, root)
            continue
        out[name] = _placeholder_value(_get(p, "type"))
    return out


def render_reference(tools: list[McpTool]) -> tuple[str, str]:
    by = {t.name: t for t in tools}
    cards: list[str] = []
    nav: list[str] = []
    for gid, gname, gdesc, names in GROUPS:
        nav.append(f'<a href="#g-{gid}">{gname} <span>{len(names)}</span></a>')
        items: list[str] = []
        for n in names:
            t = by[n]
            cls, label = badge(t.annotations)
            hints = " · ".join(f'{k.replace("Hint", "")}={str(v).lower()}'
                               for k, v in sorted(t.annotations.model_dump().items()))
            desc = esc(t.description)
            if placeholder(t.description):
                types = [x for x in (_str(t.inputSchema, "description"), _str(t.outputSchema, "description")) if x]
                desc = (f'<span class="muted">Upstream description is a placeholder ("{desc}").</span> '
                        + esc(" ".join(types)))
            call = ToolCallRequest(jsonrpc="2.0", id=1, method="tools/call",
                                   params=ToolCallParams(name=n, arguments=minimal_args(t.inputSchema, t.inputSchema)))
            items.append(
                f'<article class="tool" id="{n}" data-ro="{str(t.annotations.readOnlyHint).lower()}" '
                f'data-search="{esc((n + " " + t.description).lower())}">'
                f'<header><a class="nm" href="#{n}">{n}</a><span class="tag {cls}">{label}</span>'
                f'<a class="tag" href="/mcp/tools/{n}.json">json</a></header>'
                f'<p>{desc}</p><p class="hints">{esc(hints)}</p>'
                f'<h4>Arguments</h4>{rows_html(fields_rows(t.inputSchema, t.inputSchema))}'
                f'<h4>Returns</h4>{rows_html(fields_rows(t.outputSchema, t.outputSchema))}'
                f'<details><summary>Call it</summary><pre>{esc(msg_json(call))}</pre></details></article>')
        cards.append(f'<section class="grp" id="g-{gid}"><h3>{gname}</h3><p class="muted">{gdesc}</p>{"".join(items)}</section>')
    return "".join(cards), "".join(nav)


# ---------------------------------------------------------------- sessions
def load_sessions(root: Path, surface: Surface) -> list[Session]:
    by = {t.name: t for t in surface.tools}
    out: list[Session] = []
    for f in sorted((root / "mcp/sessions").glob("*.jsonl")):
        lines = [x for x in f.read_text().splitlines() if x.strip()]
        head = SessionHead.model_validate_json(lines[0])
        pending: dict[JsonRpcId, str] = {}
        steps: list[SessionStep] = []
        for st in (SessionStep.model_validate_json(x) for x in lines[1:]):
            m = st.msg
            if isinstance(m, ToolCallRequest):
                name = m.params.name
                if name not in by:
                    raise SystemExit(f"{f.name}: unknown tool {name}")
                try:
                    jsonschema.validate(m.params.arguments, by[name].inputSchema)
                except jsonschema.ValidationError as e:
                    raise SystemExit(f"{f.name}: {name} arguments invalid: {e.message}")
                pending[m.id] = name
            elif isinstance(m, JsonRpcResponse) and m.id in pending:
                res = m.result
                name = pending.pop(m.id)
                if not isinstance(res, ToolCallResult):
                    raise SystemExit(f"{f.name}: {name} result is not a tools/call result")
                schema = surface.tool_error if res.isError else by[name].outputSchema
                try:
                    jsonschema.validate(res.structuredContent, schema)
                except jsonschema.ValidationError as e:
                    raise SystemExit(f"{f.name}: {name} result invalid: {e.message}")
                if res.isError:
                    ToolError.model_validate(res.structuredContent)
                # the server always mirrors structuredContent as a text block (typed.rs)
                content = res.content or [TextContent(text=json.dumps(res.structuredContent, separators=(",", ":")))]
                res = ToolCallResult(content=content, structuredContent=res.structuredContent, isError=res.isError)
                st = st.model_copy(update={"msg": JsonRpcResponse(jsonrpc=m.jsonrpc, id=m.id, result=res)})
            steps.append(st)
        out.append(Session(slug=f.stem, head=head, steps=steps))
    return sorted(out, key=lambda x: x.head.order)


def render_transcript(s: Session) -> str:
    rows: list[str] = []
    for st in s.steps:
        if st.note:
            rows.append(f'<div class="why">{esc(st.note)}</div>')
        who = "a" if st.from_ == "agent" else "s"
        rows.append(f'<div class="msg {who}"><span class="dir">{"→" if who == "a" else "←"}</span><code>'
                    f'{esc(st.msg_json())}</code></div>')
    return f'<div class="tx">{"".join(rows)}</div>'


def render_sessions(sessions: list[Session]) -> str:
    tabs: list[str] = []
    panes: list[str] = []
    for i, s in enumerate(sessions):
        tabs.append(f'<button role="tab" aria-selected="{str(i == 0).lower()}">{esc(s.head.title)}</button>')
        cav = f'<p class="cav">{esc(s.head.caveat)}</p>' if s.head.caveat else ""
        panes.append(f'<div class="pane{" on" if i == 0 else ""}"><p class="sum">{esc(s.head.summary)} '
                     f'<a href="/mcp/sessions/{s.slug}.jsonl">.jsonl</a></p>{render_transcript(s)}{cav}</div>')
    return f'<div class="tabset"><div class="tabs" role="tablist">{"".join(tabs)}</div>{"".join(panes)}</div>'


# ---------------------------------------------------------------- artifacts
def write_artifacts(out: Path, surface: Surface, sessions: list[Session], obs_sha: str, generated: str,
                    schema_dir: Path) -> McpStats:
    d = out / "mcp"
    (d / "tools").mkdir(parents=True, exist_ok=True)
    (d / "sessions").mkdir(exist_ok=True)
    server = ServerInfo(name="obs-mcp", version=surface.version, protocolVersion=surface.protocol,
                        capabilities=ServerCapabilities(), transport=["stdio", "unix-socket"])
    schema = McpSchemaFile(schema_version=1, generated=generated,
                           source=SchemaSource(repo=f"https://github.com/{REPO}", commit=obs_sha,
                                               paths=["docs/rust-port/control-api.schema.json", "rust/obs-mcp/src"]),
                           server=server, tools=surface.tools, resources=surface.resources,
                           resourceTemplates=[], prompts=[], toolError=surface.tool_error)
    (d / "schema.json").write_text(json.dumps(schema.model_dump(mode="json"), indent=1))
    (d / "tools.json").write_text(json.dumps(ToolsFile(tools=surface.tools).model_dump(mode="json"), indent=1))
    (d / "resources.json").write_text(
        json.dumps(ResourcesFile(resources=surface.resources).model_dump(mode="json"), indent=1))
    for t in surface.tools:
        (d / "tools" / f"{t.name}.json").write_text(json.dumps(t.model_dump(mode="json"), indent=1))
    (d / "mcp.json").write_text(json.dumps(surface.mcp_json.model_dump(mode="json", exclude_none=True), indent=2) + "\n")
    ro = [f"mcp__obs__{t.name}" for t in surface.tools if t.annotations.readOnlyHint]
    allow = AllowlistFile(permissions=Permissions(allow=ro))
    (d / "read-only-allowlist.json").write_text(json.dumps(allow.model_dump(mode="json"), indent=2) + "\n")
    for s in sessions:
        (d / "sessions" / f"{s.slug}.jsonl").write_text("\n".join(st.msg_json() for st in s.steps) + "\n")
    reg = RegistryServer(schema_="https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
                         name="io.github.obs-rust/obs-studio-rust", title="OBS Studio Rust",
                         description="Control a local OBS Studio (Rust): scenes, sources, recording, streaming, "
                                     "screenshots.",
                         version=surface.version or "0.1.0", websiteUrl=f"{SITE}/mcp/",
                         repository=RegistryRepository(url=f"https://github.com/{REPO}", source="github",
                                                       subfolder="rust/obs-mcp"))
    reg_json = reg.model_dump(mode="json", by_alias=True)
    jsonschema.validate(reg_json, JSON_SCHEMA.validate_json((schema_dir / "server.schema.json").read_text()))
    (d / "server.json").write_text(json.dumps(reg_json, indent=2) + "\n")
    n_ro = len(ro)
    n_idem = sum(1 for t in surface.tools if not t.annotations.readOnlyHint and t.annotations.idempotentHint)
    return McpStats(n_tools=len(surface.tools), n_resources=len(surface.resources), n_ro=n_ro, n_idem=n_idem,
                    n_mut=len(surface.tools) - n_ro - n_idem, ro_allow=json.dumps(ro),
                    schema_kb=f"{(d / 'schema.json').stat().st_size / 1024:.0f}")


CLIENT_CONFIG = McpJson(mcpServers={"obs": McpServerConfig(command="/path/to/obs-studio/mcp", args=["--mcp"])})


def corpus_markdown(surface: Surface, sessions: list[Session]) -> str:
    """The /mcp/ reference as markdown, for the AI corpus and /mcp/index.md."""
    o = ["# obs-studio-rust MCP server reference (generated)", "",
         f"MCP server `obs-mcp` {surface.version or ''}, protocol {surface.protocol}. Local only: stdio "
         "(`./mcp --mcp`) or a unix socket (`--mcp-listen` / `--mcp-attach`). Built from source with "
         "`./mcp --build` in an obs-studio checkout. Machine-readable: https://obs-rust.com/mcp/schema.json.",
         "", "Client config (Claude Code, Cursor, Claude Desktop):", "```json",
         json.dumps(CLIENT_CONFIG.model_dump(mode="json", exclude_none=True)), "```", ""]
    by = {t.name: t for t in surface.tools}
    for _gid, gname, gdesc, names in GROUPS:
        o += [f"## {gname} tools", gdesc, ""]
        for n in names:
            t = by[n]
            o += [f"### {n}", t.description, f"Annotations: {json.dumps(t.annotations.model_dump(mode='json'))}"]
            for label, s in (("Arguments", t.inputSchema), ("Returns", t.outputSchema)):
                rows = fields_rows(s, s)
                if rows:
                    o.append(f"{label}:")
                    o += [f"- `{r.name}` {r.type}{' (required)' if r.required else ''}"
                          f"{' default ' + json.dumps(r.default) if r.default is not None else ''}: {r.description}"
                          for r in rows]
            o.append("")
    o.append("## Resources")
    o += [f"- `{r.uri}` ({r.mimeType}): {r.description}" for r in surface.resources]
    o += ["", "## Errors", "Failed tool calls return `isError: true` with structuredContent "
          "`{code, category, message, retryable}` (ToolError); codes follow obs-websocket v5 status ranges.", ""]
    o.append("## Example sessions")
    for s in sessions:
        o += [f"### {s.head.title}", s.head.summary, "```"]
        for st in s.steps:
            if st.note:
                o.append(f"# {st.note}")
            o.append(("> " if st.from_ == "agent" else "< ") + st.msg_json())
        o.append("```")
        if s.head.caveat:
            o.append(s.head.caveat)
        o.append("")
    return "\n".join(o)
