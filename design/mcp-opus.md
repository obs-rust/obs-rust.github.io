# Publishing the obs-studio-rust MCP schema on obs-rust.com (design, Opus)

Source of truth: `obs-rust/obs-studio` at `origin/master` 7e68243c (2026-11-18). Paths below are
repo-relative to obs-studio unless they start with `/` (site URLs) or `tools/` (this site).

## 1. Inventory: what the server actually exposes

**Server identity** (`rust/obs-mcp/src/server/dispatch.rs`): `protocolVersion` `"2025-06-18"`,
`serverInfo {name: "obs-mcp", version: env!("CARGO_PKG_VERSION")}` = `"0.1.0"`
(`rust/obs-mcp/Cargo.toml`), `capabilities {tools: {}, resources: {}}`. No `instructions`, no
`prompts` capability, no `listChanged`, no `subscribe`. Methods: `initialize`, `ping`,
`tools/list`, `tools/call`, `resources/list`, `resources/read`; everything else (including
`prompts/list` and `resources/templates/list`) returns `-32601 method not found`.

**Prompts: none.** Not declared and not dispatched. The page must say so, not invent any.

**Registration** (`rust/obs-mcp/src/backend/mod.rs`, `ObsBackend::server`): scenes, sources,
outputs, screenshot, control, waiting, then resources scenes, stats. Register counts per file
5/8/6/1/9/1 = **30 tools**, matching the 30 entries of the committed snapshot. `tools/list` order
is registration order; the snapshot is sorted by name.

**Tool entry shape** (`server/tool.rs` `ToolRegistry::list`): `{name, description, inputSchema,
outputSchema?, annotations?}`. Every tool is a `TypedTool` (`server/typed.rs`), so every tool has
both `outputSchema` (`schemars::schema_for!(Output)`, draft 2020-12, with `$schema` and `title`)
and `annotations`. No tool has `title`. All input schemas set `additionalProperties: false`
(`deny_unknown_fields`); empty inputs get an explicit `properties: {}`.

**Annotations** are one of three constants (`typed.rs`):

| Const | readOnlyHint | idempotentHint | destructiveHint | openWorldHint |
|---|---|---|---|---|
| `READ_ONLY` | true | true | false | false |
| `MUTATING` | false | false | true | true |
| `IDEMPOTENT` | false | true | true | true |

**Results**: success = `content` (JSON text; screenshot adds an `image/png` item first) +
`structuredContent` + `isError:false`. Domain failure = `isError:true`, `structuredContent` is
`ToolError {code, category: not_ready|wrong_state|processing, message, retryable}` with
obs-websocket v5 codes 600, 207, 604, 702. Bad arguments are JSON-RPC `-32602`.

**Tools** (name, annotation const, required / optional inputs, description quoted verbatim):

| Tool | Ann. | Inputs (req; opt=default) | Description (verbatim) |
|---|---|---|---|
| `scenes_list` | RO | none | "List the names of all scenes, in order." |
| `scene_get_current` | RO | none | "Get the name of the current program scene, or null if none." |
| `scene_set_current` | IDEM | `name` | "Make the named scene the current program scene." |
| `scene_create` | MUT | `name` | "Create a new empty scene with the given name. When there is no program scene yet, the new scene becomes the current program scene." |
| `scene_remove` | MUT | `name` | "Remove the scene with the given name." |
| `sources_list` | RO | none | "List all sources with their names and kind ids." |
| `source_create` | MUT | `kind,name,settings`; `scene`,`position` | "Create a source of the given kind with a name and settings. Give \`scene\` (and optionally \`position\`) to also add it to that scene as an item." |
| `source_remove` | MUT | `name` | "Remove a source and its references from scenes." |
| `source_set_settings` | MUT | `name,settings` | "Merge settings into an existing source's settings." |
| `scene_item_add` | MUT | `scene,source`; `position` | "Add an existing source to a scene as a scene item, optionally at a position. A source only shows in the program output once it is an item of the program scene." |
| `scene_items_list` | RO | `scene` | "List the items of a scene (bottom to top) with their id, source name, visibility, position, scale and rotation." |
| `scene_item_set_visible` | IDEM | `scene,visible`; `item`\|`source` | "Show or hide a scene item, named by \`item\` (id from scene_items_list) or \`source\`." |
| `scene_item_set_transform` | MUT | `scene`; `item`,`source`,`position`,`scale`,`rotation` | "Set the position, scale and/or rotation of a scene item, named by \`item\` (id from scene_items_list) or \`source\`." |
| `record_start` | IDEM | `wait`=false, `timeout_ms`=5000 | "Start recording." |
| `record_stop` | IDEM | none | "Stop recording." |
| `record_status` | RO | none | "Report whether recording is active, with duration_ms and bytes where known." |
| `stream_start` | IDEM | `wait`=false, `timeout_ms`=5000 | "Start streaming." |
| `stream_stop` | IDEM | none | "Stop streaming." |
| `stream_status` | RO | none | "Report whether streaming is active, with duration_ms and bytes where known." |
| `screenshot` | RO | `source`,`width`,`height` | "Capture a PNG screenshot of a source, or of the program output when no source is named. Returns the image plus a text item {width, height, source} (source is null for the program output). The PNG has an alpha channel (RGBA): pixels nothing was drawn on, such as an empty scene, are fully transparent, which a viewer may show as white. A source only appears in the program output once it is an item of the program scene." |
| `vcam_start` | IDEM | `audio_enabled`=true, `audio_track`=1, `wait`=false, `timeout_ms`=5000 | "vcam start: control and inspect OBS directly." |
| `vcam_stop` | IDEM | none | "vcam stop: control and inspect OBS directly." |
| `vcam_status` | RO | none | "vcam status: control and inspect OBS directly." |
| `vmic_status` | RO | none | "vmic status: control and inspect OBS directly." |
| `media_restart` | MUT | `name` | "media restart: control and inspect OBS directly." |
| `media_status` | RO | `name` | "media status: control and inspect OBS directly." |
| `stats_get` | RO | none | "stats get: control and inspect OBS directly." |
| `stats_reset` | MUT | none | "stats reset: control and inspect OBS directly." |
| `pipeline_dump` | RO | none | "pipeline dump: control and inspect OBS directly." |
| `wait_for` | RO | `condition`; `timeout_ms`=5000 | "Observe a typed condition immediately, then wait within timeout_ms. Returns the final typed value on timeout; unavailable metrics never satisfy a threshold." |

`position`/`scale` are `$defs/Pair`; `wait_for.condition` is a `oneOf` tagged by `type`:
`output_state {output: record|stream|vcam|vmic, state: active|inactive}`, `source_active {name}`,
`media_state {name, state}`, `stat_at_most {metric, value}` with metric one of
`render_frame_time_ns, render_frames_dropped, vcam_latency_max_ns, vmic_latency_max_ns,
vmic_xruns, av_offset_abs_ms`. The full inputSchema/outputSchema JSON (45 KB) is not retyped here:
it is `docs/rust-port/control-api.schema.json` verbatim, and the build copies it (section 2).

**Resources** (`rust/obs-mcp/src/resources/`), `resources/list` entries `{uri, name, description,
mimeType}`; `resources/read` returns `{contents:[{uri, mimeType, text}]}`:

| uri | name | mimeType | description (verbatim) | text body |
|---|---|---|---|---|
| `obs://scenes` | `scenes` | `application/json` | "The scene graph: the current program scene, every scene and every source." | `{current, scenes, sources:[{name,kind}]}` |
| `obs://stats` | `stats` | `application/json` | "OBS performance: fps, cpu_usage (percent) and dropped_frames." | `{fps, cpu_usage, dropped_frames}` |

**Could not determine from source:** runtime behaviour beyond the schema (which source `kind`s
and `settings` keys are valid depends on the plugins `mcp-runtime` loads; the page links the
WebSocket reference's input kinds instead); whether `tools/list` succeeds without a display (mcp.md
only says it "does not prove video or device readiness"); and whether released AppImage/deb
builds contain a `--mcp`-capable binary (`--mcp` needs feature `bundled-native`; I found nothing
saying releases enable it). Treat all three as open (section 4).

### Extraction at build time: recommendation

**Recommended: committed snapshot + targeted source parse, cross-checked, fail closed.**

1. `docs/rust-port/control-api.schema.json` is already in the Pages sparse checkout (`/docs/`) and
   is CI-enforced upstream: `rust/obs-mcp/tests/mcp/typed.rs::schema_snapshot_has_not_drifted`
   compares it with `obs_mcp::tools::schema_snapshot()`. It holds `name, inputSchema,
   outputSchema, annotations` for all 30 tools plus `toolError`, but **no descriptions**
   (`tool_schema` is documented as "without human-facing prose"). Use it as the structural truth.
2. Add to the existing `pages.yml` sparse checkout (an edit, not a new workflow):
   `/rust/obs-mcp/src/`, `/rust/obs-mcp/Cargo.toml`, `/.mcp.json`. A few hundred KB.
3. `build.py` gains `mcp_inventory(obs) -> dict`, pure regex over that tree:
   - descriptions: each `typed_tool!(Ident, "name", Backend, In, Out, ANN, "desc", ...)` in
     `src/tools/*.rs` (7th arg must be one plain Rust string literal; unescape `\"`, `\\`,
     `\n`-continuations), plus the one hand-written `impl TypedTool` (`const NAME` +
     `fn description` literal) in `screenshot.rs`;
   - registration: `ObsBackend::server` in `src/backend/mod.rs` gives module order; each module's
     `pub fn register` gives `Box::new(Ident` order; map `Ident -> name` from step above;
   - resources: `fn uri/name/description/mime_type` literal bodies in `src/resources/*.rs`,
     ordered by `resources::<m>::register` calls;
   - identity: `PROTOCOL_VERSION`, `initialize_result` capabilities keys, `version` from Cargo.toml.
4. Fail the build (yesterday's site stays up, DESIGN.md principle 3) when: the registered name set
   differs from the snapshot name set; any description fails to parse; an `ANN` constant's values
   differ from the snapshot's `annotations`; capabilities gain a key the page does not render
   (for example `prompts`), or a method appears in `dispatch.rs` that the page does not know.
5. Merge: snapshot entry + `description`, in registration order, key order
   `name, description, inputSchema, outputSchema, annotations` (same as `ToolRegistry::list`).

**Rejected for now: run the built binary's `tools/list`.** Exact by construction, but the Pages
job would need soldr, the full native libobs/FFmpeg/x264 build via `obs-build mcp-runtime`
(tens of minutes, Linux deps or nix), and libobs startup. That breaks the job's budget and "docs
sparse checkout" model for 30 strings the source states literally. Superseded entirely once
upstream ships the full-prose snapshot (section 4, U1); then step 3 shrinks to reading one JSON.

## 2. Artifacts

| URL | Format | Notes |
|---|---|---|
| `/mcp/schema.json` | `{schema_version:1, generated, source:{repo, commit, paths[]}, server:{name, version, protocolVersion, capabilities, transport:"stdio"}, tools:[...tools/list result...], resources:[...resources/list result...], resourceTemplates:[], prompts:[], toolError:{...}}` | `tools`/`resources` are byte-for-byte the shape of the live results, so an agent can treat it as a pre-fetched `tools/list` |
| `/mcp/tools/<name>.json` | one tools/list entry | lets an agent fetch one tool cheaply |
| `/mcp/server.json` | official registry `server.json`, `$schema: https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json` | validated at build against a vendored copy of that schema (pinned, never fetched live) |
| `/mcp/index.md` | markdown twin of `/mcp/` | front matter per DESIGN.md §7 |
| `/mcp/mcp.json` | the repo's `.mcp.json` copied verbatim | provenance for the Claude Code snippet |

**server.json** (required: `name, description, version`; `packages` and `remotes` optional):

```json
{"$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
 "name": "io.github.obs-rust/obs-studio-rust",
 "title": "OBS Studio Rust",
 "description": "Control a local OBS (Rust hybrid): scenes, sources, recording, streaming, screenshots, virtual camera.",
 "version": "0.1.0",
 "websiteUrl": "https://obs-rust.com/mcp/",
 "repository": {"url": "https://github.com/obs-rust/obs-studio", "source": "github", "subfolder": "rust/obs-mcp"}}
```

Fit: a stdio, build-from-source server does **not** fit `packages`. Registry types are npm,
pypi, nuget, cargo (crates.io), oci, mcpb, each with an ownership check on a published artifact;
there is no "git + build command" type, and `remotes` are HTTP only. So the site publishes a
packageless `server.json` (valid against the schema, `websiteUrl` carries the setup), and does
**not** submit it to registry.modelcontextprotocol.io until a real package exists. Note: the
schema allows no packages, but whether the official registry *accepts* that is unverified (open
question). Namespace: prefer `io.github.obs-rust/*` (GitHub auth with `mcp-publisher login
github`, run by a maintainer, no workflow). `com.obs-rust/*` would need `/.well-known/mcp-registry-auth`
(`v=MCPv1; k=ed25519; p=<pubkey>`, under 4 KB, no redirects) and a private key someone keeps.
`version` = `serverInfo.version`; the release tag goes in `_meta` only if the registry gate opens.

**/.well-known/**: the only real convention is `mcp-registry-auth` above, needed only for the
domain namespace, so ship nothing by default. Server-card proposals (`/.well-known/mcp*.json`)
are unratified and aimed at remote HTTP servers; do not ship one. Discovery instead goes through
`llms.txt`, sitemap, `<link rel="alternate" type="application/json" href="/mcp/schema.json">`
on `/mcp/` and `/ai/`, and JSON-LD `SoftwareApplication` gaining `"featureList"` naming MCP.

**Install snippets** (all assume a clone at `$OBS` built once with `$OBS/mcp --build`; the launcher
exports `OBS_MCP_GRAPHICS_MODULE`/`MODULE_BIN`/`MODULE_DATA`/`DATA_PATH`, so always point clients at
`mcp`, never at `target-mcp/debug/obs-studio-rust` directly):

- Claude Code: open the clone (project `.mcp.json` is picked up and asks for approval), or
  `claude mcp add obs -- "$OBS/mcp" --mcp`.
- Cursor (`~/.cursor/mcp.json` or `.cursor/mcp.json`): `{"mcpServers":{"obs":{"command":"$OBS/mcp","args":["--mcp"]}}}`.
- VS Code (`.vscode/mcp.json`): `{"servers":{"obs":{"type":"stdio","command":"${workspaceFolder}/mcp","args":["--mcp"]}}}`.
- Claude Desktop (`claude_desktop_config.json`, same `mcpServers` shape as Cursor): shown with a
  caveat box, because Desktop ships for macOS/Windows and the server is Linux-only today; it only
  applies to a Linux Desktop build. Absolute paths everywhere; GUI clients need `uv` and `soldr` on
  the PATH they inherit.
- Attach to a running OBS: `"args":["--mcp-attach","$XDG_RUNTIME_DIR/obs-studio-rust/control.sock"]`
  after loading `libobs_mcp_module.so` (control-api.md, "Attach to the application").

Snippets are template strings in `build.py` whose command/args are asserted equal to the parsed
`.mcp.json`; drift fails the build.

**llms.txt**: in "Control OBS", two lines: `[MCP server](https://obs-rust.com/mcp/index.md): <first
sentence of the page>` and `[MCP schema (JSON)](https://obs-rust.com/mcp/schema.json): 30 tools, 2
resources, generated from <commit>` (counts are placeholders). **Corpus**: `docs/rust-port/mcp.md`
and `control-api.md` are already in the `process` tier via `docs/rust-port/*.md`; promote both to
`reference`, add typed chunks `kind: "mcp-tool"`, id `mcp:tool:<name>`, one per tool (description +
compact input/output summary + annotations, `url` `/mcp/#<name>`), `mcp:resource:<uri>` per
resource, and `site/mcp.md` (the twin) in `core` so the quickstart fits `llms-ctx.txt`. Add eval
pairs: "take a screenshot of OBS via MCP" -> `mcp:tool:screenshot`; "wait until recording is
active" -> `mcp:tool:wait_for`.

## 3. The /mcp/ page

Nav: not a sixth top item (DESIGN.md §4 fixes five); linked from `/ai/` (first card), home
compatibility section, and `/websocket/` ("prefer MCP for agents, WebSocket for existing clients").

Structure (one `h1`, works with JS off, every count from a placeholder):
1. **Hero**: "Let your agent run OBS." One sentence: obs-mcp is an MCP server inside OBS Studio
   Rust that calls libobs directly, no obs-websocket, no password. Buttons: Quickstart, schema.json.
2. **Requirements, honest, above the fold**: Linux (x86_64 tested in CI; the runtime builder
   `obs-build mcp-runtime` "stage[s] the Linux hybrid OBS application"). macOS: not supported yet.
   Windows: stdio unverified; socket attach returns "local control transport unavailable"
   (obs-rust/obs-studio#4455). Built from source (soldr + uv; NixOS auto-enters
   `ci/mcp-shell.nix`; other distros need libobs build deps); first build is long, later launches are
   incremental. Local only: stdio or a 0600 Unix socket; nothing listens on the network. Video and
   screenshots need a Wayland compositor or X server (headless Weston works); vcam needs
   v4l2loopback; vmic needs PipeWire/Pulse; record/stream need configured outputs.
3. **Quickstart** (copy buttons): clone, `./mcp --build`, smoke test
   `printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | ./mcp --mcp`, then the client
   tabs (Claude Code default, Cursor, VS Code, Codex, Claude Desktop with caveat). Then a 5-call
   agent recipe: `scene_create` -> `source_create {kind, name, settings, scene}` ->
   `screenshot` -> `record_start {wait:true}` -> `wait_for {condition:{type:"output_state",
   output:"record", state:"active"}}`. Kinds shown must exist in the module list (assert at build
   against a checked-in allowlist, or show a placeholder kind with a note).
4. **Two modes**: headless (`--mcp`, own libobs instance, `--record-dir`) vs attach to the running
   app (`--mcp-listen`/`--mcp-attach`, module socket). Diagram as text table, not image.
5. **Tool reference**: grouped Scenes, Sources and items, Outputs, Capture, Devices and media,
   Diagnostics, Waiting. Per tool an anchored card: name, verbatim description, badges from
   annotations (read-only / idempotent / destructive), inputs table (name, type, required, default,
   field description from schema), output fields, collapsible raw JSON. Errors section: the
   ToolError schema and the four codes, linking `/websocket/` status codes.
6. **Resources** (2) and **Prompts: none** stated plainly.
7. **For agents** box: the schema URL, `/mcp/index.md`, per-tool JSON, and "receipt" line (commit,
   date, source paths), per DESIGN.md principle 1.

Copy direction: imperative, short, no "AI-powered" adjectives. Never claim cross-platform or
"one-click". Where the upstream description is boilerplate ("vcam start: control and inspect OBS
directly.") show it verbatim and add a site-written summary under a visibly separate "Notes"
label sourced from control-api.md, so agents can tell protocol text from site prose.

## 4. Risks, open questions, upstream asks

Risks:
- **Regex parse is brittle** to macro or formatting changes. Mitigated by the snapshot set check
  and fail-closed; replaced by U1.
- **Weak descriptions**: 9 control tools say only "<x>: control and inspect OBS directly.", which
  hurts tool selection by agents. Upstream fix (U2), not a site rewrite of the schema.
- **Annotation semantics**: `MUTATING`/`IDEMPOTENT` set `openWorldHint: true` and
  `destructiveHint: true` even for `scene_create`/`record_start`; clients may over-prompt. Publish
  as-is; file U3.
- `vcam_start.audio_track` says "1 through 6" but schema has `minimum: 0`, no maximum (U3).
- Snapshot vs live drift is guarded only for structure; descriptions and resources have no
  upstream snapshot (U1).
- Promising usability the build cannot prove: keep requirements text tied to the cited files
  (`mcp.md`, `obs-build` usage string, `platform/unsupported.rs`) via `claims.toml` patterns.
- `server.json` may mislead registries/crawlers into thinking an install package exists: it has
  none, and the page says so.

Open questions:
- Do release artifacts (AppImage/deb/Flatpak) include a `bundled-native` binary able to run
  `--mcp`? If yes, a far simpler quickstart exists and an OCI/MCPB package becomes feasible.
- Does `tools/list` (libobs startup) succeed with no display at all, or must agents always have a
  compositor? Needed for the requirements box.
- Does the official registry accept a packageless `server.json`? Verify with `mcp-publisher
  validate` before any submission.
- Does `--mcp` build/run on macOS at all (stdio has no OS gating in `host.rs`, but the launcher and
  runtime stager are Linux-oriented)?

File upstream (obs-rust/obs-studio):
- **U1** Commit the *full* contract: extend `schema_snapshot()` (or add `mcp_manifest()`) to
  emit exactly `{initialize, tools/list, resources/list}` including descriptions, guarded by the
  existing drift test, at e.g. `docs/rust-port/mcp-manifest.json`. Plus `obs-studio-rust
  --print-mcp-schema` that prints it without starting libobs. Then the site reads one JSON from
  the docs sparse checkout and drops all Rust parsing.
- **U2** Real descriptions for vcam/vmic/media/stats/pipeline tools (the current text is a
  generated placeholder).
- **U3** Review annotation constants (openWorldHint for local OBS; destructive for create/start)
  and the `audio_track` bounds.
- **U4** Optional MCP polish: `instructions` in `initialize`, tool `title`s, resource `title`s; a
  `prompts` capability only if real prompts are designed.
- **U5** A publishable package for the registry: OCI image (headless Weston + `--mcp`, label
  `io.modelcontextprotocol.server.name`) or MCPB from release assets; then submit
  `server.json` with `packages[{registryType:"oci", transport:{type:"stdio"}}]`.
- **U6** Windows named-pipe transport is already #4455; link it, don't duplicate.

Site acceptance checks (add to `tools/check.py`): `/mcp/schema.json` tool names equal the
snapshot names; `/mcp/server.json` validates against the vendored 2025-12-11 schema; every tool has
a `/mcp/#<name>` anchor and a `mcp:tool:<name>` chunk; no number on `/mcp/` is hand-typed;
snippet command/args equal `.mcp.json`.
