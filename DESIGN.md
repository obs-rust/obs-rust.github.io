# obs-rust.com — design document

Revision 7 — 2026-11-18. Living document; supersedes Revision 6 (same day, in git history).

Revision 6 raised the bar from "nothing wrong" to "stunningly good" with five craft items, #26
to #30. This revision refines it and adds no work: P0 is empty since PR #16 and #30 shipped in
#18; the four items left are in build order with their files and the §11 lines each turns
green (§10); checks that were entangled, flaky, unreachable or not worth their cost are fixed
or dropped (§11, "What changed"). Measured on https://obs-rust.com, 2026-11-18, 10:36 to 10:48
UTC (site `3b5904f`, then `d1de09d`).

**Revision 6's script: 18 `FAIL` lines** at 10:36 (19 before #16). **Revision 7's script: 29**
at 10:44 and 10:46, after #18: the same faults less search, one line per item and page (10 for
#26, 10 for #27, 8 for #28, 1 for #29), so each PR turns whole lines green.

## 1. Position

> obs-studio-rust is real, it is OBS, and you can run it, script it and read all of it today.

| Audience | Job | Succeeds when |
|---|---|---|
| Streamers | Decide to try it | On the first screen of `/` they see the real app; within three taps they know what does not work yet and hold a verified installer for their OS |
| Builders | Call OBS from code | They pick WebSocket or MCP from one table, find a request with its fields, and send it to their own OBS without leaving the page |
| AI agents | Answer or act correctly | Given only `https://obs-rust.com/llms.txt`, a cold agent answers an install, API, MCP or port-process question with a citable URL in three fetches or fewer |

When goals conflict: truth of a claim, then agent-readable text, then visual polish.

## 2. Shipped (verified on the live site, not read from PR descriptions)

| Item | Evidence on obs-rust.com | PR |
|---|---|---|
| R2 P0 #1 to #6, #8; `/mcp/`; typed tooling | libobs figure from `conversion.json`; `tools/check.py` and basedpyright strict in `pages.yml`; self-hosted fonts, no third-party request on any page; `/nope` is 404; corpus `schema_version` 2 with typed `ws-*`, `mcp-tool`, `ledger-*` chunks; 30 MCP tools from the server's schema; `tools/models.py` | #2 to #5, #7 |
| R3 P0 #2, #3: real app, agent router | Hero is the upstream screenshot `/assets/main-window.webp` (34 KB) with a receipt. `## Router` heads `llms.txt` and `/ai/`: 12 rows, each printed size equal to the bytes served; `/ai/manifest.json` lists 106 documents and every tenth matches its SHA-256 | #6, #8, #9 |
| R4 P0 #5, #8: stable and beta, "What to expect" | `#stable` offers `v1.0.0` (7 files) and `#beta` offers `v1.0.1-beta.20261108` (9 files); 16 of 16 hashes equal the line in that release's `SHA256SUMS`, on `/` and in `site-download.md`, with JS off too. Six limits beside the download, each linking `blob/<40 hex>/README.md#L<n>`; the cited lines support their sentence (A4) | #11 |
| R4 P0 #17a, #2 (part), #15a | At 320, 390 and 1440 px: no sideways scroll, no text under 12 px, no control under 24 px, no nav link off screen, a `:focus-visible` ring. All chunk `url`s are absolute and every ninth distinct one is 200 | #12, #13 |
| R5 P0 5b (desktop), 12: stable first, app first | Eyebrow "obs-studio-rust · stable v1.0.0"; the action reads "Download v1.0.0 ↓" at 1440 px. `llms.txt`: "ships stable and beta builds", "Releases: stable obs-studio-rust-v1.0.0; beta obs-studio-rust-v1.0.1-beta.20261108"; router row "Install and verify the download" (A5). The screenshot is 660 px wide at 1440x900 and 343 px at 390x844, ending 0.72 and 0.74 screens down; h1 is 72 px and 38 px | #15 |
| R5 P0 4, 2: promises reworded, figure pinned, agent path closed | None of the six banned phrases on any page (A3): "Built to stay compatible"; "clients written for obs-websocket v5 (OBS 28 and later) are expected to work against it unchanged". `/` links `blob/fc58e78c…/conversion.json`, whose `libobs.all.percent` is 60.36, shown as 60.4% (A6). The `--dangerously-skip-permissions` block opens with a `.caution` paragraph. 0 of 1709 chunks hold `<img`, `<p align` or shields.io; "Linux" is in the first 1500 characters of `/mcp/index.md`; `site-control.md` says the MCP server runs "on the OBS machine itself (Linux)" and "A WebSocket client may run remotely" (A7) | #15 |
| R6 P1 #30: search that answers | On `/ai/#q=install%20on%20windows` the first of 25 hits is `site-download.md#windows-x64-arm64`; `SetInputSettings` and `wait_for` put their typed chunk first (A8). Six example queries; `/` focuses `#q`; the tallest of the first five cards is 150 px, each with a copy button; `#meta` is `aria-live` and reads "25 results for …" (S5). Merged 10:40 UTC during this revision; A8 and both S5 lines are green | #18 |
| R6 P0 5c: the action on the phone's first screen | At 390x844 the first screen holds the link "Download v1.0.0 ↓" (outside the header) and the whole monitor, 358 px wide, ending 0.73 screens down; B "/ first screen at 390 px" prints nothing (10:36 UTC, site `3ad32a9` and later) | #16 |

## 3. Critique of the live site: correct, not yet stunning

Seen as a designer, in screenshots at 1440x900 and 390x844 and in computed styles read by the
§11 probe. The pages are honest and tidy. They are also five pages by five hands, mostly text,
that never move, and whose two instruments (console and search) wait below the fold. Search
itself now answers (#18).

1. **No type scale, and the pages disagree.** 38 distinct font sizes are in use, 20 of them on
   `/` (12.9, 13.5, 21, 24, 34, 39.52, 104 ...). The h1 is 72 px on `/`, 84 px on three pages,
   96 px on `/mcp/`, 128 px on the 404; a section h2 is 52 px on `/`, 38 px on `/examples/`.
   Radii are 3, 4, 6, 8 and 10 px. Paragraphs run 51 em wide on four pages and 72 em on `/`
   (about 105 and 150 characters a line). `/` and `/ai/` end a four-card row with a lone card.
2. **Four of five pages open on words.** On `/websocket/` the console starts 0.68 screens down
   at 1440 px and 1.46 at 390 px, under four "op" cards; on `/ai/` the search box is 2.19 and
   3.92 screens down, under five feed cards. The site has one picture; `og:image` is a 768 KB
   square; a 643 KB logo ships unreferenced.
3. **Too long to scan.** `/websocket/` is 84 screens at 1440 px and 151 at 390 px, every entry
   open; `/mcp/` is 20 and 34; `/` is 8 and 17, of which the download section is 5.5 and
   "what changed" 3.1 at 390 px.
4. **Nothing moves.** No element animates. 25% of links and buttons on `/` ease on hover and
   0% to 6% elsewhere, so a button fades on one page and snaps on the next.
5. **The console is a blank box until you own an OBS**: an empty log and a JSON textarea.
## 4. Principles and constraints

1. **Receipts, visibly.** Every figure is computed at build time and shows its source, commit
   and date, linked at a commit and never at a branch. No receipt, no number.
2. **The project's own measures only**: `conversion.json`, the features ledger, the releases
   API, `protocol.json`, `control-api.schema.json`, the README, upstream `docs/images/`.
3. **Show the thing, say what does not work**: the real application and release assets, and
   their limits beside the pitch, quoted from upstream files.
4. **Fail closed.** If a source cannot be fetched or parsed the build fails; stale beats wrong.
5. **Text first; static, first-party, small.** Every page an agent may need has a markdown
   twin. No framework or third-party origin; assets are self-hosted; JS only enhances.
6. **Craft is measured.** A rule of §6 a script can read (a size, a radius, a position) is
   checked by a script; what only an eye can judge is a yes/no question in §11 D.

Constraints from the maintainer; a change that breaks one is not done:

- **Python runs only through `uv run`**, strictly typed: pydantic models or frozen dataclasses
  for all data, no duck-typed dicts, `basedpyright` strict clean (the `pages.yml` step). A new
  input, such as the replay transcript, gets a model in `tools/models.py`.
- One generator (`tools/build.py`, `corpus.py`, `mcp.py`, `sitedocs.py`), one gate
  (`tools/check.py`), the existing `pages.yml`. No new workflow file. Assets are self-hosted.
  Each item lands with its check in `check.py`, so §11 finds nothing `_site/` did not show.

## 5. Information architecture

Nav, on one row at 390 px: **Download · WebSocket API · MCP · Examples · AI Corpus**, GitHub.
Five pages and the 404. Each page has one **object**, marked `data-object`, that leads it:

```
/             The program monitor (the real app). Then proof strip, download with its limits,
              what changed (with one more real capture), build with it
/websocket/   The console, docked beside the reference.   /websocket/#demo replays a session
/mcp/         The agent session panel.                    /mcp/index.md is its text twin
/examples/    The first runnable snippet.                 /404.html: the badge and the nav links
/ai/          The search box, then router and feeds.      /ai/#q=<query> runs a search into #hits
              /ai/docs/*.md, corpus.json, manifest.json; /llms.txt, /llms-ctx.txt, /llms-full.txt
P1 depth:     /download/ /changes/ /progress/ /control/ /websocket/<Name>.md /mcp/tools/<name>.md
```

## 6. Visual system

The brand stays. Colour has fixed meaning; a colour used outside its meaning is a bug.

| Token | Value | Means |
|---|---|---|
| `--bg0/1/2`, `--plate`, `--edge` | `#0b0c0d` to `#24282b`, seams `#33383c` | canvas, steel plates, 1 px seams |
| `--rust` | `#e8631a` | Rust code, primary action, the one accent per view |
| `--cu` | `#3fa58a` | verified or computed: receipts, links, connected state |
| `--haz` | `#f2b705` | caution only: beta, unsigned, untested, destructive, recorded and not live; the focus ring |
| `--red` | `#ff4040` | tally: on air, error. Never decoration |
| `--c`, `--cpp` | `#8a96a3`, `#5d6b7a` | legacy C and C++ in data graphics |
| `--fg`, `--fg2`, `--dim` | `#ece8e1`, `#c9c5bd`, `#8e949a` | text; `--dim` never under 13 px |

**Type scale, the only sizes on the site (px):** text 12, 13, 15, 17, 19; display 22, 30, 40,
52, 72; 96 for the hero numeral and the 404 only. **Big Shoulders Stencil Display 900** for
h1 (72 at 1440 px, 40 at 390 px, on every page), h2 (52, 30) and numerals, six words at most;
**Barlow 400/600** for body (17, lede 19) and UI (15); **JetBrains Mono** for code (13),
labels and receipts (12, 13). Sizes and radii are tokens in `site.css` (`--t-*`, `--r-*`); a
page `<style>` may lay out its own object but names them by token, never as a px literal.
**Rhythm and shape:** 1180 px max, 8 px scale, body text (15 px and up) 40 em wide at most. Every page starts
the same: header, 72 px (24 px at 390 px), eyebrow, h1, lede, object. Sections are 96 px apart
(64 px at 390 px). Radius is 4 px on controls and tags, 6 px on plates, 50% on lights. A card
row never ends in one lone card. Tables and code scroll in their own box, never the page.

Signature moments, four and only four. **The program monitor**: bezel, tally and dock around
the upstream screenshot, 640 px or wider on desktop, 330 px or wider and whole within the
first screen on a phone. **The receipt**: one component, `.receipt`, patina-green mono under
every computed number and limit, its link a 40-hex permalink. **The headline figure**: one
per view, libobs lines ported; other denominators are labelled rows beneath it or leave the
page. **The tally light**: lit red only for live state, the WebSocket console connection.

**Imagery** is real: upstream captures (`docs/images/`) re-encoded at build, each with a
receipt, and a 1200x630 social card generated from the app screenshot. The badge is the only
drawn mark. No stock art, no decorative illustration, no shipped file that no page references.
**Motion has a job; CSS only, all of it in `site.css`; off under `prefers-reduced-motion`.**
(a) Every link, button and `summary` eases colour, border and background over 120 to 180 ms,
by one rule, alike on every page. (b) The conversion bar fills once, from zero to its figure,
within 1.2 s. (c) The tally pulses while the console is connected, the one animation that
repeats. (d) A copy control shows "copied" for 1.5 s. Nothing else moves.

## 7. Content and corpus

Voice: plain, specific, verifiable; no superlatives, no absolutes ("every", "nothing",
"identical"). A promise or a limit ships in one of two forms: a sentence with a line receipt
(a typed `Limit` in `build.py` whose pattern must still match the upstream file, rendered
with a `blob/<commit>/<file>#L<n>` link), or a sentence reworded until it says only what the
project measures ("clients written for obs-websocket v5 are expected to work against it
unchanged", not "every client works").

Streamers: the first screen names the newest stable release; each download has its size,
SHA-256 and verify command, and its limits beside it. Builders: one computed WebSocket-or-MCP
table on `/` and in `site-control.md`; examples name only what exists. Agents: the router
(task, one file, exact bytes) heads `llms.txt` and `/ai/`.

**Corpus.** Tiers by rule in `build.py`: `core` (README without badges, AGENTS, CONTRIBUTING,
SECURITY, CODESTYLE, CONSTITUTION, ledger summary, `site/*.md`, MCP and WebSocket narrative)
fills `llms-ctx.txt`; then `reference`, `process`, `archive`. Chunks split on headings, open
with their breadcrumb, hold no markup, and are at most 2400 characters; typed chunks
(`ws-request`, `ws-event`, `ws-enum`, `mcp-tool`, `mcp-resource`, `ledger-entry`, `ledger-fix`,
later `c-symbol`) are one unit each. Fields: `id`, `doc`, `group`, `tier`, `kind`,
`breadcrumb`, `url` (absolute, resolves), `source`, `text`, `chars`, `tokens_est`, `sha256`.

**Search** on `/ai/` is lexical and client-side (embedding search stays rejected). Terms match
whole words or word prefixes, never the inside of a word; one- and two-letter words and "on",
"the", "to", "how" count only inside the whole phrase. Rank by term frequency, then boost a
match in the title or breadcrumb, an exact `id`, and `core` over `process` and `archive`. A
result is a card of at most 200 px: kind, title, breadcrumb, a two-line snippet with the match
marked, "Open", and a copy button (URL and chunk `id`, ready to paste to an agent). The count
is `#meta`, `aria-live`. Before a query, six example queries are links (`#q=...`). `/` focuses
the box.

**Feeds.** `llms.txt`: 80 links and 25 KB at most, each `[title](url): first sentence`, naming
the newest stable release and beta; `llms-ctx.txt` under 300 KB; `manifest.json` gives each
document's bytes and SHA-256.

## 8. Budgets and accessibility

Checked by `tools/check.py` on `_site/`, and by §11 on the live site. Live values in brackets.

| Budget | Limit |
|---|---|
| Third-party origins requested by any page | 0 [0] |
| HTML gzipped: `/` with CSS; `/websocket/`; `/mcp/`; `/ai/` | 40 KB [13.3]; 60 KB [35.5]; 20 KB [13.3]; 30 KB [7.9] |
| First search on `/ai/`, gzipped (P1) | 150 KB [629 KB] |
| Fonts, all files; largest image on `/` | 160 KB [157.7 KB]; 120 KB [34 KB] |
| `llms.txt` / `llms-ctx.txt` | 80 links, 25 KB [55, 16.6 KB] / 300 KB [230.5 KB] |
| Social card | 1200x630 PNG under 200 KB [768 KB square]; unreferenced assets 0 [1, 643 KB] |
| Page length at 1440 / 390 px, in screens | `/` 6.5 / 12 [8.1 / 17.2]; `/websocket/` 15 / 30 [84 / 151]; `/examples/` 7 / 10 [6 / 8.3]; `/ai/` 5 / 10 [4.1 / 8.7]; `/mcp/` 10 / 18 [19.6 / 33.6] |

Accessibility is WCAG 2.2 AA; §11 B probes it at 320, 390 and 1440 px, and with JS off;
`check.py` keeps heading order, `alt`, labels, the skip link and contrast. Long pages get short
by closing detail, never by dropping it: an entry is a `<details>` whose `summary` carries the
anchor, so every name is on the page and findable with JS off.

## 9. WebSocket reference and console

Sticky index left, reference centre, console (`#console`) docked right and in the first screen,
so "Try" never scrolls the reader away. Under 1200 px it is a bottom sheet that shows 15% of
the screen or more (state, the last frame, Replay) and opens on "Try". The password is never
stored. The log (`#log`) reads as a conversation: one row per frame with `data-op`, direction,
op name, indented JSON and round-trip time. A typed form per request is depth (item 19).

**Replay.** `/websocket/#demo`, and a "Replay a session" button, play a checked-in transcript
(Hello, Identify, Identified, `GetVersion`, its response, one event), inlined in the page at
build, into the log within four seconds; no socket opens. The console says, in `--haz`, where
the frames came from: "recorded from obs-studio-rust-v<n>" only if they were captured from
that release, otherwise "scripted from the protocol of obs-studio-rust-v<n>". `#st` reads
"replay" and the tally stays unlit. The build fails if a frame names what `protocol.json`
lacks or the tag is not the newest stable release.

## 10. Backlog

Numbers continue Revisions 3 to 5; a letter marks a split. An item is done when its check
passes in `tools/check.py` on `_site/` and in §11 on the live site.

### P1 "stunning": what §11 S and D5 to D9 judge (29 `FAIL` lines; P0 is empty)

Four PRs, in this order, one item each; these alone stand between the site and an LGTM (#30
shipped in #18 and holds A8, both S5 lines and D9). Each PR adds its S lines to `check.py`,
and leaves every line that was green, green.

| Order | # | Item | Files | §11 lines it turns green |
|---|---|---|---|---|
| 1 | 26 | **One system on every page** (absorbs 17b). The scale, radii and measure of §6 as `--t-*` and `--r-*` tokens; every px literal for a size or radius replaced; card rows of 2, 3 or 4 that never orphan; h1 72 / 40 px. | `assets/site.css`; the `<style>` block and `style=` attributes of all six `src/*.html`; inline sizes emitted by `tools/build.py` and `tools/mcp.py`; `tools/check.py` | 10: `S1 <page> at 1440 px` and `S1 <page> at 390 px` for `/`, `/websocket/`, `/examples/`, `/ai/`, `/mcp/`. D5. |
| 2 | 27 | **Every page opens on its object** (absorbs 12b). The same page start everywhere, then the `data-object` of §5: monitor, console, agent session (config and three calls, built from `mcp/schema.json`), first snippet, search box above the router. Entries on `/websocket/` and `/mcp/` are closed `<details>`; on `/` the beta files and the older ledger entries close. | Markup of `src/index.html`, `websocket.html`, `mcp.html`, `examples.html`, `ai.html`; entry templates in `tools/build.py` (`<article>`, about line 539) and `tools/mcp.py` (about line 299); dock layout in `assets/site.css`; `tools/check.py` | 10: `S2 <page> at 1440 px` and `S2 <page> at 390 px` for the five pages. Must keep `B / with JS off` (six stable files and hashes stay open) and `B /websocket/ with JS off` (each `summary` carries the `id`). D6. |
| 3 | 28 | **The finish: pictures and motion** (absorbs 7). One more real capture on `/` beside its ledger entry (upstream `docs/images/gpu-status-red.png`, 194 KB, re-encoded like the hero) with a receipt; the generated social card; the two logo PNGs gone; the four motions of §6. | `assets/site.css` (one transition rule, two or three `@keyframes`); `src/index.html` (bar, second figure); `tools/build.py` (capture, card, `og:image` at about line 581); `tools/models.py`; `assets/*.png`; `tools/check.py` | 8: `S3 <page> eases` for the five pages, `S3 / pictures`, `S3 the social card`, `S3 / motion`. `S3 / with reduced motion` and `S3 site.css` are green now and must stay so, as must `S2 /` (length). |
| 3, parallel | 29 | **A console that plays.** The replay and the conversation log of §9. | `src/websocket.html`; `src/replay.json` (new); `tools/build.py` (inline and validate the transcript); `tools/models.py` (its model); `tools/check.py` | 1: `S4 /websocket/#demo` (ops 0, 2, 6 and 7 in `#log`; "recorded" or "scripted" with the release tag; `#st` not "connected"). D8. |

**Conflicts.** #26 rewrites every page's `<style>` (including the px literals #18 just added
to `src/ai.html`), so nothing runs beside it. #27 moves the markup #26 restyled and docks the
console #29 fills, so it follows #26 and precedes #29; #28 adds a picture to the page whose
length #27 sets. #28 and #29 may run in parallel: #29 owns `src/websocket.html`, #28 owns
`site.css` and `src/index.html` (the tally's pulse is a `site.css` class that #29 only
toggles), and both only append to `build.py`, `models.py` and `check.py`; the second to merge
rebases. Every other pair is serial.

### P1: depth (does not gate the LGTM)

| # | Item | Acceptance check |
|---|---|---|
| 19 | **Typed "Try" form** from `requestFields`; a missing required field disables Send and says why. | An empty required field blocks Send with a message; `localStorage` never holds the password. |
| 6 | **Gate v2**: every §11 check, S included, in `check.py` on `_site/` (the probe runs on local files); a post-deploy step in the existing job runs §11 A1. | `check.py` exits non-zero for each of: a table wider than its page, 11 px text, a 14 px font size, a relative chunk `url`, a banned phrase, a limit whose pattern is gone; the deploy job fails if `/llms.txt` is not 200 `text/plain` or `/nope` is not 404. |
| 4b | **Home in order**: one headline figure; proof strip of four receipts without "Forks"; ledger preview leads with fixed bugs; a copy control per hash; the WebSocket-or-MCP table. | One figure carries the hero numeral style; "N requests", "N events" and "N typed tools" equal `protocol.json` and `mcp/schema.json`. |
| 2b, 1, 15 | **Corpus residue and search index**: prose `url` ends in its heading's `#anchor`; no prose chunk under 300 characters; hall of fame out of `core`; `c-symbol` chunks; deterministic output; `/ai/search.json`; `tools/eval_corpus.py`. | No prose `url` without `#`; one `c-symbol` chunk per Sphinx directive; two builds from the same inputs give a byte-identical `corpus.json` apart from the timestamp; the first search transfers under 150 KB gzipped; 90% of 30 or more checked-in questions have the expected chunk in the top 5. |
| 11, 18, 13 | **Markdown twins, per-item pages, sitemap**: `index.md` per page with `rel="alternate"`; `/websocket/<Name>.md` and `/mcp/tools/<name>.md`; JSON-LD on `/`; every document in `sitemap.xml`; `server.json` valid against the vendored schema. | Every alternate link resolves; a `.md` exists for every name in `protocol.json` and every MCP tool; JSON-LD's version equals the newest stable tag; the sitemap lists as many URLs as the manifest has documents; `server.json` validates against `tools/vendor/server.schema.json`. |
| 16 | **Examples as files** `examples/<lang>/*`, highlighted at build, served raw, with one MCP agent session. | Every request, event and tool name used exists in `protocol.json` or `mcp/schema.json`; Python examples pass `uv run python -m py_compile`. |
| 9, 10, 14 | **`/changes/`, `/control/`, `/progress/`** from the ledger, the two schemas and `conversion.json`. | Entry and figure counts equal their sources; each page reads complete with JS off; one receipt each. |

### P2: depth

20 `/websocket/obs-websocket.d.ts` (`tsc --noEmit` accepts it). 21 `/libobs/` symbol index (every
`c-symbol` id resolves). 22 topic bundles `/ai/bundles/*.txt` (sizes in `llms.txt`). 23 MCP
`packages` in `server.json` (URL and hash equal a release asset and its `SHA256SUMS` line). 24
contributor strip (equals `leaderboard.json`). 25 `/releases.xml`; a launch-speed figure from JSON.

## 11. The done bar

The judge works on the **live site** only; nothing is taken from a build log, a PR or this
document's brackets. Verdict: **LGTM** when the script prints no `FAIL` line, all three trials
in C pass, at most one of D1 to D4 fails and at most one of D5, D6, D8 and D9 fails; otherwise
**FAIL:** and the failed lines. Budget 10 minutes: the script ran in 1 min 41 s and 1 min 42 s (killed, and failed, at
9 min); C's trials run in parallel in about five; D takes four. The script needs only `bash`,
`curl`, `jq` and the Chromium at `~/.hermes/tools/chromium-1208/chrome-linux64/chrome`, and
samples nothing at random: two runs against one deploy print the same lines.

```bash
cd "$(mktemp -d)"   # then extract the two blocks below from this file and run them
awk '/^```html probe/{f="probe.html";next} /^```bash judge/{f="judge.sh";next} /^```$/{f=""} f{print > f}' /path/to/DESIGN.md
timeout 540 bash judge.sh | tee verdict.txt; grep -c '^FAIL' verdict.txt   # 0 is a pass; a timeout is a FAIL
```

```html probe
<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:#000}iframe{display:block;border:0}</style><body><script>
const P=new URLSearchParams(location.search),w=+P.get('w'),h=+P.get('h'),H=P.get('hash'),f=document.createElement('iframe');
f.width=w;f.height=h;if(P.get('nojs')=='1')f.sandbox='allow-same-origin';f.src='page.html'+(H?'#'+H:'');document.body.append(f);
f.onload=()=>P.get('shot')||setTimeout(()=>{const d=f.contentDocument,W=f.contentWindow,q=s=>[...d.querySelectorAll(s)],box=e=>e.getBoundingClientRect(),cs=e=>W.getComputedStyle(e),
 vis=e=>box(e).width>0&&box(e).height>0,px=e=>parseFloat(cs(e).fontSize),bar=e=>e.closest('header,nav,footer'),uniq=a=>[...new Set(a)],txt=s=>(e=>e?e.innerText.trim():'')(d.querySelector(s)),text=q('body *').filter(e=>vis(e)&&[...e.childNodes].some(n=>n.nodeType==3&&n.textContent.trim())),img=q('img').filter(vis),
 hero=img.filter(e=>box(e).top<h).sort((a,b)=>box(b).width-box(a).width)[0],obj=q('[data-object]').filter(vis)[0],act=q('a,button,summary').filter(vis),cta=q('a[href*="#download"],a[href*="#stable"],a[href*="/releases/download/"]').filter(e=>vis(e)&&!bar(e)&&box(e).bottom<=h)[0],
 hit=q('#hits>*').filter(e=>vis(e)&&e.querySelector('a[href]'));
d.dispatchEvent(new W.KeyboardEvent('keydown',{key:'/',bubbles:true}));
const r={w:W.innerWidth,overflow_px:d.documentElement.scrollWidth-W.innerWidth,small_text:text.filter(e=>!e.children.length&&px(e)<12).length,small_controls:q('button,summary,input,select,header a,nav a').filter(e=>vis(e)&&(box(e).width<24||box(e).height<24)).length,
 nav_clipped:q('header a,nav a').filter(e=>vis(e)&&!e.closest('footer')&&(box(e).right>w+1||box(e).left<-1)).length,hero_w:hero?Math.round(box(hero).width):0,hero_bottom_vh:hero?+(box(hero).bottom/h).toFixed(2):9,cta:cta?cta.innerText.trim():'',
 dl_links:q('a[href*="/releases/download/"]').filter(vis).length,hashes:(d.body.innerText.match(/\b[0-9a-f]{64}\b/g)||[]).length,ids:q("[id]").filter(vis).length,line_receipts:q('a[href*="/blob/"][href*="#L"]').map(a=>({href:a.href,text:a.parentElement.innerText.replace(/\s+/g,' ')})),
 third_party:W.performance.getEntriesByType('resource').map(e=>e.name).filter(n=>!/^(https:\/\/obs-rust\.com\/|file:)/.test(n)),sizes:uniq(text.filter(e=>e.isConnected).map(e=>Math.round(px(e)*100)/100)).sort((a,b)=>a-b),h1:(e=>e?px(e):0)(q('h1').filter(vis)[0]),
 radii:uniq(q('body *').filter(vis).map(e=>cs(e).borderTopLeftRadius).filter(r=>r!='0px')).sort(),measure:Math.round(Math.max(0,...q('p,li').filter(e=>vis(e)&&px(e)>=15&&e.innerText.length>120).map(e=>box(e).width/px(e)))),
 orphans:q('body *').filter(e=>vis(e)&&cs(e).display=='grid'&&e.children.length>3).filter(e=>{const t=[...e.children].filter(vis).map(c=>Math.round(box(c).top)); return t.filter(x=>x==t[0]).length>2&&t.filter(x=>x==t[t.length-1]).length==1}).length,
 screens:+(d.documentElement.scrollHeight/h).toFixed(1),obj_top:obj?+(box(obj).top/h).toFixed(2):9,obj_w:obj?Math.round(box(obj).width):0,easing:act.length?+(act.filter(e=>cs(e).transitionDuration!='0s').length/act.length).toFixed(2):0,anim:q('body *').filter(e=>vis(e)&&cs(e).animationName!='none').length,
 pictures:img.filter(e=>box(e).width>=300).length,slash:d.activeElement?d.activeElement.id:'',hits:hit.length,hit_h:Math.round(Math.max(0,...hit.slice(0,5).map(e=>box(e).height))),hit_first:(a=>a?a.href:'')(d.querySelector('#hits a[href]')),
 hit_copy:hit.slice(0,5).filter(e=>e.querySelector('button')).length,tries:q('a[href*="#q="]').filter(vis).length,count:txt('#meta[aria-live]'),ops:uniq(q('#log [data-op]').map(e=>+e.dataset.op)).sort(),state:txt('#st'),recorded:(txt('#console').match(/(recorded|scripted)[^\n]*obs-studio-rust-v[\d.]+/i)||[''])[0]};
document.body.innerHTML='<pre>'+JSON.stringify(r).replace(/</g,'&lt;')+'</pre>'},H?6000:2500);
</script>
```

```bash judge
B=https://obs-rust.com; GH=https://github.com/obs-rust/obs-studio; RAW=https://raw.githubusercontent.com/obs-rust/obs-studio
C=~/.hermes/tools/chromium-1208/chrome-linux64/chrome; PAGES="/ /websocket/ /examples/ /ai/ /mcp/"; mkdir -p shots
fail(){ echo "FAIL $*"; }; get(){ curl -s -m 60 --retry 2 --compressed "$B$1"; }; gz(){ curl -s -m 60 -H 'Accept-Encoding: gzip' "$B$1" | wc -c; }
lim(){ [ "$2" -le "$3" ] || fail "$1 = $2 > $3"; }; code(){ curl -s -m 30 --retry 2 -L -o /dev/null -w '%{http_code}' "$1"; }; export -f code
alive(){ xargs -P 6 -I{} bash -c '[ "$(code "{}")" = 200 ] || echo "FAIL '"$1"': {}"'; }   # alive LABEL < urls: each is 200, six at a time
chrome(){ timeout 60 "$C" --headless=new --incognito --no-sandbox --disable-gpu --hide-scrollbars --allow-file-access-from-files --user-data-dir="$PWD/prof" $XF "$@" 2>/dev/null; }
page(){ get "$1" | sed "s|<head>|<head><base href=\"$B$1\">|;s/history\.\(replace\|push\)State/console.debug/g" > page.html; }   # the live page, framed from a local file
probe(){ k="p$(tr -c 'a-z0-9\n' _ <<<"$*").json"; [ -s "$k" ] && { cat "$k"; return; }; page "$1"   # probe PATH W H [nojs] [hash]: layout facts as JSON, cached
  for try in 1 2; do chrome --window-size=1700,1300 --virtual-time-budget=20000 --dump-dom "file://$PWD/probe.html?w=$2&h=$3&nojs=${4:-0}&hash=${5:-}" | grep -o '{"w":.*}' > "$k" && break; done; cat "$k"; }
want(){ r=$(probe $2); [ -n "$r" ] || { fail "$1: the probe returned nothing"; return; }   # want LABEL "PATH W H [nojs] [hash]" JQ-FAULTS
  jq -r --arg l "$1" "[$3]|if length>0 then \"FAIL \(\$l): \"+join(\"; \") else empty end" <<<"$r"; }
shoot(){ page "$2"; for try in 1 2 3; do chrome --window-size=$3,$4 --virtual-time-budget=9000 --screenshot="shots/$1.png" "file://$PWD/probe.html?w=$3&h=$4&shot=1&hash=${5:-}" >/dev/null   # shoot NAME PATH W H [hash]
  [ "$(wc -c < "shots/$1.png")" -gt 30000 ] && return; done; fail "D no screenshot of $2 at $3 px"; }
# A1 the site is up, fresh, and serves each format with the right status and type
get /llms.txt > llms.txt; d=$(grep -o 'Generated [0-9-]*' llms.txt | cut -d' ' -f2); [ -n "$d" ] && [ $(( ($(date -u +%s) - $(date -u -d "$d" +%s)) / 86400 )) -le 2 ] || fail "A1 site generated '$d', over 2 days ago"
st(){ c=$1; ty=$2; shift 2; for p; do got=$(curl -s -m 60 -o /dev/null -w '%{http_code} %{content_type}' "$B$p")
  case "$got" in "$c $ty"*) ;; *) fail "A1 $p -> $got";; esac; done; }
st 200 text/html $PAGES; st 404 text/html /nope; st 200 text/plain /llms.txt /llms-ctx.txt /llms-full.txt; st 200 application/json /ai/corpus.json /ai/manifest.json /mcp/schema.json /websocket/protocol.json
st 200 text/markdown /mcp/index.md /ai/docs/site-download.md /ai/docs/site-control.md /ai/docs/site-examples.md
# A2 weight: a phone on a slow link, and an agent with one context window
lim "A2 / html+css gzipped" $(( $(gz /) + $(gz /assets/site.css) + $(gz /assets/fonts.css) )) 40000; lim "A2 /websocket/ html gzipped" "$(gz /websocket/)" 60000; lim "A2 llms.txt bytes" "$(wc -c < llms.txt)" 25000; lim "A2 llms-ctx.txt bytes" "$(get /llms-ctx.txt | wc -c)" 300000
# A3 no retired or absolute promise is back
BAN='rust has passed c|starting soon|nothing you rely on|keep the two identical|every client written|every v5 client works'; for p in $PAGES /nope; do get $p | grep -oiE "$BAN" | sort -u | sed "s|^|FAIL A3 $p says: |"; done
# A4 limits: three or more on /, each with a commit-pinned line receipt whose lines say the same thing
probe / 1440 900 > home.json; [ "$(jq '.line_receipts|length' home.json 2>/dev/null || echo 0)" -ge 3 ] || fail "A4 / shows under 3 limits with a line receipt"
jq -r '.line_receipts[]?|[.href,.text]|@tsv' home.json | while IFS=$'\t' read -r href text; do
  [[ $href =~ /blob/([0-9a-f]{40})/([^#]+)#L([0-9]+)$ ]] || { fail "A4 receipt is not pinned to a commit and a line: $href"; continue; }
  win=$(curl -s -m 30 "$RAW/${BASH_REMATCH[1]}/${BASH_REMATCH[2]}" | sed -n "${BASH_REMATCH[3]},$(( BASH_REMATCH[3] + 3 ))p")
  n=0; for wd in $(grep -oE '[A-Za-z]{6,}' <<<"$text" | sort -u); do grep -qiF "$wd" <<<"$win" && n=$((n+1)); done
  [ "$n" -ge 2 ] || fail "A4 the cited lines do not support: ${text:0:80}"; done
# A5 downloads: the newest stable and any newer beta, every file with the SHA-256 from its own SHA256SUMS
get / > home.html; get /ai/docs/site-download.md > dl.md
REL=$(curl -s -m 60 ${GITHUB_TOKEN:+-H "Authorization: Bearer $GITHUB_TOKEN"} "https://api.github.com/repos/obs-rust/obs-studio/releases?per_page=100")
OURS='[.[]|select(.tag_name|startswith("obs-studio-rust-v"))]'; stable=$(jq -r "$OURS|map(select(.prerelease|not))[0].tag_name // empty" <<<"$REL" 2>/dev/null)
beta=$(jq -r "$OURS|(map(.prerelease)|index(false)) as \$i|.[:\$i][0].tag_name // empty" <<<"$REL" 2>/dev/null)
[ -n "$stable" ] || fail "A5 cannot read a stable release from the GitHub API (if rate limited, set GITHUB_TOKEN)"; for tag in $stable $beta; do curl -sL -m 60 "$GH/releases/download/$tag/SHA256SUMS" > "sums.$tag"
  for doc in home.html dl.md; do links=$(grep -o "releases/download/$tag/[^\")]*" $doc | sort -u)
    [ "$(grep -c . <<<"$links")" -ge 3 ] || fail "A5 $doc offers under 3 files of $tag"
    for l in $links; do h=$(awk -v f="${l##*/}" '$2==f||$2=="*"f{print $1}' "sums.$tag"); [ -n "$h" ] && grep -q "$h" $doc || fail "A5 $doc: ${l##*/} lacks the SHA-256 from SHA256SUMS"; done; done; done
[ -z "$stable" ] || grep -q "$stable" llms.txt || fail "A5 llms.txt does not name the newest stable release, $stable"
# A6 figures and names equal their sources
sha=$(grep -oE '[0-9a-f]{40}/conversion\.json' home.html | head -1); pct=$(curl -s -m 30 "$RAW/$sha" | jq -r '.libobs.all.percent|"\(.*10|round/10)|\(.*10|floor/10)"|gsub("\\.";"\\.")' 2>/dev/null)
[ -n "$sha" ] && [ -n "$pct" ] || fail "A6 / has no conversion.json receipt pinned to a commit"; [ -z "$pct" ] || grep -qE "(^|[^0-9.])($pct) ?%" home.html || fail "A6 / does not show the libobs percent of its receipt ($pct)"
get /websocket/protocol.json > p.json; get /mcp/schema.json > m.json; get /ai/docs/site-control.md > ctl.md
for n in "$(jq '.requests|length' p.json) requests" "$(jq '.events|length' p.json) events" "$(jq '.tools|length' m.json) typed tools"; do
  grep -q "$n" ctl.md && grep -q "$n" home.html || fail "A6 '$n' is not on / and in site-control.md"; done
names=$(get /ai/docs/site-examples.md | grep -oE "requestType\": ?\"[A-Za-z]+|call\('[A-Za-z]+|\.on\('[A-Za-z]+" | grep -oE '[A-Za-z]+$' | sort -u); [ "$(wc -w <<<"$names")" -ge 5 ] || fail "A6 site-examples.md names under 5 requests or events"
for n in $names; do jq -e --arg n "$n" '[.requests[].requestType,.events[].eventType]|index($n)' p.json >/dev/null || fail "A6 an example uses $n, which protocol.json lacks"; done
get /examples/ | grep -oE 'href="https://github\.com/[^"#]+' | cut -d'"' -f2 | sort -u | alive "A6 dead link on /examples/"
# A7 agent path: router sizes, manifest hashes, chunk urls, MCP platform
rt=$(sed -n '/^## Router/,/^## Feeds/p' llms.txt | grep -o '(https://[^)]*) ([0-9]* bytes)' | tr -d '()'); [ "$(grep -c bytes <<<"$rt")" -ge 8 ] || fail "A7 the router in llms.txt has under 8 rows"
while read -r u b _; do [ -z "$u" ] || [ "$(curl -s -m 60 --compressed "$u" | wc -c)" = "$b" ] || fail "A7 router size is wrong: $u"; done <<<"$rt"
get /ai/manifest.json > man.json; jq -r '.docs|to_entries[]|select(.key%10==0).value|"\(.sha256) \(.url)"' man.json | while read -r h u; do
  [ "$(curl -s -m 60 "$u" | sha256sum | cut -d' ' -f1)" = "$h" ] || fail "A7 manifest sha256 is wrong: $u"; done; get /ai/corpus.json > c.json
jq -r '([.chunks[]|select(.url|startswith("https://")|not)]|length) as $rel | ([.chunks[]|select(.text|test("<img |<p align|shields\\.io"))]|length) as $raw
  | (select($rel>0)|"\($rel) chunk urls are not absolute"), (select($raw>0)|"\($raw) chunks hold raw HTML or badge markup") | "FAIL A7 corpus: "+.' c.json
jq -r '.chunks[].url|split("#")[0]' c.json | sort -u | awk 'NR%9==1' | alive "A7 chunk url is dead"
for id in ws:request:SetInputSettings mcp:tool:wait_for; do jq -e --arg i "$id" '[.chunks[]|select(.id==$i)]|length==1' c.json >/dev/null || fail "A7 no chunk $id"; done
get /mcp/index.md | head -c 1500 | grep -qi linux || fail "A7 /mcp/index.md does not name its platform in the first 1500 characters"; grep -qi linux ctl.md || fail "A7 site-control.md does not name the MCP platform"
# A8 search on /ai/: a plain question and two exact names each put their own document first (the first hit, whatever it links)
while read -r q ok; do want "A8 search '$q'" "/ai/ 1440 900 0 q=$q" "(select(.hit_first|test(\"$ok\")|not)|\"first hit is \(.hit_first), want $ok\")"; done <<'Q'
install%20on%20windows site-download|obs-rust\\.com/#
SetInputSettings /websocket/#SetInputSettings
wait_for /mcp/#wait_for
Q
# B what a visitor sees, from headless Chromium: probe.html reads the fetched live page in a same-origin frame
ALL='(select(.overflow_px>0)|"scrolls sideways by \(.overflow_px) px"),(select(.small_text>0)|"\(.small_text) texts under 12 px"),(select(.small_controls>0)|"\(.small_controls) controls under 24 px"),(select(.nav_clipped>0)|"\(.nav_clipped) nav links off screen"),(select(.third_party|length>0)|"third-party request to \(.third_party[0])")'
for p in $PAGES /nope; do for s in "390 844" "1440 900"; do want "B $p at ${s% *} px" "$p $s" "$ALL"; done; done; want "B / at 320 px" "/ 320 640" "$ALL"
HERO='(select(.hero_w<MINW or .hero_bottom_vh>1)|"largest image on the first screen is \(.hero_w) px wide, ending at \(.hero_bottom_vh) screens"),(select(.cta=="" or (.cta|test("beta";"i")))|"first-screen download action reads: \(.cta)")'
want "B / first screen at 1440 px" "/ 1440 900" "${HERO/MINW/640}"; want "B / first screen at 390 px" "/ 390 844" "${HERO/MINW/330}"
want "B / with JS off" "/ 1440 900 1" '(select(.dl_links<6 or .hashes<6)|"\(.dl_links) download links and \(.hashes) SHA-256 on the page")'
want "B /websocket/ with JS off" "/websocket/ 1440 900 1" "(select(.ids<$(jq '(.requests|length)+(.events|length)' p.json))|\"only \(.ids) anchored entries are visible\")"; get /assets/site.css | grep -q ':focus-visible' || fail "B site.css has no :focus-visible ring"
# S craft, measured, one line per item and page: S1 one system (#26), S2 the object leads (#27), S3 pictures and motion (#28), S4 console (#29), S5 search (#30)
SCALE='[12,13,15,17,19,22,30,40,52,72,96]'; RAD='["4px","6px","50%"]'
S1="(select(.sizes-$SCALE|length>0)|\"type sizes off the scale: \(.sizes-$SCALE|map(tostring)|join(\" \"))\"),(select(.radii-$RAD|length>0)|\"radii off the system: \(.radii-$RAD|join(\" \"))\"),(select(.measure>40)|\"body text runs \(.measure) em wide\"),(select(.orphans>0)|\"\(.orphans) card grids end in a lone card\"),(select(.h1!=H1)|\"h1 is \(.h1) px, not H1\")"
S2='(select(.obj_top>TOP or .obj_w<MINW)|"its object ([data-object]) starts \(.obj_top) screens down, \(.obj_w) px wide"),(select(.screens>MAX)|"\(.screens) screens long, over MAX")'
s2(){ x=${S2//TOP/$1}; x=${x//MINW/$2}; echo "${x//MAX/$3}"; }; while read -r p m1 m2; do want "S1 $p at 1440 px" "$p 1440 900" "${S1//H1/72}"; want "S1 $p at 390 px" "$p 390 844" "${S1//H1/40}"; want "S2 $p at 1440 px" "$p 1440 900" "$(s2 0.6 560 $m1)"; want "S2 $p at 390 px" "$p 390 844" "$(s2 0.85 330 $m2)"
  want "S3 $p eases" "$p 1440 900" '(select(.easing<0.9)|"\(.easing*100|round)% of links, buttons and summaries have a transition, want 90%")'; done <<'T'
/ 6.5 12
/websocket/ 15 30
/examples/ 7 10
/ai/ 5 10
/mcp/ 10 18
T
want "S3 / pictures" "/ 1440 900" '(select(.pictures<2)|"\(.pictures) real pictures 300 px or wider, want 2")'
og=$(grep -oE 'property="og:image" content="[^"]*' home.html | cut -d'"' -f4); curl -s -m 60 "$og" -o og.png; [ "$(od -An -tu1 -j16 -N8 og.png | awk '{print $1*16777216+$2*65536+$3*256+$4 "x" $5*16777216+$6*65536+$7*256+$8}')" = 1200x630 ] && [ "$(wc -c < og.png)" -le 200000 ] || fail "S3 the social card is not a 1200x630 PNG under 200 KB"
want "S3 / motion" "/ 1440 900" '(select(.anim<1 or .anim>6)|"\(.anim) animated elements, want 1 to 6")'   # 901 below: a second cache key
XF=--force-prefers-reduced-motion want "S3 / with reduced motion" "/ 1440 901" '(select(.anim>0)|"\(.anim) elements still animate")'
kf=$(get /assets/site.css | grep -o '@keyframes' | wc -l); inf=$(get /assets/site.css | grep -o 'infinite' | wc -l); pk=$(for p in $PAGES /nope; do get $p; done | grep -c '@keyframes')
[ "$kf" -le 3 ] && [ "$inf" -le 1 ] && [ "$pk" = 0 ] || fail "S3 site.css: $kf @keyframes (at most 3), $inf that repeat (at most 1), $pk pages with their own (0)"
want "S4 /websocket/#demo" "/websocket/ 1440 900 0 demo" '(select([0,2,6,7]-.ops|length>0)|"the replay shows ops \(.ops|map(tostring)|join(" ")), want 0 2 6 7"),(select(.recorded=="")|"the replay does not say recorded or scripted, and from which release"),(select(.state|test("^connected";"i"))|"the tally claims a live connection")'
want "S5 /ai/ idle" "/ai/ 1440 900" '(select(.slash!="q")|"/ does not focus the search box"),(select(.tries<4)|"\(.tries) example queries offered, want 4")'
want "S5 /ai/ results" "/ai/ 1440 900 0 q=install%20on%20windows" '(select(.hits<3 or .hit_h>200)|"\(.hits) hits, the tallest of the first five \(.hit_h) px, over 200"),(select(.hit_copy<5)|"\(.hit_copy) of the first five hits have a copy button"),(select(.count|test("[0-9]")|not)|"no aria-live result count")'
# D pictures for the judge, in shots/ (the live page in a frame of the stated size)
shoot home-1440 / 1440 900; shoot home-390 / 390 844; shoot examples-1440 /examples/ 1440 900; shoot mcp-390 /mcp/ 390 844; shoot console-1440 /websocket/ 1440 900 demo; shoot search-1440 /ai/ 1440 1400 q=install%20on%20windows
```

**What changed from Revision 6's script** (an audit of S and D; A, B and S5 are as they were).
*Entangled:* an `S1-2` line needed #26, #27 and #28 together; it is now `S1`, `S2` and
`S3 … eases`, one item each. *Flaky:* the `/` key makes `/ai/` redraw, and the probe read a
detached element as a `null` size; it skips those. *Unreachable or on a knife edge:*
`/examples/` sat at its 6-screen limit and `/ai/` 0.4 under, so they get 7 / 10 and 5 / 10,
and `/` 6.5 / 12; a 12 px receipt line failed the 40 em measure, which now reads body text
only; D9 asked for five results in a 900 px frame that fits two, so its picture is 1400 px
tall and it asks for three; a replay nobody recorded could pass only by saying "recorded",
so "scripted" passes too. *Not worth their cost:* the mascot checks (no small mascot exists,
and a 160 px robot would compete with the search box), the ban on any page `<style>` and
the typed form (item 19). *Not for an eye:* D7 read CSS and is now the `S3 site.css` line;
D5 and D6 no longer ask the judge to count sizes or measure bands, which S1 and S2 do.
*Verified:* `--force-prefers-reduced-motion` switches the media query in this Chromium, in a
frame too. The probe frames a local copy of the live page with `history.replaceState`
neutralised (a `file:` frame may not rewrite its URL).

**C. Cold trials.** Each is one fresh sub-agent with a fetch tool, no repository and no prior
context, three fetches per question; the judge checks the answer against the named source.

1. **Streamer**, from `/`: the Windows x64 file of the newest stable release with its SHA-256,
   and one thing to expect. Pass: the hash equals the line in `sums.<stable tag>`; the limit
   is one of the receipted sentences in `home.json`.
2. **Builder**, from `/`: which surface for "a button on another PC that switches scene"
   (WebSocket) and for "an agent on the OBS machine that waits until recording is active"
   (MCP), `SetCurrentProgramScene`'s fields, `wait_for`'s arguments, where the MCP server
   runs. Pass: both choices right, fields equal `p.json` and `m.json`, the platform is Linux.
3. **Agent**, from `/llms.txt`: the Linux AppImage of the newest stable release with its
   SHA-256; `SetInputSettings`'s fields; an MCP client config and a three-call session; how
   to claim an issue; the percent of libobs ported and its commit. Pass: four of five
   correct, each citing a fetched URL whose body contains the fact.

**D. Judgement.** Each line is a yes/no question; a "no" fails it and the judge names the
element at fault. D1 to D4 ask whether the site is honest, D5 to D9 whether it is stunning.
Method for D5 to D9: open the named file in `shots/` (the live page at the stated size;
downscale to 800 px wide if the harness caps image size) and answer from the picture and the
named criteria, not from the S lines, which already count.

1. On the first screen (`home-1440.png`), could `/` not be mistaken for a template: the real
   application readable, one headline figure with its receipt, one primary action?
2. Of ten sentences, the first under every second heading across the five pages, is none a
   superlative, or an absolute promise without a receipt beside it?
3. Are limits as easy to find as the pitch: on the page, next to the download they limit?
4. Does colour carry only the meanings of §6: hazard marks real cautions (beta, unsigned, the
   permission-skipping prompt, a replay); the tally is unlit unless the console is connected?
5. **One hand.** `home-1440.png` beside `examples-1440.png`, and `home-390.png` beside
   `mcp-390.png`: does each pair read as two pages of one site: the same header, the same
   start (eyebrow, h1, lede) at the same left edge and weight, the same plates and buttons?
6. **The object leads.** In each of the six pictures, is the first thing the eye lands on the
   page's object (the app, the console with traffic, the search box with results, the agent
   session, a runnable snippet), readable, with nothing decorative larger than it?
8. (D7 is retired: S3 measures motion.) **The console plays.** In `console-1440.png` (`/websocket/#demo`, nothing connected): could
   someone new to obs-websocket follow the exchange: four or more frames, each with direction,
   op name and indented JSON; "recorded" or "scripted" with a release tag, in the caution
   colour; the tally unlit; a reference entry visible beside or below the console?
9. **Search answers.** In `search-1440.png` ("install on windows", a 1400 px tall frame): does
   the first result read as the answer (the site's download or install text, not a CI note);
   are three or more results on screen, each with kind, title, breadcrumb and a marked
   snippet of two lines or fewer; and are the result count and a copy control visible?

## 12. Non-goals

No framework, bundler, analytics, cookie banner or third-party embed. No server-side search,
hosted MCP endpoint or embedding service. No hand-edited copy of upstream docs. No blog, no
light theme, no new workflow files. No claim the build cannot check. No stock art, carousel,
autoplaying video, scroll-jacking or motion that carries no state.
