# obs-rust.com — design document

Status: living document. Rewritten every other loop round by a fresh design pass.
Revision 1 — 2026-11-17.

## 1. Purpose

obs-rust.com is the front door for **obs-studio-rust** (`obs-rust/obs-studio`): the
independent, hybrid Rust/C/C++ rewrite of OBS Studio that keeps the libobs C ABI, the
obs-websocket v5 protocol and the plugin/scripting APIs compatible.

The site serves three audiences, in priority order:

1. **Users** who want to know what this is, whether it is real, and how to download it.
2. **Builders**: people driving OBS remotely (obs-websocket v5 clients, stream decks,
   bots, overlays) and plugin authors who need the API surface in one place.
3. **AI agents**, as readers and as contributors. They need a clean, complete,
   machine-readable text corpus (`llms.txt`, `llms-full.txt`, chunked JSON), plus the
   paste-in worker prompt that turns an agent into a contributor.

## 2. Principles

- **Receipts over claims.** Every number on the page (Rust vs C bytes, stars, latest
  release, request count) is computed at build time from GitHub or the protocol file.
  Nothing is hand-typed.
- **Static and fast.** Plain HTML, CSS and vanilla JS. No framework and no client bundle.
  The page reads correctly with JS off; JS only adds search, the live console and
  release lookups.
- **One source of truth.** API pages and the AI corpus are generated from
  `obs-rust/obs-studio` (README, `docs/`) and `obs-rust/obs-websocket`
  (`docs/generated/protocol.json`, pinned to the submodule commit obs-studio ships).
  Nothing is copied by hand, so nothing goes stale by hand.
- **Agent-first text.** Every human page has a text twin: `/llms.txt` is the index,
  `/llms-full.txt` the whole corpus, `/ai/corpus.json` the chunks, and
  `/websocket/protocol.json` the raw protocol.
- **Brand continuity.** It keeps the obs-rust/brand identity: forged steel plates, rust
  orange (`#e8631a`), copper-patina green (`#3fa58a`), hazard yellow, stencil display
  type and the bronze robot mascot. It should look like an engineered machine, not a
  SaaS template.

## 3. Visual language

| Token | Value | Use |
|---|---|---|
| `--bg` | `#0e0f10` → `#17191a` | page canvas; faint brushed-steel texture |
| `--plate` | `#24282b` | cards, panels |
| `--edge` | `#3d4246` | 1–2 px plate borders |
| `--rust` | `#e8631a` | primary accent, CTAs, Rust in charts |
| `--cu` | `#3fa58a` | secondary accent, links, "live" states |
| `--haz` | `#f2b705` | warning stripes, beta badges |
| `--c` | `#8a96a3` | C/C++ in charts (cold steel vs hot rust) |

Type: Big Shoulders Stencil Display for headlines, Barlow Condensed for body copy and
JetBrains Mono for code, labels and data.

Signature elements:

- **Hero "program monitor"**: an OBS-style preview frame with a live REC/LIVE tally, a
  timecode, animated audio meters and a scene list. It says "this is OBS" at a glance,
  in CSS with no video.
- **Crossover gauge**: one horizontal bar of Rust vs C vs C++ bytes, from GitHub's
  language API. Rust has passed C in the repository, and the bar shows it.
- Hazard-stripe dividers and riveted plates, used sparingly.

Motion: meters and the tally pulse; nothing else moves. `prefers-reduced-motion`
turns all of it off.

## 4. Information architecture

```
/                 Home: hero, crossover gauge, download, what's different, how it's built,
                  contribute-with-your-agent, project grid, footer
/websocket/       obs-websocket v5 API reference: 147 requests, 60 events, 7 enums,
                  live search and category filter, per-item anchors, a live console
                  that connects to ws://localhost:4455 from the browser
/examples/        Client snippets (Rust/obws, Python, JS, raw WebSocket), plugin and
                  scripting starters, client-library directory
/ai/              Corpus browser: full-text search over every chunk, a link to each
                  raw .md, and usage notes for agents
/llms.txt         llmstxt.org index
/llms-full.txt    the whole corpus, one file
/ai/corpus.json   [{id, title, source, url, heading, text}] chunks of about 1.5k chars
/ai/docs/*.md     one normalized markdown file per source document
/websocket/protocol.json   pinned upstream protocol file
/sitemap.xml, /robots.txt
```

## 5. Build

- `tools/build.py` (a `uv run --script` PEP 723 script) takes `--obs-studio <checkout>`
  and writes `_site/`. It fetches `protocol.json` and `protocol.md` at the obs-websocket
  submodule SHA recorded in the obs-studio checkout, and repo stats from the GitHub API
  (token optional).
- `src/` holds the hand-authored pages, templated with `{{key}}` placeholders that
  the build fills in.
- `.github/workflows/pages.yml` (the existing workflow, extended, with no new workflow
  file) checks out obs-studio (docs only, sparse), runs the build and deploys
  `_site/`. It runs on push, on dispatch and daily, so the docs and stats stay fresh.

## 6. Corpus scope

Included: the obs-studio README, AGENTS.md, BUILD.md, CONTRIBUTING.md, SECURITY.md,
`docs/*.md` (features ledger, CI tooling, GPU status...), `docs/rust-port/*.md`,
`docs/knowledge/*.md`, `docs/sphinx/*.rst` (the libobs C API reference), and the
obs-websocket protocol (narrative plus generated reference).

Excluded: images, `docs/rust-port/native-graph/` (generated graphs), dated CI audit
logs older than the current ones (all kept for now; revisit if the corpus passes 5 MB).

## 7. Backlog

- [ ] Port-progress page: per-module Rust/C status from the issue tracker.
- [ ] Features ledger rendered as a filterable "what's different" page.
- [ ] OG image generated at build time with live numbers.
- [ ] Client-side semantic search (small embedding index) on /ai/.
- [ ] Downloads page with per-OS detection and checksum display.
