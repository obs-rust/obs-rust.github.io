# obs-rust.com — design document

Revision 4 — 2026-11-18. Living document; supersedes Revision 3 (same day, in git history).

Revision 3 set a done bar; PRs #7 and #8 shipped the typed tooling, the real screenshot and
the checksums, and #9 (the agent router) is landing. This revision judges the live site again,
cuts P0 to the six items between it and an LGTM, and makes §11 a script. Figures were measured on
https://obs-rust.com on 2026-11-18, 07:36 to 08:30 UTC (site `44fd405`, obs-studio@`a3a58f069`),
with curl and headless Chromium at 1440x900 and 390x844. They are evidence, not site copy.

## 1. Position

> obs-studio-rust is real, it is OBS, and you can run it, script it and read all of it today.

| Audience | Job | Succeeds when |
|---|---|---|
| Streamers | Decide to try it | On the first screen of `/` they see the real app; within three taps they know what does not work yet and hold a verified installer for their OS |
| Builders | Call OBS from code | They pick WebSocket or MCP from one table, find a request with its fields, and send it to their own OBS without leaving the page |
| AI agents | Answer or act correctly | Given only `https://obs-rust.com/llms.txt`, a cold agent answers an install, API, MCP or port-process question with a citable URL in three fetches or fewer |

When goals conflict: truth of a claim, then agent-readable text, then visual polish.

## 2. Shipped

Verified on the live site, not read from PR descriptions.

| Item | Evidence on obs-rust.com | PR |
|---|---|---|
| R2 P0 #1, #2, #5, #6, #8 | libobs figure from `conversion.json`; `tools/check.py` in `pages.yml`; mobile nav; self-hosted fonts, no third-party request on any page; lazy corpus load; `/404.html` returns 404 | #2, #4 |
| `/mcp/` | 30 tools and 2 resources from the server's schema; `schema.json`, `tools.json`, `server.json`, `index.md` all 200 | #3 |
| R2 P0 #3, #4 | Corpus `schema_version` 2 with typed `ws-*`, `mcp-tool`, `ledger-*` chunks; no prose chunk over 2400 characters outside a table or fence | #5 |
| Typed tooling | `tools/models.py` (pydantic, frozen dataclasses); `pages.yml` runs basedpyright strict; the last four runs on `main` are green | #7 |
| R3 P0 #3 | Hero is `/assets/main-window.webp`: 34,210 B, 1280x774, `alt`, `width`, `height`, receipt to the screenshot at the built commit. "Starting Soon", "BRB" and `requestAnimationFrame` are on no page | #8 |
| R3 P0 #5 (part) | 9 download links, 9 full SHA-256, 9 of 9 equal to the release's `SHA256SUMS`; all three OS cards and hashes present with JS off; the visitor's OS card moves first | #8 |
| R3 P0 #4 (part) | "Rust has passed C" is gone; "crashes" is gone from every meta description | #6, #8 |

**In progress, not counted as shipped: R3 P0 #2 (PR #9).** It deployed while this revision
was written. First probe: the router heads `llms.txt` and `/ai/` (12 rows, 12 of 12 printed
sizes equal the bytes served); `/ai/manifest.json` lists 106 documents (8 of 8 sampled SHA-256
match); the three `site-*.md` documents are in `llms-ctx.txt` (221 KB). The rest is P0 #2.

## 3. Critique of the live site

**A streamer on `/`**

1. **The app is too small to read, and on a phone it is below the first screen.** At 1440x900
   the 1280 px screenshot renders 497 px wide beside a 112 px, seven-word slogan 385 px tall.
   At 390x844 it is 299 px wide and ends at 1.30 viewport heights.
2. **A stable release exists and the site hides it.** `obs-studio-rust-v1.0.0` (2026-11-01,
   not a prerelease) is on GitHub; the page offers only `v1.0.1-beta.20261108`, ten days old,
   under "public beta", while its own ledger card says "The certified 1.0.0 release is available".
3. **The download is far down and hard to verify.** `#download` starts 2.27 viewports down on
   desktop and 3.89 on a phone (11,305 px page, eight sections where §5 allows six). Hashes are
   10.5 px `--dim` text over two lines, with no copy control or verify command.
4. **Nothing says what does not work.** The README says macOS packages are notarized only
   "when the project's release credentials are configured", that SmartScreen warns on Windows
   and that the Flatpak does not update itself. On the page the only caution is "beta".
5. **Absolutes without a receipt.** "Nothing you rely on breaks"; "four tiers of tests keep
   the two identical"; "Plugins compiled for OBS load without a rebuild"; on `/websocket/`,
   "every client written for OBS 28+ works against it"; on `/examples/`, "Every v5 client works".
6. **Three denominators in one block, and a receipt nobody can check.** `#crossover` shows
   60.2% of libobs, a Rust 38.7 / C 38.4 language bar and "Whole app 16.9%". The receipt links
   a moving branch; the file changed a minute after the build (60.25 to 60.36). The proof
   strip still counts "27 Forks" and upstream's "147 WebSocket requests".
7. **Wrong emphasis.** The ledger preview leads with three MCP entries while the 386 fixed
   upstream bugs stay a number; `claude --dangerously-skip-permissions` has no caution mark.
8. **Small and unfocusable.** 36 text nodes on `/` are under 12 px; no stylesheet has a
   `:focus-visible` rule; the nav strip clips a link at 390 px and two at 320 px. `og:image` is
   a 768 KB square PNG; the 643 KB `obs-rust-logo.png` is deployed and referenced by nothing.

**A plugin or tool builder**

9. **`/websocket/` is broken sideways.** `table.ft` has `overflow: visible`: the document is
   393 px wider than a 1440 px window and 1015 px wider than a 390 px one, so a phone zooms the
   whole page out. `/mcp/` overflows by 59 px and `/examples/` (`table.libs`) by 103 px.
10. **`/websocket/` is one 316 KB page**, 73,839 px tall: 774 focusable elements, 1445 text
    nodes under 12 px, 147 "Try" buttons under 24 px, no text twin per request. Headings skip
    from `h1` to `h3` here and to `h4` on `/ai/`, `/mcp/`, `/examples/` and the 404 page.
11. **No "which API" for a human, and a wrong one for agents.** `/control/` is 404 and `/`
    shows two unrelated cards. `site-control.md` says both surfaces "run locally" (a WebSocket
    client can be remote) and, like `/mcp/index.md`, never says the MCP server builds only on
    Linux; on `/mcp/` that fact sits far below a clone-and-build quick start.
12. **Examples are typed into `src/examples.html`**: not files, not run by anything. The ten
    names they use exist in `protocol.json` today, and no check keeps it so.

**An AI agent**

13. **Chunk URLs cannot be followed.** 1470 of 1716 chunks carry a relative `url`
    (`/ai/docs/readme.md`) while typed chunks carry absolute ones, and none of the 993 prose
    chunks has an anchor, so a citation points at a whole file.
14. **Noise in the core tier.** `readme#top` is badge HTML; 16 chunks hold raw `<img` or
    shields.io markup; the README's "Hall of Fame" rides into `llms-ctx.txt`. Six prose chunks
    are under 300 characters. The libobs C reference has no `c-symbol` chunk.
15. **Search is heavy and weak on plain questions.** The first keystroke downloads all of
    `corpus.json`, 619 KB gzipped. `SetInputSettings` and `wait_for` rank their typed chunk
    first; "install on Windows" returns "Flatpak PCH cache qualification" first.
16. **Crawlers see ten URLs.** `sitemap.xml` lists 10 and leaves 106 documents out. Only
    `/mcp/` declares a markdown alternate; there is no JSON-LD.
17. **The gate saw none of this.** `check.py` has no overflow, heading, text-size or claim
    check, and nothing in `pages.yml` fetches the site after a deploy.

## 4. Principles and constraints

1. **Receipts, visibly.** Every figure is computed at build time and shows its source, commit
   and date, linked at a commit and never at a branch. No receipt, no number.
2. **The project's own measures only**: `conversion.json`, the features ledger, the releases
   API, `protocol.json`, `control-api.schema.json`.
3. **Show the thing, say what does not work.** The real application and release assets, and
   their limits beside the pitch, quoted from upstream files.
4. **Fail closed.** If a source cannot be fetched or parsed the build fails; stale beats wrong.
5. **Text first; static, first-party, small.** Every page an agent may need has a markdown
   twin. No framework or third-party origin; JS only enhances.

Constraints from the maintainer; a change that breaks one is not done:

- **Python runs only through `uv run`.** Every Python change keeps strict typing: pydantic
  models or frozen dataclasses for all data, no duck-typed dicts, and `basedpyright` strict
  clean (the `pages.yml` step). New inputs (`claims.toml`, releases) get a model in `models.py`.
- One generator (`tools/build.py`, `corpus.py`, `mcp.py`), one gate (`tools/check.py`), the
  existing `pages.yml`. No new workflow file. Each backlog item lands with its check in
  `check.py`, so what §11 measures on the live site was already measured on `_site/`.

## 5. Information architecture

Nav on every viewport, all links visible without scrolling at 320 px: **Download · WebSocket
API · MCP · Examples · For AI**, then GitHub. Five pages and the 404 are enough for an LGTM;
the pages marked P1 are depth.

```
/             Six sections in order: hero (screenshot, headline figure, one action), proof
              strip, download, what works and what does not, what changed, build with it
              (WebSocket-or-MCP table, examples, AI, contribute)
/websocket/   Reference and live console        /mcp/   Server reference, /mcp/index.md
/examples/    Checked snippets and links out    /404.html   Mascot and the nav links
/ai/          Router, feeds, search; /ai/docs/*.md, corpus.json, manifest.json, claims.json;
              /llms.txt, /llms-ctx.txt, /llms-full.txt
P1 depth:     /download/ /changes/ /progress/ /control/ /websocket/<Name>.md /mcp/tools/<name>.md
```

## 6. Visual system

The brand stays. Colour has fixed meaning; a colour used outside its meaning is a bug.

| Token | Value | Means |
|---|---|---|
| `--bg0/1/2`, `--plate`, `--edge` | `#0b0c0d` to `#24282b`, seams `#33383c` | canvas, steel plates, 1 px seams |
| `--rust` | `#e8631a` | Rust code, primary action, the one accent per view |
| `--cu` | `#3fa58a` | verified or computed: receipts, links, connected state |
| `--haz` | `#f2b705` | caution only: beta, unsigned, untested, destructive |
| `--red` | `#ff4040` | tally: on air, error. Never decoration |
| `--c`, `--cpp` | `#8a96a3`, `#5d6b7a` | legacy C and C++ in data graphics |
| `--fg`, `--fg2`, `--dim` | `#ece8e1`, `#c9c5bd`, `#8e949a` | text; `--dim` never under 13 px |

Type: **Big Shoulders Stencil Display 900** for h1, h2 and hero numerals, six words at most,
h1 at most 72 px on desktop and 40 px on a phone so the screenshot leads; **Barlow 400/600**
for body and UI; **JetBrains Mono** for code, labels, receipts and data. No text under 12 px.
Layout: 1180 px max, 8 px scale, 4 px radius on controls, 6 px on plates. Tables and code
scroll inside their own box; the page never scrolls sideways.

Signature moments, four and only four:

1. **The program monitor.** Bezel, tally and dock around the upstream screenshot: 640 px or
   wider on desktop, whole within the first screen on a phone. Tally unlit.
2. **The receipt.** One component, `.receipt`, patina-green mono under every computed number,
   its link a 40-hex permalink. It is the proof mark.
3. **The headline figure.** Exactly one `.headline[data-value]` per view: libobs lines ported.
   Other denominators are labelled rows beneath it, or leave the page.
4. **The tally light.** Lit red only for live state: the WebSocket console connection.

The bronze robot appears on `/ai/`, `/mcp/`, the 404 page and the social card, from one file
under 60 KB. Motion: CSS only, paused offscreen, off under `prefers-reduced-motion`.

## 7. Content and corpus

Voice: plain, specific, verifiable; no superlatives, no absolutes ("every", "nothing",
"identical"). A promise or a limit is a **claim**: an entry in `claims.toml` with `id`, `kind`
(`promise` or `limit`), `page`, `text` (a literal substring of the served HTML), a
commit-pinned `source_raw` URL and a `pattern` (ERE) that must still match there. The build
fails when one stops matching, and publishes the set as `/ai/claims.json` (`{"claims": [...]}`).

- **Streamers.** Proof strip: four receipts (libobs converted, upstream bugs fixed,
  user-visible changes, newest stable and newest beta with dates). Download: both channels,
  visitor's OS first, each file with size, SHA-256, a copy control and the verify command.
  Beside it, at least three limits (signing, tested platforms, updates) and how to go back.
  The ledger preview leads with fixed bugs and skips automation entries.
- **Builders.** One computed table on `/` and in `site-control.md` (transport, where it runs,
  count of operations, auth, platforms, waits). Examples name only requests, events and tools
  that exist. **Agents.** The router (task, one file, exact bytes) heads `llms.txt` and `/ai/`.

**Tiers**, by rule in `build.py`: `core` (README without badges or the hall of fame, AGENTS,
CONTRIBUTING, SECURITY, CODESTYLE, CONSTITUTION, ledger summary, `site/*.md`, MCP and
WebSocket narrative) fills `llms-ctx.txt`; then `reference`, `process`, `archive`.

**Chunks.** Split on headings; each opens with its breadcrumb; HTML and badge markup are
stripped. Prose is 300 to 2400 characters, never split inside a fence or table. Typed chunks
are one unit each: `ws-request`, `ws-event`, `ws-enum`, `mcp-tool`, `mcp-resource`, `c-symbol`,
`ledger-entry`, `ledger-fix`. Every `url` is absolute and resolves; a prose `url` ends in its
heading's `#anchor`. Fields: `id` (structural: `<doc>#<heading-path>`, `ws:<kind>:<Name>`,
`mcp:tool:<name>`, `c:<symbol>`), `doc`, `group`, `tier`, `kind`, `breadcrumb`, `url`, `source`
(permalink), `text`, `chars`, `tokens_est`, `sha256`.

**Feeds.** `llms.txt`: 80 links and 25 KB at most, each `[title](url): first sentence`;
`llms-ctx.txt` under 300 KB. Markdown opens with front matter (`title`, `source`, `commit`,
`tier`, `tokens_est`). The sitemap lists every HTML page and markdown document;
`manifest.json` gives each document's bytes and SHA-256. Embedding search stays rejected.

## 8. Budgets and accessibility

Checked by `tools/check.py` on `_site/` and by §11 on the live site. Live values in brackets.

| Budget | Limit |
|---|---|
| Third-party origins requested by any page | 0 [0] |
| `/` HTML + CSS, gzipped | 40 KB [11.8 KB] |
| `/websocket/`, `/mcp/`, `/ai/` HTML, gzipped | 60, 20, 30 KB [35.4, 13.3, 7.9 KB] |
| First search on `/ai/`, gzipped (P1) | 150 KB [619 KB] |
| Fonts, all files | 160 KB [157.7 KB, six files, four Barlow weights] |
| Largest image on `/` | 120 KB, explicit `width` and `height` [34 KB] |
| Social card (P1) | 1200x630 PNG under 200 KB [768 KB square]; unreferenced assets 0 [1, 643 KB] |
| `llms.txt` / `llms-ctx.txt` | 80 links, 25 KB [40, 16.6 KB] / 300 KB [221 KB] |

Accessibility is WCAG 2.2 AA. The probe in §11 checks: no horizontal overflow at 320, 390 and
1440 px; one `h1`, no skipped level; `alt`, `width` and `height` on images; no text under 12 px;
controls 24x24 px or larger; every page complete with JS off. Static checks: a `:focus-visible`
ring, labels on inputs, a skip link, contrast (body 4.5:1, stencil and borders 3:1).

## 9. WebSocket reference and console

Sticky index left, reference centre, console docked right above 1200 px and a bottom sheet
below it, so "Try" never scrolls the reader away. "Try" builds a typed form from
`requestFields`; a missing required field disables Send and says why. The password is never
stored. A failed connect names the likely cause and offers a `websocat` command.

## 10. Backlog

Numbers are Revision 3's (`17a`/`17b` split item 17). An item is done when its check passes in
`tools/check.py` on `_site/` and in §11 on the live site.

### P0: what stands between the site and an LGTM

| # | Item | Acceptance check |
|---|---|---|
| 4 | **Claims with receipts, one headline.** `claims.toml` and `/ai/claims.json`; rewrite or receipt every absolute in critique 5; one `.headline`; proof strip per §7; conversion receipt pinned to a commit; a `--haz` caution on the `--dangerously-skip-permissions` block. | §11 A3, A4, A6: no banned phrase on any page; `claims.json` has 8 or more claims, each `text` on its page and each `pattern` in its pinned source; exactly one `.headline[data-value]` on `/`, within 0.06 of `libobs.all.percent` in the linked `conversion.json`; the build fails when a pattern is removed from a fixture. |
| 5 | **Stable and beta downloads.** Both channels from the releases API on `/` and in `site-download.md`; copy control and verify command; hashes at 12 px or more on one line where width allows. | §11 A5: the newest non-prerelease and the newest prerelease `obs-studio-rust-v*` tags each have 3 or more files linked, each with the SHA-256 from that release's `SHA256SUMS`; the build fails on a missing hash. |
| 8 | **"What works, what does not"** next to the download: signing and notarization status, SmartScreen, tested distributions, Flatpak updates, how to go back, each a `limit` claim. | §11 A4: 3 or more claims with `kind: "limit"` and `page: "/"`; a cold reader names one limit (§11 C1). |
| 12 | **Home in six sections, app first.** Order of §5; screenshot leads; download within two screens; the WebSocket-or-MCP table with computed counts. | §11 A6: "N requests", "N events" and "N typed tools" on `/` and in `site-control.md` equal `protocol.json` and `mcp/schema.json`. §11 B: at 1440x900 the hero image is 640 px or wider, ends inside the first viewport, and `#download` starts within 2.0 viewports; at 390x844 the image is 330 px or wider and ends inside the first viewport, and `#download` starts within 3.0; six `section` elements; four or more `.receipt`. |
| 17a | **Nothing broken on any page**: tables scroll in their box, heading order, 12 px floor, 24 px controls, nav fits, `:focus-visible`. | §11 B on all five pages and `/nope` at 390 and 1440: `overflow_px <= 0`, one `h1`, no heading skip, no text under 12 px, no control under 24 px, no clipped nav link; `/` also at 320; `site.css` has `:focus-visible`. |
| 2 | **Close the agent path** (absorbs the URL line of #1 and the sitemap line of #11). Absolute, anchored chunk URLs; markup stripped; no prose chunk under 300; the MCP platform in the first 1500 characters of `/mcp/index.md` and in `site-control.md`; full sitemap. | §11 A7: router sizes equal bytes served; sampled manifest hashes match; no relative or dead chunk `url`; no prose `url` without `#`; no `<img`, `<p align` or shields.io in chunk text; "Linux" in both MCP texts; the sitemap lists at least as many URLs as the manifest has documents and each sampled one is 200. |

### P1: the pages that make the case

| # | Item | Acceptance check |
|---|---|---|
| 6 | **Gate v2**: every §11 A and B check in `check.py` on `_site/` (the probe runs on local files); a post-deploy step in the existing job runs §11 A1. | `check.py` exits non-zero for each of: a table wider than its page, a skipped heading, 11 px text, a relative chunk `url`, a claim whose pattern is gone; the deploy job fails if `/llms.txt` is not 200 `text/plain` or `/nope` is not 404. |
| 7 | **Social card and asset hygiene.** Generated 1200x630 card; delete the unused logo; mascot on the 404 page. | `og:image` on every page is a 1200x630 PNG under 200 KB; no file in `_site/assets/` is unreferenced; `/404.html` has the mascot with `alt`. |
| 1 | **Corpus residue**: `c-symbol` chunks for the libobs reference; deterministic output. | One `c-symbol` chunk per Sphinx directive; two builds from the same inputs give a byte-identical `corpus.json` apart from the timestamp. |
| 15 | **Search index and retrieval eval**: `/ai/search.json`, `tools/eval_corpus.py`, an `aria-live` result count. | First search transfers under 150 KB gzipped; 90% of 30 or more checked-in questions have the expected chunk in the top 5, "install on Windows" among them. |
| 11 | **Markdown twins**: `index.md` per page, `rel="alternate"`, JSON-LD on `/`. | Every HTML page's alternate link resolves; JSON-LD parses and its version equals the newest stable tag. |
| 18 | **Per-item WebSocket pages and `.md`.** | For every name in `protocol.json`, `/websocket/<Name>.md` exists and is in the sitemap. |
| 16 | **Examples as files** `examples/<lang>/*`, highlighted at build, served raw, with one MCP agent session. | Every request, event and tool name used exists in `protocol.json` or `mcp/schema.json`; Python examples pass `uv run python -m py_compile`. |
| 13 | **MCP v2**: per-tool pages and `.md`; `server.json` valid against the vendored schema. | `/mcp/tools/<name>.md` exists for every tool; `server.json` validates against `tools/vendor/server.schema.json`. |
| 9, 10, 14 | **`/changes/`, `/control/`, `/progress/`** from the ledger, the two schemas and `conversion.json`. | Entry and figure counts equal their sources; each page reads complete with JS off; one receipt each. |
| 17b | **CSS consolidation**: no page `<style>`; two Barlow weights. | No `<style` in any `_site/**/*.html`; `fonts.css` declares two Barlow faces. |
| 19 | **Console v2** per §9. | An empty required field blocks Send with a message; `localStorage` never holds the password; scroll position is unchanged after "Try". |

### P2: depth

20 `/websocket/obs-websocket.d.ts` (`tsc --noEmit` accepts it). 21 `/libobs/` symbol index (every
`c-symbol` id resolves). 22 topic bundles `/ai/bundles/*.txt` (sizes in `llms.txt`). 23 installable
MCP `packages` in `server.json` (URL and hash equal a release asset and its `SHA256SUMS` line).
24 contributor strip (figures equal `leaderboard.json`, with a receipt). 25 `/releases.xml` (its
newest entry equals the newest tag) and a launch-speed figure (read from JSON, never from prose).

## 11. The done bar

The judge works on the **live site** only; nothing is taken from a build log, a PR or this
document's brackets. Verdict: **LGTM** when A and B print no `FAIL` line, all four trials in C
pass and at most one line of D fails; otherwise **FAIL:** followed by the failed lines. Budget
30 minutes: the script (A and B) ran in 2 min 56 s, C takes fifteen, D five. Needs `curl`, `jq`,
`perl` and the Chromium at `~/.hermes/tools/chromium-1208/chrome-linux64/chrome`. Run against
the site as measured for this revision, the script prints 46 `FAIL` lines (29 in A, 17 in B).
It samples at random, so run it twice; a probe that returns nothing is a `FAIL`.

```bash
cd "$(mktemp -d)"   # then extract the two blocks below from this file and run them
awk '/^```html probe/{f="probe.html";next} /^```bash judge/{f="judge.sh";next} /^```$/{f=""} f{print > f}' /path/to/DESIGN.md
bash judge.sh | tee verdict.txt; grep -c '^FAIL' verdict.txt   # 0 is a pass for A and B
```

```html probe
<!doctype html><meta charset="utf-8"><body><script>
const P=new URLSearchParams(location.search),w=+P.get('w'),h=+P.get('h'),f=document.createElement('iframe');
f.width=w;f.height=h;f.style.border=0;f.src='page.html';document.body.append(f);
f.onload=()=>setTimeout(()=>{const d=f.contentDocument,W=f.contentWindow,q=s=>[...d.querySelectorAll(s)],box=e=>e.getBoundingClientRect(),
 vis=e=>box(e).width>0&&box(e).height>0,px=e=>parseFloat(W.getComputedStyle(e).fontSize),small=e=>vis(e)&&(box(e).width<24||box(e).height<24),
 H=q('h1,h2,h3,h4,h5,h6').map(e=>+e.tagName[1]),hero=d.querySelector('img[src*="main-window"]'),dl=d.querySelector('#download');
const r={w:W.innerWidth,overflow_px:d.documentElement.scrollWidth-W.innerWidth,h1:q('h1').length,heading_skips:H.filter((n,i)=>i&&n>H[i-1]+1).length,
 img_no_alt:q('img:not([alt])').length,img_no_size:q('img:not([width]),img:not([height])').length,
 text_under_12px:q('body *').filter(e=>vis(e)&&!e.children.length&&e.textContent.trim()&&px(e)<12).length,
 controls_under_24px:q('button,summary,input,select,header a,nav a').filter(small).length,nav_clipped:q('header a,nav a').filter(e=>vis(e)&&box(e).right>w+1).length,
 hero_w:hero?Math.round(box(hero).width):0,hero_bottom_vh:hero?+(box(hero).bottom/h).toFixed(2):9,download_top_vh:dl?+(box(dl).top/h).toFixed(2):9,
 sections:q('main section,body>section').length,os_cards:q('#download [data-os]').length,sha:q('#download .sha').length,headline:q('.headline').length,
 receipts:q('.receipt').length,articles:q('article').length,
 third_party:W.performance.getEntriesByType('resource').map(e=>e.name).filter(n=>!/^(https:\/\/obs-rust\.com\/|file:)/.test(n))};
document.body.innerHTML='<pre>'+JSON.stringify(r)+'</pre>'},2500);
</script>
```

```bash judge
B=https://obs-rust.com; GH=https://github.com/obs-rust/obs-studio; API=https://api.github.com/repos/obs-rust
C=~/.hermes/tools/chromium-1208/chrome-linux64/chrome; PAGES="/ /websocket/ /examples/ /ai/ /mcp/"
fail(){ echo "FAIL $*"; }; get(){ curl -s --compressed "$B$1"; }; gz(){ curl -s -H 'Accept-Encoding: gzip' "$B$1" | wc -c; }
lim(){ [ "$2" -le "$3" ] || fail "$1 = $2 > $3"; }; code(){ curl -s -o /dev/null -w '%{http_code}' "$1"; }
# A1 live, fresh, right status and type
[ "$(curl -s "$API/obs-rust.github.io/actions/runs?branch=main&per_page=1" | jq -r '.workflow_runs[0].conclusion')" = success ] || fail "A1 last pages.yml run on main is not green"
get /llms.txt > llms.txt; d=$(grep -o 'Generated [0-9-]*' llms.txt | cut -d' ' -f2)
[ -n "$d" ] && [ $(( ($(date -u +%s) - $(date -u -d "$d" +%s)) / 86400 )) -le 2 ] || fail "A1 site generated '$d', over 2 days ago"
st(){ c=$1; ty=$2; shift 2; for p; do got=$(curl -s -o /dev/null -w '%{http_code} %{content_type}' "$B$p")
  case "$got" in "$c $ty"*) ;; *) fail "A1 $p -> $got";; esac; done; }
st 200 text/html $PAGES; st 404 text/html /nope; st 200 text/plain /llms.txt /llms-ctx.txt /llms-full.txt; st 200 application/xml /sitemap.xml
st 200 application/json /ai/corpus.json /ai/manifest.json /ai/claims.json /mcp/schema.json /websocket/protocol.json
st 200 text/markdown /mcp/index.md /ai/docs/site-download.md /ai/docs/site-control.md /ai/docs/site-examples.md
# A2 budgets of section 8 (bytes; gzipped unless marked raw)
lim "A2 home html+css" $(( $(gz /) + $(gz /assets/site.css) + $(gz /assets/fonts.css) )) 40000
lim "A2 /websocket/" "$(gz /websocket/)" 60000; lim "A2 /mcp/" "$(gz /mcp/)" 20000; lim "A2 /ai/" "$(gz /ai/)" 30000
lim "A2 llms.txt raw" "$(wc -c < llms.txt)" 25000; lim "A2 llms.txt links" "$(grep -c '^- \[' llms.txt)" 80
lim "A2 llms-ctx.txt raw" "$(get /llms-ctx.txt | wc -c)" 300000; lim "A2 hero raw" "$(curl -s $B/assets/main-window.webp | wc -c)" 120000
lim "A2 fonts raw" "$(get /assets/fonts.css | grep -o '/assets/fonts/[^)]*' | sort -u | while read -r f; do curl -s "$B$f" | wc -c; done | awk '{s+=$1} END{print s+0}')" 160000
# A3 nothing retired or absolute is back (case-insensitive, whole HTML of every page)
BAN='rust has passed c|starting soon|requestAnimationFrame|nothing you rely on breaks|every (v5 )?client|keep the two identical|without the bugs|>forks<'
for p in $PAGES /nope; do get $p | grep -oiE "$BAN" | sort -u | sed "s|^|FAIL A3 $p: |"; done
# A4 claims: each is on its page and still in its commit-pinned upstream source; limits are on the home page
get /ai/claims.json > claims.json
jq -e '(.claims|length)>=8 and ([.claims[]|select(.kind=="limit" and .page=="/")]|length)>=3' claims.json >/dev/null 2>&1 || fail "A4 claims.json needs 8+ claims, 3+ limits on /"
jq -r '.claims[]|[.id,.page,.text,.source_raw,.pattern]|@tsv' claims.json 2>/dev/null | while IFS=$'\t' read -r id page text src pat; do
  get "$page" | grep -qF -- "$text" || fail "A4 $id: text is not on $page"
  case "$src" in https://raw.githubusercontent.com/obs-rust/*) curl -s "$src" | grep -qE -- "$pat" || fail "A4 $id: pattern gone from $src";; *) fail "A4 $id: source not pinned";; esac; done
# A5 downloads: newest stable and newest beta, each link with the SHA-256 from that release's SHA256SUMS
get / > home.html; get /ai/docs/site-download.md > dl.md; REL=$(curl -s "$API/obs-studio/releases?per_page=30")
for sel in 'select(.prerelease|not)' 'select(.prerelease)'; do
  tag=$(jq -r "[.[]|select(.tag_name|startswith(\"obs-studio-rust-v\"))|$sel][0].tag_name" <<<"$REL"); curl -sL "$GH/releases/download/$tag/SHA256SUMS" > "sums.$tag"
  for doc in home.html dl.md; do links=$(grep -o "releases/download/$tag/[^\")]*" $doc | sort -u)
    [ "$(grep -c . <<<"$links")" -ge 3 ] || fail "A5 $doc offers under 3 files of $tag"
    for l in $links; do h=$(awk -v f="${l##*/}" '$2==f{print $1}' "sums.$tag"); [ -n "$h" ] && grep -q "$h" $doc || fail "A5 $doc: no SHA-256 for ${l##*/}"; done; done; done
# A6 figures equal their sources
raw=$(grep -o 'https://raw.githubusercontent.com/obs-rust/obs-studio/[0-9a-f]\{40\}/conversion.json' home.html | head -1)
have=$(grep -o 'class="headline" data-value="[0-9.]*"' home.html | grep -o '[0-9.]*"$' | tr -d '"')
[ "$(grep -c 'class="headline"' home.html)" = 1 ] && [ -n "$raw" ] && [ -n "$have" ] || fail "A6 / needs one .headline[data-value] and a commit-pinned conversion.json receipt"
[ -z "$raw" ] || curl -s "$raw" | jq -e --argjson h "${have:-0}" '(.libobs.all.percent-$h)|fabs<=0.06' >/dev/null || fail "A6 headline $have differs from $raw"
get /websocket/protocol.json > p.json; get /mcp/schema.json > m.json; get /ai/docs/site-control.md > ctl.md
for n in "$(jq '.requests|length' p.json) requests" "$(jq '.events|length' p.json) events" "$(jq '.tools|length' m.json) typed tools"; do
  grep -q "$n" ctl.md && grep -q "$n" home.html || fail "A6 '$n' is not on / and in site-control.md"; done
for n in $(get /ai/docs/site-examples.md | grep -oE "requestType\": ?\"[A-Za-z]+|call\('[A-Za-z]+|\.on\('[A-Za-z]+" | grep -oE '[A-Za-z]+$' | sort -u); do
  jq -e --arg n "$n" '[.requests[].requestType,.events[].eventType]|index($n)' p.json >/dev/null || fail "A6 example uses unknown name $n"; done
# A7 agent path: router, manifest, corpus, MCP twin, sitemap
rt=$(sed -n '/^## Router/,/^## Feeds/p' llms.txt | grep -o '(https://[^)]*) ([0-9]* bytes)' | tr -d '()')
[ "$(grep -c bytes <<<"$rt")" -ge 8 ] || fail "A7 router has under 8 rows"
while read -r u b _; do [ -z "$u" ] || [ "$(curl -s --compressed "$u" | wc -c)" = "$b" ] || fail "A7 router size wrong: $u"; done <<<"$rt"
get /ai/manifest.json > man.json; jq -r '.docs[]|"\(.sha256) \(.url)"' man.json | shuf -n 8 | while read -r h u; do
  [ "$(curl -s "$u" | sha256sum | cut -d' ' -f1)" = "$h" ] || fail "A7 manifest sha256 wrong: $u"; done
get /ai/corpus.json > c.json
jq -r '[.chunks[]|select(.kind=="prose")] as $p | [
  (select(([$p[]|select(.chars<300)]|length)>0)|"prose chunks under 300 chars"),
  (select(([$p[]|select(.chars>2400 and (.text|contains("```")|not) and (.text|contains("\n|")|not))]|length)>0)|"prose chunks over 2400 chars"),
  (select(([.chunks[]|select(.url|startswith("https://obs-rust.com/")|not)]|length)>0)|"chunk urls that are not absolute"),
  (select(([$p[]|select(.url|contains("#")|not)]|length)>0)|"prose chunk urls without an anchor"),
  (select(([.chunks[]|select(.text|test("<img |<p align|shields\\.io"))]|length)>0)|"raw HTML or badges in chunk text")] | .[] | "FAIL A7 corpus: " + .' c.json
for u in $(jq -r '.chunks[].url|split("#")[0]' c.json | sort -u | shuf -n 12); do [ "$(code "$u")" = 200 ] || fail "A7 chunk url dead: $u"; done
for id in ws:request:SetInputSettings mcp:tool:wait_for; do jq -e --arg i "$id" '[.chunks[]|select(.id==$i)]|length==1' c.json >/dev/null || fail "A7 no chunk $id"; done
get /mcp/index.md | head -c 1500 | grep -qi linux || fail "A7 /mcp/index.md does not name its platform in the first 1500 chars"
grep -qi linux ctl.md || fail "A7 site-control.md does not name the MCP platform"
sm=$(get /sitemap.xml | grep -o 'https://obs-rust.com[^<]*'); [ "$(grep -c . <<<"$sm")" -ge "$(jq '.docs|length' man.json)" ] || fail "A7 sitemap lists fewer URLs than manifest.json has documents"
for u in $(shuf -n 10 <<<"$sm"); do [ "$(code "$u")" = 200 ] || fail "A7 sitemap url dead: $u"; done
# B layout facts from headless Chromium: probe.html reads the fetched live page in a same-origin frame
probe(){ curl -s --compressed "$B$1" | NOJS="$4" U="$B$1" perl -0pe 's|<script\b.*?</script>||gs if $ENV{NOJS}; s|<head>|<head><base href="$ENV{U}">|' > page.html
  for try in 1 2 3; do timeout 90 "$C" --headless=new --no-sandbox --disable-gpu --allow-file-access-from-files --user-data-dir="$PWD/prof" \
    --window-size=1700,1300 --virtual-time-budget=9000 --dump-dom "file://$PWD/probe.html?w=$2&h=$3" 2>/dev/null | grep -o '{"w":[^<]*' && break; done; }
want(){ r=$(probe $2); jq -e "$3" <<<"$r" >/dev/null || fail "B $1 [$3] got $r"; }   # want LABEL "PATH W H [nojs]" JQ-CONDITION
ALL='.overflow_px<=0 and .h1==1 and .heading_skips==0 and .img_no_alt==0 and .img_no_size==0 and .text_under_12px==0 and .controls_under_24px==0 and .nav_clipped==0 and (.third_party|length)==0'
for p in $PAGES /nope; do for s in "390 844" "1440 900"; do want "$p at ${s% *}" "$p $s" "$ALL"; done; done
want "/ desktop" "/ 1440 900" '.hero_w>=640 and .hero_bottom_vh<=1 and .download_top_vh<=2 and .sections==6 and .headline==1 and .receipts>=4'
want "/ phone" "/ 390 844" '.hero_w>=330 and .hero_bottom_vh<=1 and .download_top_vh<=3'
want "/ at 320" "/ 320 640" '.overflow_px<=0 and .nav_clipped==0'
want "/ without JS" "/ 1440 900 nojs" '.os_cards>=3 and .sha>=6 and .hero_w>=640 and .receipts>=4'
want "/websocket/ without JS" "/websocket/ 1440 900 nojs" ".articles>=$(jq '(.requests|length)+(.events|length)+(.enums|length)' p.json)"
get /assets/site.css | grep -q ':focus-visible' || fail "B no :focus-visible rule in site.css"
```

**C. Cold trials.** Each is one fresh sub-agent with a fetch tool, no repository and no prior
context, three fetches per question; the judge checks the answer against the named source.

1. **Streamer**, from `/`: one thing that does not work yet, and the Windows x64 file of the
   newest stable release with its SHA-256. Pass: the limit is a `limit` claim in
   `claims.json` and the hash equals the line in `sums.<tag>`.
2. **Builder**, from `/`: which surface for "a button on another PC that switches scene"
   (WebSocket) and for "an agent on the OBS machine that waits until recording is active"
   (MCP), with `SetCurrentProgramScene`'s fields and `wait_for`'s arguments. Pass: both
   choices right, and the fields equal `p.json` and `m.json`.
3. **Agent, reading**, from `/llms.txt`: the Linux AppImage of the newest beta with its
   SHA-256; `SetInputSettings`'s request fields; `wait_for`'s arguments; how to claim an issue;
   the percent of libobs ported and its commit. Pass: four of five correct, each citing a
   fetched URL whose body contains the fact.
4. **Agent, acting**, from `/mcp/index.md` only: a client config, a three-call session and the
   platform. Pass: each tool is in `m.json` with its required arguments; the platform is Linux.

**D. Judgement** (two or more failures is FAIL; the judge quotes the element it faults)

1. Above the fold, `/` could not be mistaken for a template: the real application readable,
   one headline figure with its receipt, one primary action.
2. Of ten sentences sampled across the five pages, none is a superlative, an absolute, or a
   promise missing from `claims.json`.
3. The four signature moments of §6 are present and no fifth decoration has appeared.
4. Colour carries only the meanings of §6: hazard marks real cautions (beta, unsigned, the
   permission-skipping prompt); the tally is unlit unless the console is connected.
5. Limits are as easy to find as the pitch: on the page, next to the promise they limit.

## 12. Non-goals

No framework, bundler, analytics, cookie banner or third-party embed. No server-side search,
hosted MCP endpoint or embedding service. No hand-edited copy of upstream docs. No blog, no
light theme, no new workflow files. No claim the build cannot check.
