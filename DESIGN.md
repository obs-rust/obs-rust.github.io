# obs-rust.com — design document

Revision 3 — 2026-11-18. Living document; supersedes Revision 2 (2026-11-18, in git history).

Revision 2 set a backlog; PRs #2 to #5 fixed the false number, added the gate, published
`/mcp/` and rebuilt the corpus. This revision judges what ships now, re-orders the rest
and defines done (§11). Figures here were measured on a build of `main` at b13a029
(obs-studio@7e68243cf) and on the live site. They are evidence, not site copy.

## 1. Position

> obs-studio-rust is real, it is OBS, and you can run it, script it and read all of it today.

| Audience | Job | Succeeds when |
|---|---|---|
| Streamers | Decide to try it | From `/` they see the real app, learn what works and what does not, and reach a verified installer for their OS in one click |
| Builders | Call OBS from code | They find a request or tool, see its fields and send it to their own OBS without leaving the page |
| AI agents | Answer or act correctly | Given only `https://obs-rust.com/llms.txt`, a cold agent answers an install, API, MCP or port-process question with a citable URL in three fetches or fewer |

When goals conflict: truth of a claim, then agent-readable text, then visual polish.

## 2. Shipped

| R2 item | What landed | PR |
|---|---|---|
| P0 #1 | libobs figure read from `conversion.json`, with a receipt (source, commit, date); linguist split labelled "whole repository" | #2 |
| P0 #5 | Mobile nav strip under 760 px, no JS | #2 |
| P0 #9 (part) | `/404.html` | #2 |
| new | `/mcp/`: 30 tools and 2 resources generated from `control-api.schema.json` and `rust/obs-mcp/src`; `schema.json`, `tools.json`, `server.json`, per-tool JSON, three sessions validated against the real schemas, client configs, read-only allowlist, `index.md` twin. Designs: `design/mcp-opus.md`, `design/mcp-fable.md` | #3 |
| P0 #2 | `tools/check.py` in `pages.yml`: expected files, placeholders, internal links, third-party origins, three budgets, sitemap, MCP parity, no hand-typed figures in the home copy | #4 |
| P0 #6 | Self-hosted fonts, 158 KB, zero third-party origins | #4 |
| P0 #8 | Corpus loads on first keystroke; `/ai/` lists every document as static HTML; no `autofocus` | #4 |
| P0 #4 (part) | `/llms-ctx.txt`, 204 KB, opens with the latest release and its assets | #4 |

| P0 #3, #4 | Corpus `schema_version` 2: 1672 chunks with structural ids, breadcrumb, tier, `url`, pinned `source`, `chars`, `tokens_est`, `sha256`; typed `ws-*`, `mcp-tool`, `ledger-entry`, `ledger-fix`; protocol indexed once; per-group `.jsonl`; front matter on `/ai/docs/*.md`. `llms.txt` v2: 36 links, first-sentence summaries, feed sizes, six sections | #5 |

Still open from Revision 2 and re-ranked in §10: the corpus residue (§3.10, §3.11),
`claims.toml`, the social card, and all of P1 and P2.

## 3. Critique of what ships now

**What still reads as generic**

1. **The hero is still a mock-up.** The monitor shows invented scenes ("Starting Soon",
   "BRB"), a fake "Live" lamp and a timecode driven by `requestAnimationFrame`
   (`src/index.html:251`). No pixel of the real application appears on any page: the
   sparse checkout in `pages.yml` still excludes `docs/images/`.
2. **The headline "Rust has passed C" rests on 38.7% against 38.4%** of linguist bytes
   and sits above "60.2% of libobs ported" and "Whole app 16.9% ported". Three figures
   with three denominators in one block: a reader cannot tell which one the claim is.
3. **The mascot is still missing.** The 404 page shows only the badge; the bronze robot
   is used only as `og:image`, a 768 KB square file declared as `summary_large_image`.
   `assets/obs-rust-logo.png` (643 KB) ships and nothing references it.
4. **The proof strip counts the wrong things.** "27 forks" is a vanity figure and "147
   WebSocket requests" is upstream's count, not ours.
5. **CSS is not a system yet.** A `<style>` block on every page, 16 inline `style=` on
   the home page, no `:focus-visible` rule anywhere, four Barlow weights where §6 has two.

**What a streamer still misses**

6. **A reason to trust the download.** No checksum on the page (the release publishes
   `SHA256SUMS`), no OS put first, no system requirements, no signing status.
7. **What does not work.** The page says "public beta" and nothing else: no known gaps,
   no way back, no statement of which plugins were actually loaded in tests.
8. **Their own changes.** The nine newest ledger entries lead with three about MCP
   internals. The 386 fixed upstream bugs, the strongest argument, are a number only.
9. **A wrong promise in every link preview.** The meta and `og:description` still say
   "with the crashes fixed", the absolute Revision 2 removed from the body.

**What an agent still misses**

10. **`llms.txt` v2 lists files, not tasks.** Nothing says which file answers which
    question; the download line leaves the site; the site's examples, download facts,
    CODESTYLE and the WebSocket-or-MCP choice are in no feed; there is no manifest.
11. **The corpus is typed but not yet tight.** 233 of 1335 prose chunks are still under
    300 characters and 6 exceed 2400 (largest 6.3k); the libobs C reference is prose,
    with no `c-symbol` chunk; chunk `url`s carry no anchor. Search still fetches the
    whole corpus on the first keystroke, now 2.4 MB (588 KB gzipped).
12. **Only `/mcp/` has a markdown twin.** No `rel="alternate"` elsewhere, no JSON-LD;
    the sitemap lists 10 URLs while 101 documents sit unlisted in `/ai/docs/`.
13. **Two control surfaces, no guidance.** WebSocket (147 requests, any OBS, remote) and
    MCP (30 tools, local, typed waits) are presented separately. Nothing says which to
    pick, and the site's own examples and the two control pages are not in the corpus.
14. **MCP adoption stops at a build.** The quick start is clone and `./mcp --build`;
    that Linux is the supported path and macOS untested appears only far down the page.
    `server.json` has no `packages` entry, so no registry or client can install it.

**What the gate does not yet prove**

15. `check.py` enforces three of the budgets in §8 and checks digits only in
    `src/index.html`; it has no anchor, unreferenced-asset, accessibility or receipt
    check. Nothing verifies the deployed site.

## 4. Principles

1. **Receipts, visibly.** Every figure is computed at build time and shows its source,
   commit and date. No receipt, no number.
2. **Use the project's own measures** (`conversion.json`, the features ledger,
   `protocol.json`, `control-api.schema.json`). The site never invents a metric.
3. **Show the thing.** The real application, release assets and sessions replace every
   imitation. A mock-up is a claim without a receipt.
4. **Say what does not work.** Limits and beta status sit beside the pitch, quoted from
   upstream files.
5. **Fail closed.** If a source cannot be fetched or parsed the build fails and
   yesterday's site stays up. Stale beats wrong.
6. **Text first, twin always.** Every HTML page has a markdown twin at a predictable
   URL. The corpus is a product with acceptance tests.
7. **Static, first-party, small.** No framework or third-party origin; JS is progressive
   enhancement. One generator (`tools/build.py`, `tools/mcp.py`) and one checker
   (`tools/check.py`), both through `uv run` in the existing `pages.yml`.

## 5. Information architecture

Top nav on every viewport: **Download · What's different · Control OBS · Examples · For
AI**. "Control OBS" opens `/control/`; WebSocket and MCP are also linked in every footer.

```
/                   Six sections: hero (real screenshot), proof strip, download,
                    what works and what does not, top of the ledger, builders and agents
/download/          Latest release by OS: sizes, SHA-256, requirements, install steps
/changes/           Whole features ledger: fixed bugs first, filterable, anchor per entry
/progress/          libobs conversion from conversion.json: gauge, modules, method
/control/           WebSocket or MCP: one comparison table, computed, then two doors
/websocket/         Single-page reference and live console
/websocket/<Name>/  One light page per request, event and enum; <Name>.md beside it
/mcp/               Server reference (shipped); /mcp/tools/<name>/ and <name>.md
/examples/          Examples rendered from checked files in examples/
/ai/                Agent entry point: task router, feeds, search
/404.html           Mascot, the nav links
/llms.txt           Curated, tiered, sized index; /llms-ctx.txt core; /llms-full.txt all
/ai/manifest.json   Every document and feed: url, title, summary, tier, bytes, sha256
/ai/corpus.json     Chunks (§7); /ai/search.json prebuilt index; /ai/docs/*.md
/<page>/index.md    Markdown twin of every HTML page; /assets/card.png (generated)
```

## 6. Visual system

The brand stays. Colour has fixed meaning; a colour used outside its meaning is a bug.

| Token | Value | Means |
|---|---|---|
| `--bg0/1/2`, `--plate`, `--edge` | `#0b0c0d` to `#24282b`, seams `#33383c` | canvas, steel plates, 1 px seams |
| `--rust` | `#e8631a` | Rust code, primary action, the one accent per view |
| `--cu` | `#3fa58a` | verified or computed: receipts, links, connected state |
| `--haz` | `#f2b705` | caution only: beta, untested, deprecated, destructive |
| `--red` | `#ff4040` | tally: on air, error. Never decoration |
| `--c`, `--cpp` | `#8a96a3`, `#5d6b7a` | legacy C and C++ in data graphics |
| `--fg`, `--fg2`, `--dim` | `#ece8e1`, `#c9c5bd`, `#8e949a` | text; `--dim` never under 13 px |

Type: **Big Shoulders Stencil Display 900** for h1, h2 and hero numerals (never under
28 px or over six words); **Barlow 400/600** for body and UI; **JetBrains Mono** for
code, labels, receipts and data. Layout: 1180 px max, 8 px scale, 4 px radius on
controls, 6 px on plates. All CSS lives in `assets/site.css`; no page `<style>` blocks,
and inline `style=` only for computed values.

Signature moments, four and only four:

1. **The program monitor.** Bezel, tally and dock stay; the contents become true. The
   screen is the upstream application screenshot, the lower third is the libobs figure
   with its receipt, the scene list is the site nav. No invented scene names, no running
   timecode. The tally lamp is unlit steel here.
2. **The receipt.** One component (`.receipt`, `data-src`, `data-rev`, `data-date`) in
   patina-green mono under every computed number, on every page. It is the proof mark.
3. **The conversion gauge.** libobs lines ported, rust filling cold steel. Exactly one
   headline figure per view; other denominators are labelled rows beneath it. The
   headline "Rust has passed C" is retired until `conversion.json` itself supports it.
4. **The tally light.** Lit red only for live state: the WebSocket console connection.

The bronze robot appears on `/ai/`, `/mcp/`, the 404 page and the social card, from one
file under 60 KB. Motion: CSS only, paused offscreen, off under `prefers-reduced-motion`.

## 7. Content and corpus

Voice: plain, specific, verifiable; no superlatives or absolutes. Every product claim
traces to an obs-studio file through `claims.toml` (id, page, source file, pattern that
must still match), so `check.py` fails when upstream drops it.

- **Streamers.** The proof strip is four receipts: libobs converted, upstream bugs
  fixed, user-visible changes, latest release and its date. A "what works, what does
  not" block quotes upstream (release criteria, README platform notes, signing policy).
  The ledger preview on `/` leads with fixed bugs and skips automation entries.
- **Builders.** `/control/` answers "which API" with a computed table (transport, where
  it runs, count of operations, auth, platforms, waits), then the two references.
- **Agents.** `/ai/` opens with a task router: a table from task (install, call the
  WebSocket API, drive OBS over MCP, contribute a port, find a C symbol) to the one file
  to fetch and its size. The same table is the head of `llms.txt`.

**Tiers**, by rule in `build.py`: `core` (README, AGENTS, CONTRIBUTING, SECURITY,
CODESTYLE, CONSTITUTION, ledger summary, generated `site/download.md`, `site/examples.md`
and `site/control.md`, MCP and WebSocket narrative) fills `llms-ctx.txt`; `reference`
(per-item WebSocket, MCP tools, libobs C API, BUILD); `process` (`docs/rust-port/*`,
`docs/knowledge/*`, `ci-tooling`); `archive` (dated audits, handoffs, hall of fame).

**Chunks** (shipped in #5; the rules stay the contract). Split on headings; each chunk
opens with its breadcrumb. Prose is 300 to 2400 characters: merge smaller sections into a
sibling or parent, split larger ones at paragraph, list item, then sentence, never inside
a fenced block or table. Typed chunks are one unit each: `ws-request`, `ws-event`,
`ws-enum`, `mcp-tool`, `mcp-resource`, `c-symbol`, `ledger-entry`, `ledger-fix`. Record:

```json
{"id": "ws:request:SetInputSettings", "doc": "obs-websocket-reference",
 "group": "websocket", "tier": "reference", "kind": "ws-request",
 "breadcrumb": ["obs-websocket v5", "Requests", "inputs", "SetInputSettings"],
 "url": "https://obs-rust.com/websocket/SetInputSettings.md",
 "source": "<permalink at the built commit, with line range for prose>",
 "text": "...", "chars": 0, "tokens_est": 0, "sha256": "..."}
```

Ids are structural: `<doc-slug>#<heading-path-slug>` (`~2` for overflow), `ws:<kind>:<Name>`,
`mcp:tool:<name>`, `c:<symbol>`. The top level carries `schema_version` and both commits.

**`llms.txt`.** At most 80 links, each `[title](url): summary` from the document's first
sentence. Head: two sentences on the project, the task router, every feed with bytes and
token estimate, then the six sections. `llms-ctx.txt` stays under 300 KB.

**Discoverability.** Markdown files open with front matter (`title`, `source`, `commit`,
`updated`, `tier`, `tokens_est`). Every HTML page carries `<link rel="alternate"
type="text/markdown">` and a visible "Text version" link. The sitemap lists every HTML
and markdown URL; the home page carries computed JSON-LD `SoftwareApplication`.

**Search and eval.** `/ai/search.json` is a prebuilt BM25 index with identifier-aware
tokens, loaded on first focus. `tools/eval_corpus.py` runs 30 or more checked-in pairs
of question and expected chunk id through the page's own ranking code. Embedding search
stays rejected: queries are mostly identifiers and the index breaks the size budget.

## 8. Budgets and accessibility

Enforced by `tools/check.py` on `_site/`. Current values in brackets.

| Budget | Limit |
|---|---|
| Third-party origins loaded by any page | 0 [0] |
| `/` HTML + CSS + JS, gzipped | 40 KB [HTML 8.4 KB] |
| `/websocket/` HTML, gzipped | 60 KB [33.9 KB] |
| `/mcp/` HTML, gzipped | 20 KB [13.0 KB] |
| `/ai/` bytes fetched before interaction, and on first search, gzipped | 30 KB [7.0 KB], 150 KB [588 KB] |
| Fonts, all files | 160 KB [158 KB], display face preloaded |
| Largest image on `/` | 120 KB, explicit `width` and `height` |
| Social card | 1200x630, under 200 KB, generated at build [768 KB square] |
| Shipped but unreferenced assets | 0 [1, 643 KB] |
| `llms.txt` / `llms-ctx.txt` | 80 links and 25 KB [36, 14.5 KB] / 300 KB [204 KB] |

Accessibility is WCAG 2.2 AA, checked statically where possible: computed contrast for
every text token on every surface token (body 4.5:1, stencil and borders 3:1); one `h1`,
no skipped level, `alt` on images, labels on inputs, a skip link and `main`; a visible
`:focus-visible` ring; targets at least 24x24 px; no horizontal scroll at 320 px; live
regions for result counts and console status; every page complete with JS disabled.

## 9. WebSocket reference and console

Sticky index left, reference centre, console docked right above 1200 px and as a bottom
sheet below, so "Try" never scrolls the reader away. Cards add a copyable deep link,
client one-liners generated from field types, related events and a "Text" link. "Try"
builds a typed form from `requestFields`; missing required fields disable Send and say
why. The log has pretty and raw views, an event filter from `EventSubscription` and
`RequestStatus` names. URL and subscriptions persist in `localStorage`; the password
never does. A failed connect names the likely cause and offers a `websocat` command.

## 10. Backlog

Ordered within each priority; R2 numbers in brackets. An item is done when its check
passes in `tools/check.py` (or the named command) on the built site.

### P0: finish the foundation, remove what is still untrue

| # | Item | Acceptance check |
|---|---|---|
| 1 | **Close the corpus residue** [R2 #3]. Merge the remaining short prose chunks, split the long ones, add `c-symbol` chunks for the libobs reference, give every chunk `url` an anchor. | No `prose` chunk outside 300..2400 chars except a single fenced block or table; one `c-symbol` chunk per Sphinx directive in the C reference; every chunk `url` resolves to a file on the site, with an anchor for prose; two builds from the same inputs give byte-identical `corpus.json` apart from the timestamp. |
| 2 | **Agent task router and `manifest.json`** [R2 #4]. Router table at the head of `llms.txt` and on `/ai/`; generated `site/download.md`, `site/examples.md`, `site/control.md`, plus CODESTYLE and CONSTITUTION, in core. | Each router row names a task, one URL that resolves and a size equal to the file on disk; the download row points at `obs-rust.com`; `llms-ctx.txt` contains the three `site/*.md` documents and stays under 300 KB; `manifest.json` lists every `/ai/docs/*.md` with a matching `sha256`. |
| 3 | **Real application in the hero** [R2 #12]. Add the screenshot path to the sparse checkout; monitor contents per §6; delete the timecode script. | The hero `<img>` is built from the obs-studio checkout, under 120 KB, with `alt`, `width` and `height`; the strings "Starting Soon" and "BRB" are absent from `_site/index.html`; no `requestAnimationFrame` in any shipped page; the build fails if the image is missing. |
| 4 | **One honest headline; `claims.toml`** [R2 #7]. Retire "Rust has passed C"; one headline figure per view; fix the meta description; replace the forks and upstream-request stats. | `grep -ri "crashes" _site/*.html` finds nothing; `/` has one `.headline` figure and every other figure is a labelled row with a `.receipt`; `check.py` fails when a `claims.toml` pattern no longer matches upstream; the digit check covers every `src/*.html`. |
| 5 | **Download block a streamer can trust** [R2 #13]. `/download/` and the home block: SHA-256 from the release's `SHA256SUMS`, requirements and install steps quoted from the README, visitor's OS first. | Every listed asset shows a size and a SHA-256 equal to the `SHA256SUMS` line; an unmatched `DL_GROUPS` suffix or a missing `SHA256SUMS` fails the build; with JS off all three OS cards and their hashes are present; `site/download.md` carries the same rows. |
| 6 | **Gate v2** [extends R2 #2]. All §8 budgets gzipped, anchor targets, unreferenced assets, one `h1`, `alt`, labels, `:focus-visible` present, every figure has a receipt. A post-deploy step in the existing `pages.yml` job fetches `/llms.txt`, `/mcp/index.md` and `/nope`. | `uv run tools/check.py _site` exits non-zero for each of: an added unreferenced file in `assets/`, a link to a missing `#anchor`, an `<img>` without `alt`, a number without `.receipt` on `/`; the deploy job fails if `/llms.txt` is not 200 `text/plain` or `/nope` is not 404. |
| 7 | **Social card and asset hygiene** [R2 #9]. Generated 1200x630 card with mascot, name and the libobs figure; delete the unused logo; mascot on the 404 page. | `og:image` on every page resolves to a 1200x630 file under 200 KB; no file in `_site/assets/` is unreferenced; `/404.html` contains the mascot image with `alt`. |

### P1: the pages that make the case

| # | Item | Acceptance check |
|---|---|---|
| 8 | **"What works, what does not"** on `/` and `/download/`: beta status, platform limits, signing, plugin loading evidence, how to go back to upstream OBS, each quoted from an upstream file. | Every sentence in the block has a `claims.toml` entry; the block contains at least one `--haz` limit; removing the source sentence upstream fails the build. |
| 9 | **`/changes/`** [R2 #10]: full ledger, fixed bugs first, filter by area, platform and text, anchor per entry; home preview excludes automation entries. | Entry count equals parsed ledger entries; each links its PR; filters work by URL query and the page reads complete with JS off; no "Headless and automation" entry in the home preview. |
| 10 | **`/control/` and the agent task router** on `/ai/` and in `llms.txt`. | Every figure in the comparison table equals `protocol.json` or `mcp/schema.json`; each router row's URL resolves and its printed size matches the file; `site/control.md` is in `llms-ctx.txt`. |
| 11 | **Markdown twins and discoverability** [R2 #18]: `index.md` per page, `rel="alternate"`, front matter, full sitemap, JSON-LD. | Every HTML page's alternate link resolves; every `.md` on the site starts with front matter holding a commit; the sitemap lists every HTML and `.md` URL; JSON-LD parses and its version equals the latest release tag. |
| 12 | **Home restructure** [R2 #14] to the six sections of §5. | `/` has six `<section>` elements; the download block starts within two viewport heights at 1440x900 and three at 390x844. |
| 13 | **MCP v2**: platform and build requirements stated in the first screen with receipts; per-tool pages and `.md`; sessions rendered from upstream transcripts when published; `server.json` valid against the vendored schema. | For every tool in `schema.json`, `/mcp/tools/<name>/index.html` and `<name>.md` exist and are in the sitemap; the first 1500 characters of `/mcp/index.md` name the supported platform; `server.json` validates against `tools/vendor/server.schema.json`. |
| 14 | **`/progress/`** [R2 #11] from `conversion.json`: gauge, by-module table, method and exclusions quoted from the file. | Every figure on the page appears in `conversion.json`; one receipt with commit and date. |
| 15 | **Retrieval eval and lazy index** [R2 #19, #8]: `/ai/search.json`, `tools/eval_corpus.py`. | At least 90% of 30+ questions have the expected chunk in the top 5, or the build fails; first search transfers under 150 KB gzipped; `SetInputSettings` ranks its `ws-request` chunk first and `wait_for` its `mcp-tool` chunk first. |
| 16 | **Examples as files** [R2 #16]: `examples/<lang>/*`, highlighted at build, served raw. | Every `requestType`, event and MCP tool name used in `examples/` exists in `protocol.json` or `mcp/schema.json`; Python examples pass `uv run python -m py_compile`. |
| 17 | **CSS consolidation and accessibility pass** [R2 #20, #21]. | No `<style` in any `_site/**/*.html`; inline `style=` sets only custom properties or `flex`; contrast and structure checks pass; exactly two Barlow weights ship; a keyboard-only walk of each page is recorded in the PR. |
| 18 | **Per-item WebSocket pages and `.md`** [R2 #17]. | For every name in `protocol.json`, `/websocket/<Name>/index.html` and `/websocket/<Name>.md` exist and are in the sitemap. |
| 19 | **Console v2** [R2 #15] per §9. | Sending with an empty required field is blocked with a message; a failed connect shows the fallback command; `localStorage` never holds the password; scroll position is unchanged after "Try". |

### P2: depth

| # | Item | Acceptance check |
|---|---|---|
| 20 | `/websocket/obs-websocket.d.ts` generated from the protocol [R2 #22]. | `tsc --noEmit` accepts it; one request type per `protocol.json` request. |
| 21 | `/libobs/` symbol index linking `c-symbol` chunks [R2 #23]. | Every `c-symbol` chunk id resolves to an anchor on the site. |
| 22 | Topic bundles `/ai/bundles/*.txt` [R2 #24]. | Each bundle is under its budget and listed with its size in `llms.txt`. |
| 23 | Installable MCP: `packages` in `server.json` once obs-studio ships the server in a release. | The package URL in `server.json` equals a release asset and its hash equals `SHA256SUMS`. |
| 24 | Contributor strip from `leaderboard.json` [R2 #25]. | Figures equal the JSON at build time, with a receipt. |
| 25 | Release feed `/releases.xml` (Atom) [R2 #27]; launch-speed figure once published as data [R2 #26]. | The feed validates and its newest entry equals the latest tag; the figure is read from JSON, never parsed from prose. |

## 11. The done bar

An independent judge gives **LGTM** only when every line below holds on the deployed
site, and **FAIL** otherwise, naming each failed line. Nothing is taken on trust.

**A. Gates (mechanical; any failure is FAIL)**

1. `uv run tools/build.py` then `uv run tools/check.py _site` exit 0 from a clean clone,
   and the last `pages.yml` run on `main` is green. P0 items 1 to 7 pass their checks.
2. Every budget in §8 holds, measured by the judge and not read from the build log.
3. Ten figures sampled across pages each equal their named source at the commit in
   their receipt. One mismatch, or one figure without a receipt, is FAIL.
4. No page loads a third-party origin; every page is readable and navigable with JS off.
5. Nothing on the site imitates the product: no invented scene, state or number.

**B. Cold trials (each run once, fresh, with no prior context)**

6. **Streamer.** From `/` on a 390 px viewport: identify what the app looks like, name
   one thing that does not work yet, and reach the correct installer and its SHA-256 for
   a stated OS, within three taps and without leaving the site until the download.
7. **Builder.** From `/`: decide between WebSocket and MCP for a stated task, find one
   named request with its fields, and copy a snippet that is checked against the
   protocol, within three clicks.
8. **Agent, reading.** A model given only the `llms.txt` URL and one fetch tool answers
   five questions (install on a stated OS, one WebSocket request's fields, one MCP
   tool's input schema, how to claim an issue, what percent of libobs is ported) with
   at most three fetches each, four of five correct, every answer citing a URL that
   contains the cited fact.
9. **Agent, acting.** A model given only `/mcp/index.md` writes a client config and a
   three-call session; both validate against `/mcp/schema.json`, and it states the
   platform requirement correctly.

**C. Judgement (two or more failures is FAIL)**

10. Above the fold, `/` could not be mistaken for a template: the real application, one
    headline figure with its receipt, and one primary action.
11. No sentence is a superlative, an absolute or a claim without a source.
12. The four signature moments of §6 are present, and no fifth decoration has appeared.
13. Colour is used only with the meanings of §6; hazard and tally mark real states.
14. Limits are as easy to find as the pitch: beta, platforms and untested paths are on
    the page that makes the matching promise.

## 12. Non-goals

No framework, bundler, analytics, cookie banner or third-party embed. No server-side
search, hosted MCP endpoint or embedding service. No hand-edited copy of upstream docs.
No blog, no light theme, no new workflow files. No claim the build cannot check.
