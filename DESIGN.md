# obs-rust.com — design document

Status: living document. Rewritten every other loop round by a fresh design pass.
Revision 2 — 2026-11-18. Supersedes Revision 1 (2026-11-17).

Revision 1 described the site as built. This one judges it and sets direction. Figures
quoted here come from the `_site/` build of 2026-11-18: evidence, not site copy.

## 1. Position

obs-rust.com exists to make one sentence believable and then actionable:

> obs-studio-rust is real, it is OBS, and you can run it, script it and read all of it today.

The site shows computed evidence and hands each visitor the next step. Three audiences:

| Audience | Job | Succeeds when |
|---|---|---|
| Users | Decide to try it | They reach the right installer for their OS in one click from `/` |
| Builders | Call OBS from code | They find a request, see its fields and send it to their own OBS without leaving the page |
| AI agents | Answer or act correctly | A cold agent given only `https://obs-rust.com/llms.txt` answers an install, API or port-process question with a citable source URL |

When goals conflict, the order is: truth of a claim, then agent-readable text, then
visual polish. A beautiful page with a wrong number is a failure.

## 2. Critique of what ships

Each finding is answered by a backlog item in §11.

**Claims**

1. **The hero states a false number.** `src/index.html:123` renders "libobs now
   {{rust_pct}}% Rust", but `rust_pct` is GitHub's language share of the whole
   repository (`tools/build.py:83`). The project's own libobs measure (`conversion.json`
   on the `leaderboard` branch) is different and much higher: we misreport and undersell.
2. **The headline metric is the wrong one.** "Rust has passed C" rests on a sub-percent
   linguist margin that counts vendored code and can flip on any merge.
3. **"The crashes go away"** (`src/index.html:110`) is an absolute nobody can verify.
4. **The strongest evidence is buried.** Nine ledger cards, then a link to a 200 KB
   markdown file. And no picture of the product: the hero is a CSS imitation of OBS,
   while `docs/images/appimage-main-window.png` sits upstream, excluded.

**Structure and UX**

5. **Mobile has no navigation** (`assets/site.css:41` hides it under 760 px), there is
   no 404 page, and the home page runs eight sections, two of them on process.
6. **Download matching is silent.** `DL_GROUPS` hard-codes asset suffixes; a rename
   degrades to "See release" without failing. No checksums, no OS highlight.
7. **Examples are hand-highlighted HTML**: not runnable, not checkable, not fetchable.
8. **The WebSocket reference is one 316 KB page with anchors only**, a raw JSON box,
   and a "Try" button that scrolls the reader away from what they were reading.

**AI corpus**

9. **`llms-full.txt` is 1.7 MB**, over 400k tokens, sold on `/ai/` as something "to
   paste into a context window". `llms.txt` descriptions are file paths, and dated CI
   audits rank beside the README.
10. **Chunking is naive.** Of 1824 chunks, 129 are under 120 characters, 35 exceed 2400,
    the largest is 24.7k, and the protocol is indexed twice (583 chunks, a third of all).
11. **Chunk ids are positional** (`slug#n`, `tools/build.py:499`): any upstream edit
    renumbers them. Chunks carry no anchor URL, pinned permalink or size.
12. **`/ai/` fetches 2.3 MB of JSON on load** (500 KB gzipped) for a substring scan,
    steals focus with `autofocus`, and is empty without JS.
13. **Missing**: the site's examples, install and download facts, `CODESTYLE.md`,
    `CONSTITUTION.md`, markdown twins of pages, markdown URLs in the sitemap, JSON-LD.

**Visual system and performance**

14. **Render-blocking third-party fonts**, four families (`tools/build.py:389`).
15. **The mascot is absent** except as `og:image`, a 768 KB square PNG; a 643 KB logo
    PNG ships unused. CSS is scattered over one sheet, a `<style>` block per page and
    30 inline `style=` attributes.
16. **Motion costs more than it earns**: `requestAnimationFrame` runs forever to
    animate an `aria-hidden` timecode.
17. **Nothing enforces the rules.** "Every number is computed" and "works without JS"
    are promises with no check.

## 3. Principles (revised)

1. **Receipts, visibly.** Every figure is computed at build time and shows its source,
   commit and date. No receipt, no number.
2. **Use the project's own measures** (`conversion.json`, the features ledger,
   `protocol.json`). The site never invents a parallel metric.
3. **Fail closed.** If a source cannot be fetched or parsed the build fails and
   yesterday's site stays up. Stale beats wrong.
4. **Text first, twin always.** Every HTML page has a markdown twin at a predictable
   URL. The corpus is a product with acceptance tests, not a by-product.
5. **Static, first-party, small.** No framework, no third-party origin. JS is
   progressive enhancement and loads data only on intent.
6. **One generator, one checker.** `tools/build.py` writes `_site/`; `tools/check.py`
   proves this document's rules. Both run in `pages.yml`. No new workflow files.
7. **Machine, not SaaS.** Few colours with fixed meanings, one display face, little motion.

## 4. Information architecture

Top nav, five items, same on every viewport: **Download · What's different · WebSocket
API · Examples · For AI**. GitHub star count sits right. Under 760 px the list becomes a
horizontally scrollable strip under the brand row (no hamburger, no JS).

```
/                   Pitch in six sections: hero, proof strip, download, compatibility
                    contract, top of the ledger, builders and contributors
/download/          Latest release by OS: sizes, checksums, install steps from the README
/changes/           The whole features ledger, filterable, one anchor per entry
/progress/          libobs conversion from conversion.json: headline, modules, method
/websocket/         Single-page reference and live console (primary UX)
/websocket/<Name>/  One light page per request, event and enum; <Name>.md beside it
/examples/          Runnable examples rendered from files in examples/
/ai/                Agent entry point: feeds, search, usage recipes
/404.html           Mascot, search box, the five nav links

/llms.txt           Curated index (llmstxt.org), described and tiered
/llms-ctx.txt       Core bundle that fits a 128k-token window
/llms-full.txt      Everything, with its size stated up front
/ai/corpus.json     Chunks (§7); /ai/corpus/<group>.jsonl; /ai/bundles/<topic>.txt
/ai/manifest.json   Documents only: slug, title, summary, tier, sizes, hashes
/ai/search.json     Prebuilt lexical index for the on-page search
/ai/docs/*.md       One normalized markdown file per source document
/<page>/index.md    Markdown twin of every HTML page
/websocket/protocol.json, /websocket/obs-websocket.d.ts, /sitemap.xml, /robots.txt
```

Cut from the home page: the four-tier grid (now one sentence in the compatibility
section) and the crossover section (now the proof strip and `/progress/`).

## 5. Visual system

Colour, with fixed meaning. A colour used outside its meaning is a bug.

| Token | Value | Means |
|---|---|---|
| `--bg0/1/2` | `#0b0c0d` `#121416` `#17191b` | canvas |
| `--plate(2)`, `--edge(2)` | `#1d2023` `#24282b`, `#33383c` `#4a5055` | raised steel plates and their 1 px seams |
| `--rust` (`-hi`, `-lo`) | `#e8631a` | Rust code, primary action, the one accent per view |
| `--cu` (`-hi`) | `#3fa58a` | verified or computed: receipts, links, connected state |
| `--haz` | `#f2b705` | caution only: beta, deprecated, optional, destructive |
| `--red` | `#ff4040` | tally: on air, error. Never decoration |
| `--c`, `--cpp` | `#8a96a3`, `#5d6b7a` | legacy C and C++ in data graphics |
| `--fg`, `--fg2`, `--dim` | `#ece8e1`, `#c9c5bd`, `#8e949a` | text; `--dim` never under 13 px |

Type: three self-hosted families. **Big Shoulders Stencil Display 900** for h1, h2 and
hero numerals only, never below 28 px or beyond six words. **Barlow 400/600** for body,
h3 and UI (Barlow Condensed is dropped). **JetBrains Mono 500/700** for code, labels,
receipts and data.

Layout: 1180 px max, 8 px spacing scale (8, 16, 24, 40, 64, 96), 4 px radius on
controls, 6 px on plates. All page CSS lives in `assets/site.css`, organised as tokens,
base, components, pages. No `<style>` blocks and no inline `style=` except computed
values (`flex`, `--pct`).

### Signature moments

Four, and only four. Anything else decorative is removed.
1. **The program monitor (hero).** Keep the bezel, tally and dock; make the contents
   true. The screen shows the real application screenshot from upstream `docs/images/`,
   the lower third shows the libobs conversion figure, and the scene list is the site
   nav with the current page active. It is not `aria-hidden`.
2. **The receipt.** Every computed number is set in stencil over a patina-green mono
   caption: `conversion.json @ f131467 · 2026-11-17`. One component (`.receipt`,
   `data-src`, `data-rev`), used wherever a number appears. It is the brand's proof mark.
3. **The conversion gauge.** libobs lines ported, rust orange filling cold steel, a tick
   per module. The repository-wide linguist split becomes a secondary line labelled
   "whole repository, GitHub linguist", with no headline attached.
4. **The tally light.** One red lamp for real state only: the live console connection.
   Everywhere else it is unlit steel.

The bronze robot appears in three places: the `/ai/` page head, the 404 page and the
generated social card. Hazard stripes: one band above the footer, plus beta and
deprecated badges. Motion: meters and tally only, CSS, paused offscreen; the timecode
ticks at 1 Hz; `prefers-reduced-motion` removes all of it.

## 6. Content strategy

Voice: plain, specific, verifiable. No superlatives and no absolutes. Every sentence
about the product traces to a file in obs-studio; `claims.toml` (claim id, source file,
pattern that must still match) lets `check.py` fail the build when upstream drops it.

- **Users** want proof and an installer. The hero line stays; the sub-line becomes
  countable (same plugins, scenes and profiles; N upstream bugs fixed; installs beside
  OBS). Under it, a proof strip of four receipts: libobs converted, upstream bugs fixed,
  user-visible features, latest release. The download block puts the visitor's OS
  first. `/changes/` is the argument, fixed bugs first.
- **Builders** want the shortest path to a working call: `/websocket/` (§8) and real,
  checked files in `/examples/`. The compatibility contract is stated once, precisely:
  the upstream obs-websocket plugin ships unmodified at a pinned commit, as a receipt.
- **AI agents** read and contribute. Readers get `/llms.txt`, sized feeds and stable
  chunk ids (§7). Contributors get the worker prompt, rendered from the README at build
  time and never retyped. `/ai/` says in five lines which file serves which task.

## 7. AI corpus design

The corpus is the second product. Design target: an agent with a 128k window and one
HTTP tool reaches a correct, cited answer in at most three fetches.

**Scope and tiers.** Every document gets a tier, assigned by rule in `build.py`:

| Tier | Contents | In `llms-ctx.txt` | In `llms.txt` |
|---|---|---|---|
| `core` | README, AGENTS, CONTRIBUTING, SECURITY, CODESTYLE, CONSTITUTION, features ledger summary, download facts, site examples, WebSocket narrative | yes | top sections |
| `reference` | WebSocket per-item reference, libobs C API, control API schema, BUILD | no (own bundles) | by topic |
| `process` | `docs/rust-port/*`, `docs/knowledge/*`, `ci-tooling` | no | by topic |
| `archive` | dated audits, retrospectives, handoffs (filename has a date or issue suffix), hall of fame | no | `## Optional` |

Generated documents join it: `site/download.md` (release, asset URLs, checksums, install
steps), `site/examples.md` and `site/progress.md`.

**Chunking.** Structure-aware, never positional. Split on headings and carry the heading
path as a breadcrumb, which also opens the chunk `text` so it stands alone when
embedded. Target 400 to 2000 characters: merge a section under 300 into its sibling or
parent; split over 2400 at paragraph, then list item, then sentence. Never split a
fenced block or table. Typed chunks are one unit each, never split or merged:
`ws-request`, `ws-event`, `ws-enum` (from `protocol.json`), `c-symbol` (one Sphinx
directive with its description) and `ledger-entry` (one bullet, with area, platforms,
date and PR as fields). The protocol is indexed once: narrative from `protocol.md`,
items from `protocol.json`.

**Chunk record** (`/ai/corpus.json`, and one per line in `/ai/corpus/<group>.jsonl`):

```json
{"id": "ws:request:SetInputSettings", "doc": "obs-websocket-reference",
 "group": "websocket", "tier": "reference", "kind": "ws-request",
 "breadcrumb": ["obs-websocket v5", "Requests", "inputs", "SetInputSettings"],
 "url": "https://obs-rust.com/websocket/SetInputSettings.md",
 "source": "<permalink at the built commit>",
 "text": "...", "chars": 0, "tokens_est": 0, "sha256": "..."}
```

Ids are structural: `<doc-slug>#<heading-path-slug>` (`~2`, `~3` for overflow parts),
`ws:<kind>:<Name>`, `c:<symbol>`, `ledger:<pr-or-slug>`. Prose `source` permalinks carry
a line range. The top-level object carries `schema_version` and both commits.

**`llms.txt`.** Under 80 links. Each line is `[title](url): summary`, the summary being
the document's first sentence, extracted at build time. The header states the project
in two sentences, then lists every feed with its size and token estimate. Sections:
Start here, Install and use, Control OBS, Extend OBS, Contribute, Optional.
`llms-ctx.txt` holds the `core` tier under 300 KB; `llms-full.txt` stays complete.

**Discoverability.** Markdown files open with front matter (`title`, `source`, `commit`,
`updated`, `tier`, `tokens_est`). Every HTML page carries
`<link rel="alternate" type="text/markdown">` and a visible "Text version" link.
`sitemap.xml` lists every HTML and markdown URL; `robots.txt` allows all agents and
names `/llms.txt`; the home page carries computed JSON-LD `SoftwareApplication`. GitHub
Pages already serves `.md` as `text/markdown` with open CORS; assert it post-deploy.

**Search.** Lexical, prebuilt, lazy. `build.py` emits `/ai/search.json`, a BM25 index
with identifier-aware tokens (`SetInputSettings` also indexes `set`, `input`,
`settings`), loaded on first focus of the search box and never on page load. Results
link to the chunk anchor and offer "copy citation". Embedding search is rejected for
now: queries here are mostly identifiers, where lexical wins, and an embedding index
breaks the size budget.

**Retrieval eval.** `tools/eval_corpus.py` runs at least 30 checked-in pairs of question
and expected chunk id (install on Ubuntu, authenticate a session, `obs_source_create`)
through the page's own ranking code, as part of `check.py`.

## 8. WebSocket reference UX

The page a builder keeps open all day. Sticky index left, reference centre, console
docked right above 1200 px and as a bottom sheet below. The console is always in view;
"Try" never scrolls the reader away.

- **Cards** keep their tags and add a copyable deep link, the request as JSON plus
  `obs-websocket-js`, `obws` and `obsws-python` one-liners generated from field types,
  related events, and a "Text" link to the `.md`.
- **Typed form.** "Try" builds a form from `requestFields`: type, required or optional
  with its default, restrictions as hints. Raw JSON stays as a tab. Missing required
  fields disable Send and say why.
- **Console.** The connection lamp is the tally light. The log gets pretty and raw
  views, per-message copy, clear, timing, and an event filter generated from the
  `EventSubscription` enum. Status codes show their `RequestStatus` name. URL and
  subscriptions persist in `localStorage`; the password never does.
- **Honest failure.** An https page opening `ws://` works for loopback in some browsers
  and not in others. On error the console names the likely cause and offers a copyable
  `websocat` command and the matching snippet from `/examples/`.
- **Search.** `/` focuses, arrows move, Enter jumps, Esc clears. It matches field names
  and enum identifiers too, and its state lives in the URL (`?q=&kind=`).
- **Per-item pages** (`/websocket/<Name>/`, `.md`) serve search engines and agents and
  link back to `#<Name>`. With JS off the main page is still a complete reference.

## 9. Budgets

Enforced by `tools/check.py` on the built `_site/`. A breach fails the deploy.

| Budget | Limit |
|---|---|
| Third-party origins referenced by any page | 0 |
| `/` HTML + CSS + JS, gzipped | 40 KB |
| `/websocket/` HTML, gzipped | 60 KB |
| `/ai/` bytes fetched before user interaction, gzipped | 30 KB |
| Fonts, all files | 160 KB, display face preloaded, `font-display: swap` |
| Largest image on `/` | 120 KB, explicit `width`/`height` |
| Social card | 1200x630, under 200 KB, generated at build |
| Shipped but unreferenced assets | 0 |
| `llms.txt` / `llms-ctx.txt` | 80 links and 25 KB / 300 KB |

Manual Lighthouse (mobile, recorded in the PR): LCP under 1.8 s, CLS under 0.02, total
blocking time under 50 ms, on every page.

Accessibility is WCAG 2.2 AA, checked statically where possible:

- Contrast computed by `check.py` for every text token on every surface token of §5:
  body at least 4.5:1, stencil headlines and UI borders at least 3:1.
- One `h1` per page, no skipped levels, `alt` on every image, a label on every input, a
  skip link and `main` landmark on every page.
- A visible `:focus-visible` ring (2 px `--rust-hi`) on every control; no `autofocus`;
  targets at least 24x24 px; no horizontal scroll at 320 px; reflow at 200% zoom.
- Chips use `aria-pressed`; result counts and console status are polite live regions;
  data graphics have a text label or table twin; every page works with JS disabled.

## 10. Build and verification

`tools/build.py` stays the single generator (`uv run`, PEP 723). New inputs:
`conversion.json`, release asset digests, the upstream screenshot (add its path to the
sparse checkout in `pages.yml`) and `examples/`. `tools/check.py` (new) asserts §9, the
claims table, the corpus rules, internal links and anchors, no unresolved placeholders,
and **no hand-typed numbers**: two or more digits in a text node of `src/*.html` outside
`<pre>`/`<code>` must come from a placeholder or a short allowlist (port, opcodes).
`pages.yml` gains two steps in its existing job: `uv run tools/check.py _site` before
upload, and a post-deploy fetch of `/llms.txt` and one `.md` asserting status and
content type. `--offline` is for local work only.

## 11. Backlog

Ordered within each priority. Each item ships with its acceptance check.

### P0: correctness and the corpus foundation

| # | Item | Acceptance check |
|---|---|---|
| 1 | **Fix the libobs figure.** Read `conversion.json` (leaderboard branch); hero lower third and proof strip show its libobs percent with a receipt (source, commit, date). Linguist share is labelled "whole repository" wherever it remains. | Built `/` contains the libobs percent equal to `conversion.json` at build time; no element pairs the word "libobs" with the linguist figure; build fails if the file is unreachable. |
| 2 | **`tools/check.py` in `pages.yml`.** Budgets, link check, placeholders, no-hand-typed-numbers, zero third-party origins, expected-file manifest. | `uv run tools/check.py _site` exits 0 on a good build and non-zero when a digit is typed into `src/index.html` or a Google Fonts link is restored; `pages.yml` runs it before upload. |
| 3 | **Chunker v2 and corpus schema.** Typed chunks, merge/split rules, structural ids, breadcrumb, `url`, pinned `source`, `chars`, `tokens_est`, `sha256`, `schema_version`; WebSocket indexed once. | No untyped chunk outside 300..2400 chars except fenced/table; ids unique; one `ws-*` chunk per request, event and enum in `protocol.json`; two builds from the same inputs give byte-identical `corpus.json` apart from the timestamp. |
| 4 | **`llms.txt` v2, tiers and `llms-ctx.txt`.** Real one-sentence summaries, tiered sections, feed sizes stated, archive tier under Optional, generated `site/download.md` and `site/examples.md` in core. | No `llms.txt` link description equals a file path; under 80 links; `llms-ctx.txt` under 300 KB and contains the README, install steps and the latest release tag; sizes printed in `llms.txt` match the files on disk. |
| 5 | **Mobile navigation.** Scrollable nav strip under 760 px, no JS. | At 390 px every nav destination is reachable from the top of every page by keyboard and touch; no horizontal page scroll at 320 px. |
| 6 | **Self-host fonts, three families.** Subset woff2 in `assets/fonts/`, preload the display face, drop Barlow Condensed. | No request leaves `obs-rust.com` on any page; font payload under 160 KB; headings render in the stencil face with JS disabled. |
| 7 | **Replace unverifiable copy.** Remove "the crashes go away"; sub-line cites fixed-bug count from the ledger. Add `claims.toml`. | `check.py` fails when a claim's upstream pattern no longer matches; no absolute claim remains in `src/`. |
| 8 | **Lazy corpus search.** Prebuilt `/ai/search.json`, loaded on first focus; no `autofocus`; `/ai/` lists every document as static HTML. | Loading `/ai/` transfers under 30 KB gzipped before interaction; with JS off the document list and feed links are present; searching `SetInputSettings` ranks its `ws-request` chunk first. |
| 9 | **404 page and asset hygiene.** `404.html` with mascot and nav; delete the unused logo PNG; generated 1200x630 social card under 200 KB. | `/404.html` exists in `_site/`; every file in `_site/assets/` is referenced by some page; `og:image` dimensions are 1200x630. |

### P1: the pages that make the case

| # | Item | Acceptance check |
|---|---|---|
| 10 | **`/changes/`**: full ledger, fixed bugs first, filter by area, platform and text, anchor per entry. | Entry count on the page equals parsed ledger entries; each entry links its PR; filtering works by URL query; readable with JS off. |
| 11 | **`/progress/`** from `conversion.json`: gauge, by-module table, method and exclusions quoted from the file. | Every figure on the page appears in `conversion.json`; the receipt shows its commit and date. |
| 12 | **Real screenshot in the monitor**, scene list as nav. Add the image path to the sparse checkout. | Hero image comes from the obs-studio checkout at build, under 120 KB, with `alt`; the monitor is not `aria-hidden`. |
| 13 | **`/download/`** with checksums and OS highlight; build fails on unmatched assets. | Each listed asset shows size and SHA-256 from the release API; renaming a suffix in `DL_GROUPS` to a non-existent one fails the build; the visitor's OS card is marked first, and the page is complete without JS. |
| 14 | **Home restructure** to six sections with the proof strip. | `/` has six `<section>` elements; the download block is within two viewport heights at 1440x900; every number carries a `.receipt`. |
| 15 | **Console v2**: docked, typed form, event filter, status-code names, persistence without password, honest failure path. | Sending `SetCurrentProgramScene` with an empty required field is blocked with a message; a failed connect shows the fallback command; `localStorage` never contains the password; reader scroll position is unchanged after "Try". |
| 16 | **Examples as files.** `examples/<lang>/*`, highlighted at build, each exposed as raw text and in `site/examples.md`. | `check.py` extracts every `requestType` and event name used in `examples/` and finds each in `protocol.json`; Python examples pass `uv run python -m py_compile`. |
| 17 | **Per-item WebSocket pages and `.md`.** | For every name in `protocol.json`, `/websocket/<Name>/index.html` and `/websocket/<Name>.md` exist and are in the sitemap. |
| 18 | **Markdown twins and discoverability.** `index.md` per page, `rel="alternate"`, front matter, sitemap, `robots.txt`, JSON-LD. | Every HTML page's alternate link resolves; every `.md` starts with front matter holding a commit; JSON-LD parses and its version equals the latest release tag. |
| 19 | **Retrieval eval** in `check.py`. | `uv run tools/eval_corpus.py` reports at least 90% of 30+ questions with the expected chunk in the top 5; the build fails below that. |
| 20 | **CSS consolidation and motion fixes.** One stylesheet, no page `<style>`, no stray inline styles, offscreen animation paused, timecode at 1 Hz. | `grep -c '<style' _site/**/*.html` is 0; inline `style=` only sets computed custom properties or `flex`; no `requestAnimationFrame` in shipped JS. |
| 21 | **Accessibility pass.** Focus rings, contrast check, landmarks, live regions. | `check.py` contrast and structure checks pass; a keyboard-only walk of each page is recorded in the PR. |

### P2: depth

| # | Item | Acceptance check |
|---|---|---|
| 22 | `/websocket/obs-websocket.d.ts` generated from the protocol. | `tsc --noEmit` accepts it; it declares one request type per `protocol.json` request. |
| 23 | `/libobs/` symbol index over the Sphinx reference, linking `c-symbol` chunks. | Every `c-symbol` chunk id resolves to an anchor on the site. |
| 24 | Topic bundles `/ai/bundles/*.txt`. | Each bundle's size is under its budget and is listed with its size in `llms.txt`. |
| 25 | Contributor strip on `/` from `leaderboard.json` (merged PR total, contributors). | Figures equal the JSON at build time, with a receipt. |
| 26 | Launch-speed figure, only once obs-studio publishes it as data. | The number is read from a JSON file in the checkout; no prose parsing. |
| 27 | Release feed (`/releases.xml`, Atom) built from the releases API. | Feed validates; newest entry equals the latest release tag. |

## 12. Non-goals

No framework, bundler, analytics, cookie banner or third-party embed. No server-side
search, hosted MCP endpoint or embedding service. No hand-edited copy of upstream docs:
wrong text is fixed in obs-studio. No blog; news is the ledger and the release list. No
light theme. No claim the build cannot check.
