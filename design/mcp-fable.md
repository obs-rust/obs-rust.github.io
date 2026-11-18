# /mcp/ — publishing the obs-studio-rust MCP schema (design, agent-experience angle)

Read against obs-studio `origin/master @ 7e68243cf`. Counts and names below are evidence from that commit;
the site computes them at build time and never types them.

## 0. Position

Two readers decide whether this server gets used. The **human configuring an agent** asks: what will it
touch, can I let it look without letting it go live, how long until it works? The **agent** asks: which
tool fits, what are the exact argument names, what comes back, what do I do when it fails? The page
answers the human in the first screen and the agent in one fetch. Everything is generated from the file
upstream already guards with a test: `docs/rust-port/control-api.schema.json`, held equal to the
registered types by `schema_snapshot_has_not_drifted` (`rust/obs-mcp/tests/mcp/typed.rs:89`). The site
does not build OBS and hosts no endpoint (DESIGN.md §12).

## 1. What the server really exposes (verified)

`initialize` returns `protocolVersion: "2025-06-18"`, `serverInfo: {name: "obs-mcp", version: "0.1.0"}`,
`capabilities: {tools: {}, resources: {}}` (`rust/obs-mcp/src/server/dispatch.rs:14-22`). Methods:
`initialize`, `ping`, `tools/list`, `tools/call`, `resources/list`, `resources/read`; anything else is
`-32601`. Framing is one JSON message per line.

**Tools: 30**, each with `inputSchema`, `outputSchema` and `annotations`:

| Source file | Tools |
|---|---|
| scenes | `scenes_list`, `scene_get_current`, `scene_set_current`, `scene_create`, `scene_remove` |
| sources | `sources_list`, `source_create`, `source_remove`, `source_set_settings`, `scene_item_add`, `scene_items_list`, `scene_item_set_visible`, `scene_item_set_transform` |
| outputs | `record_start`, `record_stop`, `record_status`, `stream_start`, `stream_stop`, `stream_status` |
| control | `vcam_start`, `vcam_stop`, `vcam_status`, `vmic_status`, `media_restart`, `media_status`, `stats_get`, `stats_reset`, `pipeline_dump` |
| screenshot, waiting | `screenshot`, `wait_for` |

By annotation: 13 have `readOnlyHint: true`; 8 are idempotent state changes (the six start/stop tools,
`scene_set_current`, `scene_item_set_visible`); 9 are plain mutations.

**Resources: 2**, both `application/json`: `obs://scenes` (`{current, scenes, sources}`) and `obs://stats`
(`{fps, cpu_usage, dropped_frames}`).

**Prompts: none.** No `prompts` capability; `prompts/list` is method-not-found. The site says so, publishes
`"prompts": []`, and calls its own task write-ups "recipes".

**Errors.** Bad or unknown arguments are JSON-RPC `-32602` (inputs use `deny_unknown_fields`). Domain
failures are results with `isError: true` and `structuredContent` of `ToolError {code, category, message,
retryable}`; codes follow obs-websocket v5 (600, 207, 604, 702); `category` is `not_ready`, `wrong_state`
or `processing` (`rust/obs-mcp/src/server/typed.rs:41-99`).

## 2. What to publish

| URL | Contents | Why an agent wants it |
|---|---|---|
| `/mcp/tools.json` | Exactly a `tools/list` result: `{"tools":[{name, description, inputSchema, outputSchema, annotations}]}` | Load it as if the server had answered; plan before anything is built |
| `/mcp/resources.json` | Exactly a `resources/list` result | Same |
| `/mcp/manifest.json` | `{schema_version, commit, schema_source, protocolVersion, serverInfo, capabilities, transports, prompts: [], toolError, counts, limits, requirements}` plus the URLs of the rest | One fetch that says what this is |
| `/mcp/schema.json` | The upstream snapshot, byte-identical | The receipt: diff it against upstream |
| `/mcp/<tool>/`, `/mcp/<tool>.md`, `/mcp/index.md` | One light page and markdown twin per tool; twin of the page | Deep links and single-tool retrieval |
| `/mcp/sessions/<slug>.jsonl` | The example sessions as raw request/response lines | Few-shot material to copy call by call |
| `/mcp/config/<client>.{json,toml}` | Each client config as a raw file | `curl -o` beats copying from HTML |
| `/mcp/allow-read-only.json` | Names with `readOnlyHint: true` and ready permission strings (`mcp__obs__scenes_list`, ...) | A human grants "look, don't touch" in one paste |

**Descriptions are not in the snapshot** (`tool_schema` omits prose on purpose). Until U1 lands, `build.py`
reads them from the `typed_tool!` invocations and the `screenshot` `fn description`, and fails if the names
it finds differ from the snapshot's.

**Registry `server.json`: not yet.** The registry lists servers a client can install (npm, PyPI, OCI,
NuGet, MCPB) or reach at a URL. This server is neither; it is built from a git checkout. A listing that
cannot be installed misleads the agent at the moment it trusted us. Publish when U8 ships an installable
artifact; `manifest.json` carries the same identity fields, so conversion is mechanical. The page says
"not in the MCP registry yet" and why.

**`/.well-known/`: nothing.** The circulating proposals (server cards, `/.well-known/mcp*`) describe remote
HTTP servers at the origin that hosts them and are not in the `2025-06-18` revision this server declares.
obs-rust.com hosts no server; a card would advertise an endpoint that does not exist.

**Discovery hooks that do exist.**

- `llms.txt`, section "Control OBS": `/mcp/index.md`, `/mcp/tools.json`, `/mcp/manifest.json`, each with a
  build-extracted summary and size; the header sentence gains "ships a local MCP server (N tools)".
- `llms-ctx.txt` includes `/mcp/index.md` (core tier); the per-tool reference is `reference` tier with its
  own bundle `/ai/bundles/mcp.txt`.
- Corpus: typed chunks `mcp-tool`, `mcp-resource`, `mcp-session`, one each, never split; ids
  `mcp:tool:record_start`, `mcp:resource:obs://stats`; `source` is the snapshot permalink.
- `<link rel="alternate">` for `text/markdown` (`/mcp/index.md`) and `application/json` (`/mcp/tools.json`);
  every `/mcp/` URL in `sitemap.xml`.

**Client configs**, generated from one table in `build.py`. `<repo>` is the absolute checkout path; the
page asks for it once in a text box and substitutes it (with JS off it stays `<repo>`).

| Client | File | Shape |
|---|---|---|
| Claude Code, in the repo | `.mcp.json` (committed upstream) | `{"mcpServers":{"obs":{"command":"./mcp","args":["--mcp"]}}}` |
| Claude Code, elsewhere | shell | `claude mcp add obs -- <repo>/mcp --mcp` |
| Claude Desktop, Cursor | `claude_desktop_config.json`, `.cursor/mcp.json` | same object, `"command": "<repo>/mcp"` |
| VS Code | `.vscode/mcp.json` | `{"servers":{"obs":{"type":"stdio","command":"<repo>/mcp","args":["--mcp"]}}}` |
| Codex | `~/.codex/config.toml` | `[mcp_servers.obs]`, `command = "<repo>/mcp"`, `args = ["--mcp"]` |
| Any, your running OBS | as above | `"args": ["--mcp-attach"]` (default socket `$XDG_RUNTIME_DIR/obs-studio-rust/control.sock`) |

Two notes sit directly under the table, because they are where setups fail: `./mcp` is relative, so it
works only when the client starts in the repo root; and the launcher builds incrementally before serving,
so run `./mcp --build` once first or the client's startup timeout fires during a cold build.

## 3. The /mcp/ page

Nav stays at five items. `/mcp/` is the first card on `/ai/`, a link in the home "builders" section and in
the footer beside `/websocket/`. (Open question for the merge: rename "WebSocket API" to "Control APIs".)

### 3.1 Order of the page

1. **Hero.** Stencil h1 "GIVE YOUR AGENT OBS". Sub-line: "A local MCP server inside obs-studio-rust. It
   calls libobs directly, with typed inputs and outputs." Left plate: the config with a copy button and
   `./mcp --build`. Right plate, the **hero moment**: a four-message transcript, `wait_for` then
   `record_start`, argument and result fields highlighted. Under it the receipt: `30 tools · 2 resources ·
   control-api.schema.json @ 7e68243 · <date>`, all computed. No animation; the tally light stays unlit,
   because nothing on this page is connected to anything.
2. **Two modes, one choice**, the decision the human must make, as two plates. *Its own OBS* (`--mcp`):
   the stdio server "owns its own instance", a sandbox separate from the OBS you have open; right for
   building scenes, tests, CI. *Your running OBS* (`--mcp-attach`): needs `obs-mcp-module` built and
   installed, and acts on the live application; hazard badge.
3. **What it can and cannot do.** Three columns from annotations: Look (13), Switch (8), Change (9). Then a
   short "Not here yet" list linking the §5 issues (audio, source-kind discovery, stream network health,
   events). Saying what is absent stops an agent from guessing a tool name.
4. **Requirements** as a checklist, one source link per line (§3.4).
5. **Sessions** (§3.3): four tabs, each also a `.jsonl`.
6. **Reference** (§3.2), with a filter box and a read-only toggle.
7. **Errors and limits**: the `ToolError` table and the limits to plan around: `timeout_ms` defaults to
   5000 and may not exceed 300000; requests are serial; `wait_for` blocks the control thread; at most 32
   socket clients; 16 MiB per frame.
8. **Machine-readable**: the table of §2 with sizes, and the allowlist snippet.

### 3.2 Per-tool reference

Grouped by what the agent is trying to do, not by source file: **See** (`scenes_list`, `scene_get_current`,
`sources_list`, `scene_items_list`, `screenshot`, `pipeline_dump`), **Compose** (scene, source and item
mutations), **Go live** (record, stream, vcam, vmic), **Media**, **Measure** (`stats_get`, `stats_reset`),
**Wait** (`wait_for`). Membership is a checked table; a tool in no group fails the build. Each card:

- Name in mono with a copyable anchor. Badge from annotations: `read-only` in patina green, `idempotent` in
  steel, `changes state` in rust orange. The four raw hints are printed too, since clients read those.
- The upstream description verbatim. For the nine placeholder strings ("vcam start: control and inspect
  OBS directly.") the card shows the doc comments of the input and output types and links U2. We do not
  write our own description.
- **Arguments** from `inputSchema`: name, type, required, default, description; `$ref` resolved and enums
  listed. `wait_for` shows its four condition shapes (`output_state`, `source_active`, `media_state`,
  `stat_at_most`) and six metrics as sub-tables.
- **Returns** from `outputSchema`; nullable fields say what null means, quoted from the schema ("null until
  independently measured").
- **Call it**: a `tools/call` line with minimal valid arguments synthesized from the schema, and the shell
  form `printf '%s\n' '<line>' | ./mcp --mcp`.
- **Fails with**: only the `ToolError` constructors the tool's module calls. **Pairs with**: from
  `mcp/relations.toml` (`record_start` → `wait_for`, `record_status`), every name validated.

### 3.3 Example sessions

Stored as `mcp/sessions/*.jsonl` in the site repo, rendered as a two-column transcript with one short
sentence of agent reasoning between calls. Until U7 provides recorded transcripts each carries the label
"Schema-validated example; values are illustrative", which check C4 makes true.

**A. Start recording when the scene is ready.**

```
> {"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"agent","version":"1"}}}
< {"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2025-06-18","serverInfo":{"name":"obs-mcp","version":"0.1.0"},"capabilities":{"tools":{},"resources":{}}}}
> {"jsonrpc":"2.0","method":"notifications/initialized"}
> {"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":"scene_set_current","arguments":{"name":"Interview"}}}
< {"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"{\"name\":\"Interview\"}"}],"structuredContent":{"name":"Interview"},"isError":false}}
> {"jsonrpc":"2.0","id":3,"method":"tools/call","params":{"name":"wait_for","arguments":{"condition":{"type":"source_active","name":"Camera"},"timeout_ms":10000}}}
< {"jsonrpc":"2.0","id":3,"result":{"content":[...],"structuredContent":{"satisfied":true,"elapsed_ms":180,"last_value":{"kind":"source","present":true,"active":true}},"isError":false}}
> {"jsonrpc":"2.0","id":4,"method":"tools/call","params":{"name":"record_start","arguments":{"wait":true,"timeout_ms":5000}}}
< {"jsonrpc":"2.0","id":4,"result":{"content":[...],"structuredContent":{"active":true},"isError":false}}
```

Beside it, the unhappy branches, which are what make an agent trust a server. The camera never comes up:
`wait_for` returns `satisfied: false` with `last_value: {"kind":"source","present":true,"active":false}`,
and the agent does not record and says why. The start times out:
`"structuredContent":{"code":207,"category":"not_ready","message":"output start timed out","retryable":true},"isError":true`.

**B. Check if the stream is healthy.** Three read-only calls, all allowed under the read-only allowlist:

```
> "name":"stream_status","arguments":{}
< "structuredContent":{"active":true,"duration_ms":1804000,"bytes":1352000000}
> "name":"stats_get","arguments":{}
< "structuredContent":{"render":{"active_fps":60.0,"average_frame_time_ns":2100000,"render_total_frames":108240,"render_skipped_frames":3},
    "stages":{"render":{"live":true,...},"vcam":{...},"vmic":{...}},"end_to_end":{"av_offset_ms":null,"measured_from":"..."}}
> "name":"wait_for","arguments":{"condition":{"type":"stat_at_most","metric":"render_frames_dropped","value":10},"timeout_ms":0}
< "structuredContent":{"satisfied":true,"elapsed_ms":0,"last_value":{"kind":"stat","metric":"render_frames_dropped","value":3}}
```

The caption matters as much as the calls. This shows the output is active, bytes are moving (call
`stream_status` twice and compare `bytes`) and the renderer keeps up. It does **not** show network drops,
bitrate, congestion or reconnects: the server has no such field today (U4). An agent told this will not
invent a verdict.

**C. Add a source and verify it by looking.** `source_create` with `scene`, `scene_items_list`,
`scene_item_set_transform`, then `screenshot` and its `image` content. The tool's own warnings are quoted:
a source shows in program output only once it is an item of the program scene; empty pixels are transparent.

**D. Read state without a tool.** `resources/list`, then `resources/read` of `obs://scenes`.

### 3.4 Requirements, as the code states them (each line is a `claims.toml` entry)

- **Local only.** stdio, or a unix socket with mode 0600. No network listener and no auth layer.
- **Built from source.** `./mcp --build` needs `uv`, `soldr` and the native libobs build dependencies; on
  NixOS the launcher enters `ci/mcp-shell.nix` itself. No release artifact is documented as carrying the
  server, so the page claims none.
- **Linux is the documented path.** The launcher builds EGL/Wayland OpenGL, `linux-v4l2`, `obs-ffmpeg` and
  `obs-x264`. The socket transport is `cfg(unix)`; elsewhere it returns "local control transport
  unavailable", with Windows named pipes tracked in obs-rust/obs-studio#4455. macOS appears in no MCP doc:
  the page says "untested" and nothing more.
- **Video needs a display server**: a reachable Wayland compositor or X server (headless Weston works).
  Quoted verbatim: "A successful tools/list response alone does not prove video or device readiness."
- **Record and stream need configured outputs.** No tool configures a service or recording path (U5).
- **Annotations are advisory.** Quoted: "clients must still enforce their own policy". Hence the allowlist.

## 4. Keeping it accurate

**Inputs**, added to the sparse checkout already in `pages.yml` (no new workflow):
`docs/rust-port/control-api.schema.json`, `docs/rust-port/{mcp,control-api}.md`, `.mcp.json`,
`rust/obs-mcp/Cargo.toml`, `rust/obs-mcp/src/{tools,resources,server,platform}/`.

**Extraction in `tools/build.py`** (`uv run`, no Rust toolchain). Tools, schemas, annotations and
`toolError` come from the snapshot, the single authority for names and shapes. Descriptions come from
`typed_tool!` blocks (until U1). Resources come from the `fn uri/name/description/mime_type` literals and
the `json!` body in `src/resources/*.rs`. Identity comes from `PROTOCOL_VERSION` and the capabilities
literal in `dispatch.rs`, `version` in `Cargo.toml`, limits from `DEFAULT_TIMEOUT_MS`/`MAX_TIMEOUT_MS`.
The repo `.mcp.json` is embedded verbatim. Every regex fails closed: zero matches, or a count that
disagrees with the snapshot, stops the build and yesterday's site stays up.

**Acceptance checks (`tools/check.py`):**

| # | Check |
|---|---|
| C1 | `/mcp/schema.json` is byte-identical to the snapshot; the manifest `commit` equals the checkout HEAD |
| C2 | Names in `/mcp/tools.json` = names in the snapshot = `typed_tool!`/`NAME` names in source; every tool has a non-empty description, both schemas and annotations |
| C3 | Every tool has a card, a group, `/mcp/<tool>/index.html`, a `.md`, a sitemap entry and one `mcp-tool` chunk |
| C4 | Sessions: every `tools/call` names a real tool; `arguments` validate against its `inputSchema`; every `structuredContent` validates against the `outputSchema`, or `toolError` when `isError`; `content[0].text` parses to the same value; resource URIs exist; `initialize` results equal the extracted identity |
| C5 | Every backticked tool-like token on `/mcp/` pages and in `relations.toml` is a tool; every `obs://` URI is a resource |
| C6 | Each config parses and equals the repo `.mcp.json` modulo the path prefix; `--mcp`, `--mcp-listen`, `--mcp-attach` still occur in `docs/rust-port/mcp.md` |
| C7 | Manifest `prompts` is `[]` exactly when `capabilities` has no `prompts` key; no site recipe is labelled a prompt |
| C8 | No `server.json` and no MCP file under `/.well-known/` while `requirements.install` is `source` |
| C9 | The three annotation counts on the page equal those computed from the snapshot; `allow-read-only.json` equals the `readOnlyHint` set |
| C10 | `claims.toml` patterns for §3.4 still match upstream; a placeholder description rendered as prose fails |
| C11 | Retrieval eval gains five questions (start recording, wait for a source, meaning of 207, is there a prompt, attach to a running OBS), expected chunk in the top 5 |
| C12 | `/mcp/` HTML under 60 KB gzipped, `/mcp/index.md` under 30 KB, complete with JS off; post-deploy fetch of `/mcp/tools.json` returns 200, JSON, non-empty `tools` |

## 5. Upstream issue proposals (obs-rust/obs-studio)

Ordered by how much each changes whether an agent picks this server and then succeeds.

- **U1. Publish a complete server manifest.** Extend the snapshot (same drift test) with `description` per
  tool, the resources, `protocolVersion`, `serverInfo`, `capabilities`; add `./mcp --print-manifest` that
  needs no libobs start. Removes every regex in §4.
- **U2. Real descriptions for the nine control tools.** `vcam_start`, `vcam_stop`, `vcam_status`,
  `vmic_status`, `media_restart`, `media_status`, `stats_get`, `stats_reset`, `pipeline_dump` all read
  "<name>: control and inspect OBS directly." A model selects tools by description; these are unselectable.
  Test: no shared boilerplate, and each names its key output fields.
- **U3. Calibrate annotations, add `title`.** `MUTATING` sets `destructiveHint` and `openWorldHint` true for
  everything that writes, so `scene_set_current` looks as dangerous as `source_remove` and `stats_reset`
  claims to reach the outside world. Clients prompt on all of it, or the human turns prompts off for all
  of it. Proposal: destructive only for `scene_remove` and `source_remove`; open-world only `stream_start`.
- **U4. Stream health an agent can judge.** `stream_status` returns only `active`, `duration_ms`, `bytes`.
  Add `dropped_frames`, `total_frames`, `congestion`, `bitrate_kbps`, `reconnecting` and matching
  `wait_for` metrics; for record add `paused` and the output path.
- **U5. Close the loop on setup.** `source_kinds_list` and `source_get_settings` (today `source_create`
  requires a `kind` the agent cannot discover, and `source_set_settings` merges blind); tools to read and
  set the stream service and recording path; audio: `input_mute_set`, `input_volume_set`, `input_levels_get`.
- **U6. `instructions` in `initialize`; one stats vocabulary.** A short `instructions` string: inspect
  before mutating, `wait_for` instead of polling, the 300000 ms cap, and which instance this session
  controls. Give `obs://stats` the field names of `stats_get`, or drop it.
- **U7. Recorded golden transcripts.** The Tier 4 `mcp_stdio` test writes
  `docs/rust-port/mcp-sessions/*.jsonl` for scripted tasks, guarded like the schema. The site replaces its
  illustrative sessions and drops the label.
- **U8. An installable artifact.** Ship the server in release builds, or an MCPB bundle. Precondition for
  an honest registry `server.json`, and it removes the largest adoption cost: a native build.
- **U9. Prompts and events.** A `prompts` capability with real workflows (`preflight_check`, `go_live`,
  `diagnose_dropped_frames`); `resources/subscribe` with `notifications/resources/updated` for
  `obs://scenes`, so agents stop polling. Link `https://obs-rust.com/mcp/` from `docs/rust-port/mcp.md`.
- **U10. Safety switches for the human.** `--mcp-read-only` (register only `READ_ONLY` tools) and
  `--mcp-allow <tool,...>`. Server-side enforcement is what lets someone point an agent at a live OBS.
- Already tracked: Windows named-pipe transport, obs-rust/obs-studio#4455.

## 6. Backlog lines for DESIGN.md §11

- P1: `/mcp/` page with `tools.json`, `resources.json`, `manifest.json`, `schema.json`, configs, allowlist (C1, C2, C6, C8, C9).
- P1: per-tool pages, `.md` twins, `mcp-tool` chunks, `llms.txt` lines (C3, C5, C11); four validated sessions (C4).
- P2: switch to the upstream manifest and recorded transcripts when U1 and U7 land; `server.json` when U8 lands.
