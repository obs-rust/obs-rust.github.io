# obs-rust.com — design document

Revision 5 — 2026-11-18. Living document; supersedes Revision 4 (same day, in git history).

Revision 4 made the done bar a script. Since then PR #9 (agent router), #11 (stable and beta
downloads, limits), #12 (nothing broken on any page) and #13 (chunk URLs) shipped. This revision
runs that script against the live site, repairs it, and cuts P0 to the four items between the
site and an LGTM. Figures were measured on https://obs-rust.com on 2026-11-18, 08:30 to 09:35 UTC
(site `9e19464`, obs-studio@`c5046039d`), with curl and headless Chromium; they are evidence.

**Revision 4's script, run as written:** 44 `FAIL` lines (27 in A, 17 in B) at 08:31 UTC, and
32 (27 in A, 5 in B) at 08:49 after #12 deployed. Of the 32, 11 are real and 21 are the
script's own faults (§11, "What changed"). **Revision 5's script: 11 `FAIL` lines** (§10 P0).

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
| R3 P0 #3 | Hero is the upstream screenshot `/assets/main-window.webp` (34 KB, 1280x774) with a receipt; "Starting Soon" and "Rust has passed C" are on no page | #6, #8 |
| R3 P0 #2: agent router | `## Router` heads `llms.txt` and `/ai/`: 12 rows, 12 of 12 printed sizes equal the bytes served. `/ai/manifest.json` lists 106 documents; every tenth (11) matches its SHA-256. `site-download.md`, `site-control.md` and `site-examples.md` are 200 `text/markdown` and are in `llms-ctx.txt` (229,621 B) | #9 |
| R4 P0 #5: stable and beta | `#stable` offers `obs-studio-rust-v1.0.0` (2026-11-01, 7 files) and `#beta` offers `v1.0.1-beta.20261108` (9 files). 16 of 16 hashes equal the line in that release's own `SHA256SUMS`, on `/` and in `site-download.md`. Each OS card has its verify command. All 16 links and hashes are present with JS off | #11 |
| R4 P0 #8: "What to expect" | Six limits beside the download (SmartScreen, notarization, Flatpak updates, tested distributions, one-time import, capture permissions). Each links `blob/<40 hex>/README.md#L<n>` (lines 114, 97, 83, 74, 67, 68). The cited lines share 3 to 13 distinctive words with their sentence; lines 200 further down share 0 or 1. The build fails when a README pattern is gone | #11 |
| R4 P0 #17a: nothing broken | At 390 and 1440 px on all five pages and `/nope`, and at 320 px on `/`: no sideways scroll, no text under 12 px, no control under 24 px, no nav link off screen. `site.css` has a `:focus-visible` ring | #12 |
| R4 P0 #2 (part), #15a: chunk URLs, search | All 1720 chunk `url`s are absolute (an `obs-rust.com` anchor, or the GitHub permalink or PR); every ninth distinct one is 200. On `/ai/`, "install on windows" returns the Windows download first (a CI note at 08:50); `SetInputSettings` and `wait_for` return their typed chunk first | #13 |

## 3. Critique of the live site

**A streamer on `/`**

1. **A stable release exists and the first screen still sells a beta.** The eyebrow reads
   "public beta" and the one action reads "Download beta ↓"; it lands on a section whose first,
   recommended channel is Stable v1.0.0. `llms.txt` says "It ships beta builds" and "Latest
   release: obs-studio-rust-v1.0.1-beta.20261108", and its router row is "Install the beta".
2. **The app is too small to read, and on a phone it is below the first screen.** At 1440x900
   the 1280 px screenshot renders 497 px wide beside a three-line slogan. At 390x844 it starts
   below the fold (the largest image on the first screen is the 34 px logo), ending at 1.31
   viewport heights.
3. **Absolutes without a receipt.** "Nothing you rely on breaks"; "four tiers of tests keep
   the two identical"; on `/websocket/`, "every client written for OBS 28+ works against it";
   on `/examples/`, "Every v5 client works". The limits six lines below now have receipts.
4. **A receipt nobody can check.** The 60.4% figure links `blob/leaderboard/conversion.json`,
   a branch whose file changes within minutes of a build. The same block shows a language
   bar and "Whole app 17.0%": three denominators (P1).
5. **Long way down, wrong emphasis** (P1). Downloads start 2.3 viewports down on desktop and
   3.9 on a phone, in eight sections. The ledger preview leads with three MCP entries while
   386 fixed upstream bugs stay a number. `claude --dangerously-skip-permissions` has no
   caution mark. `og:image` is a 768 KB square PNG; a 643 KB logo is deployed and unused.

**A plugin or tool builder**

6. **The "which API" answer is wrong.** `site-control.md` says "Both run locally", but a
   WebSocket client can sit on another machine. Neither it nor `/mcp/index.md` says the MCP
   server builds and runs only on Linux; the `/mcp/` page does. `/` shows two unrelated cards.
7. **`/websocket/` is one 316 KB page** with no text twin per request, and the examples are
   typed into `src/examples.html`, not files (P1). Their ten request and event names exist in
   `protocol.json` and the 20 GitHub links on `/examples/` resolve; §11 A6 now checks both.

**An AI agent**

8. **Noise in the core tier.** 16 chunks hold raw `<img` or shields.io markup; `readme#top`,
   the first chunk an agent meets, is badge HTML.
9. **Search is heavy** (P1): the first keystroke downloads 621 KB gzipped.
10. **The gate lags the bar**: `check.py` has no phrase, search or first-screen check (P1 #6).

## 4. Principles and constraints

1. **Receipts, visibly.** Every figure is computed at build time and shows its source, commit
   and date, linked at a commit and never at a branch. No receipt, no number.
2. **The project's own measures only**: `conversion.json`, the features ledger, the releases
   API, `protocol.json`, `control-api.schema.json`, the README.
3. **Show the thing, say what does not work.** The real application and release assets, and
   their limits beside the pitch, quoted from upstream files.
4. **Fail closed.** If a source cannot be fetched or parsed the build fails; stale beats wrong.
5. **Text first; static, first-party, small.** Every page an agent may need has a markdown
   twin. No framework or third-party origin; assets are self-hosted; JS only enhances.

Constraints from the maintainer; a change that breaks one is not done:

- **Python runs only through `uv run`.** Every Python change keeps strict typing: pydantic
  models or frozen dataclasses for all data, no duck-typed dicts, and `basedpyright` strict
  clean (the `pages.yml` step). A new input gets a model in `tools/models.py`.
- One generator (`tools/build.py`, `corpus.py`, `mcp.py`, `sitedocs.py`), one gate
  (`tools/check.py`), the existing `pages.yml`. No new workflow file. Assets are self-hosted.
  Each backlog item lands with its check in `check.py`, so what §11 measures on the live
  site was already measured on `_site/`.

## 5. Information architecture

Nav on every viewport, all links visible without scrolling at 320 px: **Download · WebSocket
API · MCP · Examples · For AI**, then GitHub. Five pages and the 404 are enough for an LGTM;
the pages marked P1 are depth.

```
/             Hero (screenshot, headline figure, one action that names the stable release),
              proof strip, download with its limits, what changed, build with it
              (WebSocket-or-MCP table, examples, AI, contribute)
/websocket/   Reference and live console        /mcp/   Server reference, /mcp/index.md
/examples/    Checked snippets and links out    /404.html   Mascot and the nav links
/ai/          Router, feeds, search (`/ai/#q=<query>` runs a search; results render in `#hits`);
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
| `--haz` | `#f2b705` | caution only: beta, unsigned, untested, destructive; the focus ring |
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
   wider on desktop, 330 px or wider and whole within the first screen on a phone. Tally unlit.
2. **The receipt.** One component, `.receipt`, patina-green mono under every computed number
   and every limit, its link a 40-hex permalink. It is the proof mark.
3. **The headline figure.** One per view: libobs lines ported. Other denominators are
   labelled rows beneath it, or leave the page.
4. **The tally light.** Lit red only for live state: the WebSocket console connection.

The bronze robot (one file under 60 KB) appears on `/ai/`, `/mcp/`, the 404 page and the social
card. Motion: CSS only, off under `prefers-reduced-motion`.

## 7. Content and corpus

Voice: plain, specific, verifiable; no superlatives, no absolutes ("every", "nothing",
"identical"). A promise or a limit is a **claim** and ships in one of two forms. Either a
sentence with a line receipt, as PR #11 built for limits: a typed `Limit` in `build.py` whose
pattern must still match the upstream file, rendered with a `blob/<commit>/<file>#L<n>` link.
Or a sentence reworded until it says only what the project measures ("the unmodified
obs-websocket plugin ships as the compatibility check", not "every client works").
Revision 4's `claims.toml` and `/ai/claims.json` are dropped: the line receipt does that job.

- **Streamers.** The first screen names the newest stable release. Download: both channels,
  visitor's OS first, each file with size, SHA-256 and the verify command; beside it the
  limits and how to go back. The ledger preview leads with fixed bugs.
- **Builders.** One computed table on `/` and in `site-control.md` (transport, where it runs
  and from where it is reachable, operations, auth, platforms, waits). Examples name only
  requests, events and tools that exist, and link only to pages that resolve.
- **Agents.** The router (task, one file, exact bytes) heads `llms.txt` and `/ai/`.

**Tiers**, by rule in `build.py`: `core` (README without badges or the hall of fame, AGENTS,
CONTRIBUTING, SECURITY, CODESTYLE, CONSTITUTION, ledger summary, `site/*.md`, MCP and
WebSocket narrative) fills `llms-ctx.txt`; then `reference`, `process`, `archive`.

**Chunks.** Split on headings; each opens with its breadcrumb; HTML and badge markup are
stripped. Prose is at most 2400 characters, never split inside a fence or table. Typed chunks
are one unit each: `ws-request`, `ws-event`, `ws-enum`, `mcp-tool`, `mcp-resource`,
`ledger-entry`, `ledger-fix`, later `c-symbol`. Every `url` is absolute and resolves. Fields:
`id` (structural: `<doc>#<heading-path>`, `ws:<kind>:<Name>`, `mcp:tool:<name>`), `doc`,
`group`, `tier`, `kind`, `breadcrumb`, `url`, `source` (permalink), `text`, `chars`,
`tokens_est`, `sha256`.

**Search** on `/ai/` is lexical and client-side. Rank by term frequency, then boost a match
in the title or breadcrumb, an exact `id`, and the `core` tier over `process` and `archive`,
so a plain question lands on the site's own documents. Embedding search stays rejected.

**Feeds.** `llms.txt`: 80 links and 25 KB at most, each `[title](url): first sentence`, its
summary naming the newest stable release and beta; `llms-ctx.txt` under 300 KB. Markdown
opens with front matter. `manifest.json` gives each document's bytes and SHA-256.

## 8. Budgets and accessibility

Checked by `tools/check.py` on `_site/`; the first three rows and the last also by §11 on the
live site. Live values in brackets.

| Budget | Limit |
|---|---|
| Third-party origins requested by any page | 0 [0] |
| `/` HTML + CSS, gzipped | 40 KB [13.1 KB] |
| `/websocket/` HTML, gzipped | 60 KB [35.5 KB] |
| `/mcp/`, `/ai/` HTML, gzipped | 20, 30 KB [13.3, 7.9 KB] |
| First search on `/ai/`, gzipped (P1) | 150 KB [621 KB] |
| Fonts, all files; largest image on `/` | 160 KB [157.7 KB]; 120 KB [34 KB] |
| Social card (P1) | 1200x630 PNG under 200 KB [768 KB square]; unreferenced assets 0 [1, 643 KB] |
| `llms.txt` / `llms-ctx.txt` | 80 links, 25 KB [40, 16.5 KB] / 300 KB [229.6 KB] |

Accessibility is WCAG 2.2 AA. §11 B probes what a visitor meets: no sideways scroll at 320,
390 and 1440 px, no text under 12 px, controls 24x24 px or larger, no nav link off screen, a
`:focus-visible` ring, downloads and reference complete with JS off. `check.py` keeps the
rest: heading order, image `alt` and size, input labels, a skip link, contrast (body 4.5:1).

## 9. WebSocket reference and console

Sticky index left, reference centre, console docked right (a bottom sheet under 1200 px), so
"Try" never scrolls the reader away. "Try" builds a typed form from `requestFields`; a missing
required field disables Send and says why. The password is never stored.

## 10. Backlog

Numbers are Revision 3's and 4's; a letter marks a split (`5b` is what is left of 5; `15a` shipped in #13). An item
is done when its check passes in `tools/check.py` on `_site/` and in §11 on the live site.

### P0: what stands between the site and an LGTM

The 11 `FAIL` lines of §11 map to these four items, each one focused PR. There is no fifth.

| # | Item | Acceptance check (§11 lines failing today) |
|---|---|---|
| 5b | **Stable first.** The hero eyebrow and action name the newest stable release ("Download v1.0.0"), not "beta"; beta stays a second channel. The `llms.txt` summary and "Latest release" line name the stable tag and the beta; the router row reads "Install and verify the download". | A5: `llms.txt` contains the newest non-prerelease `obs-studio-rust-v*` tag. B "first screen" at 1440 and 390 px: a download link outside the nav is visible on the first screen and its text has no "beta". C1 passes. (1 line, and half of 2) |
| 12 | **App first.** The screenshot leads: h1 at most 72 px on desktop and 40 px on a phone, image before the lede on a phone. | B "first screen": the largest image on the first screen is 640 px or wider at 1440x900 and 330 px or wider at 390x844, and ends inside the first viewport. (the other half of the same 2 lines) |
| 4 | **Promises reworded, figure pinned.** Rewrite the four absolutes of critique 3 per §7. Fetch `conversion.json` at the `leaderboard` commit and link `blob/<40 hex>/conversion.json`. Put a `--haz` caution on the `--dangerously-skip-permissions` block. | A3: none of the six phrases on any page. A6: `/` links `<40 hex>/conversion.json` and shows that file's `libobs.all.percent` to one decimal. D2 and D4 pass. (5 lines) |
| 2 | **Close the agent path.** Badge and HTML markup stripped from chunk text; "Linux" in the first 1500 characters of `/mcp/index.md` and in `site-control.md`, which also says a WebSocket client may be remote and the MCP server is local. | A7: no `<img`, `<p align` or shields.io in chunk text; "Linux" in both MCP texts; every chunk `url` stays absolute and every ninth distinct one is 200. C2 passes. (3 lines) |

### P1: the pages that make the case

| # | Item | Acceptance check |
|---|---|---|
| 6 | **Gate v2**: every §11 check in `check.py` on `_site/` (the probe runs on local files); a post-deploy step in the existing job runs §11 A1. | `check.py` exits non-zero for each of: a table wider than its page, 11 px text, a relative chunk `url`, a banned phrase, a limit whose pattern is gone; the deploy job fails if `/llms.txt` is not 200 `text/plain` or `/nope` is not 404. |
| 12b, 4b | **Home, shorter and in order**: sections of §5; one headline figure; proof strip of four receipts without "Forks"; ledger preview leads with fixed bugs; a copy control per hash; the WebSocket-or-MCP table. | At 1440x900 the first release link starts within 2.0 viewports, at 390x844 within 3.0; one figure carries the hero numeral style; "N requests", "N events" and "N typed tools" equal `protocol.json` and `mcp/schema.json`. |
| 7 | **Social card and asset hygiene.** Generated 1200x630 card; delete the unused logo; mascot on the 404 page. | `og:image` on every page is a 1200x630 PNG under 200 KB; no file in `_site/assets/` is unreferenced; `/404.html` has the mascot with `alt`, `width` and `height`. |
| 2b, 1 | **Corpus residue**: prose `url` ends in its heading's `#anchor`; no prose chunk under 300 characters; hall of fame out of `core`; `c-symbol` chunks; deterministic output. | No prose `url` without `#`; one `c-symbol` chunk per Sphinx directive; two builds from the same inputs give a byte-identical `corpus.json` apart from the timestamp. |
| 15 | **Search index and retrieval eval**: `/ai/search.json`, `tools/eval_corpus.py`, an `aria-live` result count. | First search transfers under 150 KB gzipped; 90% of 30 or more checked-in questions have the expected chunk in the top 5. |
| 11 | **Markdown twins and sitemap**: `index.md` per page, `rel="alternate"`, JSON-LD on `/`, every document in `sitemap.xml`. | Every HTML page's alternate link resolves; JSON-LD parses and its version equals the newest stable tag; the sitemap lists as many URLs as the manifest has documents. |
| 18, 13 | **Per-item pages and `.md`** for WebSocket and MCP; `server.json` valid against the vendored schema. | For every name in `protocol.json`, `/websocket/<Name>.md` exists; `/mcp/tools/<name>.md` exists for every tool; `server.json` validates against `tools/vendor/server.schema.json`. |
| 16 | **Examples as files** `examples/<lang>/*`, highlighted at build, served raw, with one MCP agent session. | Every request, event and tool name used exists in `protocol.json` or `mcp/schema.json`; Python examples pass `uv run python -m py_compile`. |
| 9, 10, 14 | **`/changes/`, `/control/`, `/progress/`** from the ledger, the two schemas and `conversion.json`. | Entry and figure counts equal their sources; each page reads complete with JS off; one receipt each. |
| 17b, 19 | **CSS consolidation** (no page `<style>`, two Barlow weights) and **console v2** per §9. | No `<style` in any `_site/**/*.html`; an empty required field blocks Send with a message; `localStorage` never holds the password. |

### P2: depth

20 `/websocket/obs-websocket.d.ts` (`tsc --noEmit` accepts it). 21 `/libobs/` symbol index (every
`c-symbol` id resolves). 22 topic bundles `/ai/bundles/*.txt` (sizes in `llms.txt`). 23 installable
MCP `packages` in `server.json` (URL and hash equal a release asset and its `SHA256SUMS` line).
24 contributor strip (figures equal `leaderboard.json`). 25 `/releases.xml` and a launch-speed
figure (read from JSON, never from prose).

## 11. The done bar

The judge works on the **live site** only; nothing is taken from a build log, a PR or this
document's brackets. Verdict: **LGTM** when the script prints no `FAIL` line, all three trials
in C pass and at most one line of D fails; otherwise **FAIL:** followed by the failed lines.
Budget 10 minutes: the script ran in 1 min 37 s to 2 min 52 s (it is killed, and fails, at 9 min); C's three
trials run in parallel in about five; D takes three. The script needs only `bash`, `curl`, `jq`
and the Chromium at `~/.hermes/tools/chromium-1208/chrome-linux64/chrome`, and samples nothing
at random: two runs against the same deploy print the same lines.

```bash
cd "$(mktemp -d)"   # then extract the two blocks below from this file and run them
awk '/^```html probe/{f="probe.html";next} /^```bash judge/{f="judge.sh";next} /^```$/{f=""} f{print > f}' /path/to/DESIGN.md
timeout 540 bash judge.sh | tee verdict.txt; grep -c '^FAIL' verdict.txt   # 0 is a pass; a timeout is a FAIL
```

```html probe
<!doctype html><meta charset="utf-8"><body><script>
const P=new URLSearchParams(location.search),w=+P.get('w'),h=+P.get('h'),f=document.createElement('iframe');
f.width=w;f.height=h;f.style.border=0;if(P.get('nojs'))f.sandbox='allow-same-origin';
f.src='page.html'+(P.get('q')?'#q='+encodeURIComponent(P.get('q')):'');document.body.append(f);
f.onload=()=>setTimeout(()=>{const d=f.contentDocument,W=f.contentWindow,q=s=>[...d.querySelectorAll(s)],box=e=>e.getBoundingClientRect(),
 vis=e=>box(e).width>0&&box(e).height>0,px=e=>parseFloat(W.getComputedStyle(e).fontSize),bar=e=>e.closest('header,nav,footer'),
 hero=q('img').filter(e=>vis(e)&&box(e).top<h).sort((a,b)=>box(b).width-box(a).width)[0],
 cta=q('a[href*="#download"],a[href*="#stable"],a[href*="/releases/download/"]').filter(e=>vis(e)&&!bar(e)&&box(e).bottom<=h)[0];
const r={w:W.innerWidth,overflow_px:d.documentElement.scrollWidth-W.innerWidth,
 small_text:q('body *').filter(e=>vis(e)&&!e.children.length&&e.textContent.trim()&&px(e)<12).length,
 small_controls:q('button,summary,input,select,header a,nav a').filter(e=>vis(e)&&(box(e).width<24||box(e).height<24)).length,
 nav_clipped:q('header a,nav a').filter(e=>vis(e)&&!e.closest('footer')&&(box(e).right>w+1||box(e).left<-1)).length,
 hero_w:hero?Math.round(box(hero).width):0,hero_bottom_vh:hero?+(box(hero).bottom/h).toFixed(2):9,cta:cta?cta.innerText.trim():'',
 dl_links:q('a[href*="/releases/download/"]').filter(vis).length,hashes:(d.body.innerText.match(/\b[0-9a-f]{64}\b/g)||[]).length,ids:q("[id]").filter(vis).length,
 line_receipts:q('a[href*="/blob/"][href*="#L"]').map(a=>({href:a.href,text:a.parentElement.innerText.replace(/\s+/g,' ')})),
 third_party:W.performance.getEntriesByType('resource').map(e=>e.name).filter(n=>!/^(https:\/\/obs-rust\.com\/|file:)/.test(n))};
document.body.innerHTML='<pre>'+JSON.stringify(r).replace(/</g,'&lt;')+'</pre>'},P.get('q')?6000:2500);
</script>
```

```bash judge
B=https://obs-rust.com; GH=https://github.com/obs-rust/obs-studio; RAW=https://raw.githubusercontent.com/obs-rust/obs-studio
C=~/.hermes/tools/chromium-1208/chrome-linux64/chrome; PAGES="/ /websocket/ /examples/ /ai/ /mcp/"
fail(){ echo "FAIL $*"; }; get(){ curl -s -m 60 --retry 2 --compressed "$B$1"; }; gz(){ curl -s -m 60 -H 'Accept-Encoding: gzip' "$B$1" | wc -c; }
lim(){ [ "$2" -le "$3" ] || fail "$1 = $2 > $3"; }; code(){ curl -s -m 30 --retry 2 -L -o /dev/null -w '%{http_code}' "$1"; }
chrome(){ timeout 60 "$C" --headless=new --incognito --no-sandbox --disable-gpu --allow-file-access-from-files --user-data-dir="$PWD/prof" \
  --window-size=1700,1300 --virtual-time-budget=20000 --dump-dom "$1" 2>/dev/null; }
probe(){ get "$1" | sed "s|<head>|<head><base href=\"$B$1\">|" > page.html   # probe PATH W H [nojs]: layout facts of the live page as JSON
  for try in 1 2; do chrome "file://$PWD/probe.html?w=$2&h=$3&nojs=$4" | grep -o '{"w":.*}' && break; done; }
want(){ r=$(probe $2); [ -n "$r" ] || { fail "B $1: the probe returned nothing"; return; }   # want LABEL "PATH W H [nojs]" JQ-FAULTS
  jq -r --arg l "$1" "[$3]|if length>0 then \"FAIL B \(\$l): \"+join(\"; \") else empty end" <<<"$r"; }
# A1 the site is up, fresh, and serves each format with the right status and type
get /llms.txt > llms.txt; d=$(grep -o 'Generated [0-9-]*' llms.txt | cut -d' ' -f2); [ -n "$d" ] && [ $(( ($(date -u +%s) - $(date -u -d "$d" +%s)) / 86400 )) -le 2 ] || fail "A1 site generated '$d', over 2 days ago"
st(){ c=$1; ty=$2; shift 2; for p; do got=$(curl -s -m 60 -o /dev/null -w '%{http_code} %{content_type}' "$B$p")
  case "$got" in "$c $ty"*) ;; *) fail "A1 $p -> $got";; esac; done; }
st 200 text/html $PAGES; st 404 text/html /nope; st 200 text/plain /llms.txt /llms-ctx.txt /llms-full.txt
st 200 application/json /ai/corpus.json /ai/manifest.json /mcp/schema.json /websocket/protocol.json
st 200 text/markdown /mcp/index.md /ai/docs/site-download.md /ai/docs/site-control.md /ai/docs/site-examples.md
# A2 weight: a phone on a slow link, and an agent with one context window
lim "A2 / html+css gzipped" $(( $(gz /) + $(gz /assets/site.css) + $(gz /assets/fonts.css) )) 40000
lim "A2 /websocket/ html gzipped" "$(gz /websocket/)" 60000; lim "A2 llms.txt bytes" "$(wc -c < llms.txt)" 25000; lim "A2 llms-ctx.txt bytes" "$(get /llms-ctx.txt | wc -c)" 300000
# A3 no retired or absolute promise is back
BAN='rust has passed c|starting soon|nothing you rely on|keep the two identical|every client written|every v5 client works'; for p in $PAGES /nope; do get $p | grep -oiE "$BAN" | sort -u | sed "s|^|FAIL A3 $p says: |"; done
# A4 limits: three or more on /, each with a commit-pinned line receipt whose lines say the same thing
probe / 1440 900 > home.json
[ "$(jq '.line_receipts|length' home.json 2>/dev/null || echo 0)" -ge 3 ] || fail "A4 / shows under 3 limits with a line receipt"
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
[ -n "$stable" ] || fail "A5 cannot read a stable release from the GitHub API (if rate limited, set GITHUB_TOKEN)"
for tag in $stable $beta; do curl -sL -m 60 "$GH/releases/download/$tag/SHA256SUMS" > "sums.$tag"
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
for u in $(get /examples/ | grep -oE 'href="https://github\.com/[^"#]+' | cut -d'"' -f2 | sort -u); do [ "$(code "$u")" = 200 ] || fail "A6 dead link on /examples/: $u"; done
# A7 agent path: router sizes, manifest hashes, chunk urls, MCP platform
rt=$(sed -n '/^## Router/,/^## Feeds/p' llms.txt | grep -o '(https://[^)]*) ([0-9]* bytes)' | tr -d '()'); [ "$(grep -c bytes <<<"$rt")" -ge 8 ] || fail "A7 the router in llms.txt has under 8 rows"
while read -r u b _; do [ -z "$u" ] || [ "$(curl -s -m 60 --compressed "$u" | wc -c)" = "$b" ] || fail "A7 router size is wrong: $u"; done <<<"$rt"
get /ai/manifest.json > man.json; jq -r '.docs|to_entries[]|select(.key%10==0).value|"\(.sha256) \(.url)"' man.json | while read -r h u; do
  [ "$(curl -s -m 60 "$u" | sha256sum | cut -d' ' -f1)" = "$h" ] || fail "A7 manifest sha256 is wrong: $u"; done; get /ai/corpus.json > c.json
jq -r '([.chunks[]|select(.url|startswith("https://")|not)]|length) as $rel | ([.chunks[]|select(.text|test("<img |<p align|shields\\.io"))]|length) as $raw
  | (select($rel>0)|"\($rel) chunk urls are not absolute"), (select($raw>0)|"\($raw) chunks hold raw HTML or badge markup") | "FAIL A7 corpus: "+.' c.json
for u in $(jq -r '.chunks[].url|split("#")[0]' c.json | sort -u | awk 'NR%9==1'); do case $u in /*) u=$B$u;; esac; [ "$(code "$u")" = 200 ] || fail "A7 chunk url is dead: $u"; done
for id in ws:request:SetInputSettings mcp:tool:wait_for; do jq -e --arg i "$id" '[.chunks[]|select(.id==$i)]|length==1' c.json >/dev/null || fail "A7 no chunk $id"; done
get /mcp/index.md | head -c 1500 | grep -qi linux || fail "A7 /mcp/index.md does not name its platform in the first 1500 characters"
grep -qi linux ctl.md || fail "A7 site-control.md does not name the MCP platform"
# A8 search on /ai/: a plain question and two exact names each find their document first
while read -r q ok; do h=$(chrome "$B/ai/#q=$q" | sed -n '/id="hits"/,$p' | grep -o '<a href="[^"]*"' | grep -v github.com | head -1)
  grep -qE "$ok" <<<"$h" || fail "A8 search '$q': first hit is ${h:-nothing}, want $ok"; done <<'Q'
install%20on%20windows site-download|readme|obs-rust\.com/#
SetInputSettings /websocket/#SetInputSettings
wait_for /mcp/#wait_for
Q
# B what a visitor sees, from headless Chromium: probe.html reads the fetched live page in a same-origin frame
ALL='(select(.overflow_px>0)|"scrolls sideways by \(.overflow_px) px"),(select(.small_text>0)|"\(.small_text) texts under 12 px"),(select(.small_controls>0)|"\(.small_controls) controls under 24 px"),(select(.nav_clipped>0)|"\(.nav_clipped) nav links off screen"),(select(.third_party|length>0)|"third-party request to \(.third_party[0])")'
for p in $PAGES /nope; do for s in "390 844" "1440 900"; do want "$p at ${s% *} px" "$p $s" "$ALL"; done; done; want "/ at 320 px" "/ 320 640" "$ALL"
HERO='(select(.hero_w<MINW or .hero_bottom_vh>1)|"largest image on the first screen is \(.hero_w) px wide, ending at \(.hero_bottom_vh) screens"),(select(.cta=="" or (.cta|test("beta";"i")))|"first-screen download action reads: \(.cta)")'
want "/ first screen at 1440 px" "/ 1440 900" "${HERO/MINW/640}"; want "/ first screen at 390 px" "/ 390 844" "${HERO/MINW/330}"
want "/ with JS off" "/ 1440 900 1" '(select(.dl_links<6 or .hashes<6)|"\(.dl_links) download links and \(.hashes) SHA-256 on the page")'
want "/websocket/ with JS off" "/websocket/ 1440 900 1" "(select(.ids<$(jq '(.requests|length)+(.events|length)' p.json))|\"only \(.ids) anchored entries are visible\")"
get /assets/site.css | grep -q ':focus-visible' || fail "B site.css has no :focus-visible ring"
```

**What changed from Revision 4's script.** *Slow and flaky:* a fresh Chromium profile hung
until its timeout on first launch (the second run took 2 min 42 s) and a reused one served
`site.css` from before a deploy, so Chromium now runs `--incognito`, 3 to 4 s per page; `shuf`
samples became every tenth manifest document and every ninth chunk URL; the Actions API check
is gone and the remaining API call accepts `GITHUB_TOKEN`; `perl` is gone (JS-off is a
sandboxed frame). *Wrong:* relative chunk URLs went to curl as they were, 12 "dead" lines for
one fault; `nothing you rely on breaks` never matched, because the page splits it with `<em>`;
`every client` matched an instruction on `/mcp/`; `claims.json` (2 lines) tested a mechanism
#11 replaced with line receipts, which A4 now tests. *Pedantic, moved to `check.py` or P1:*
heading order, `h1` count, image `width`/`height`, font and hero bytes, the section count,
class-name hooks (`.headline`, `.receipt`, `.sha`, `[data-os]`, `article`), prose chunk size
and anchors, the sitemap count, "Forks". *Added, because someone would notice:* A4 receipts
support their sentence; A5 `llms.txt` names the stable release; A6 links on `/examples/`
resolve; A8 search; the first-screen download action. A `FAIL` line now names its fault.

**C. Cold trials.** Each is one fresh sub-agent with a fetch tool, no repository and no prior
context, three fetches per question; the judge checks the answer against the named source.

1. **Streamer**, from `/`: the Windows x64 file of the newest stable release with its SHA-256,
   and one thing to expect or that does not work yet. Pass: the hash equals the line in
   `sums.<stable tag>`; the limit is one of the receipted sentences in `home.json`.
2. **Builder**, from `/`: which surface for "a button on another PC that switches scene"
   (WebSocket) and for "an agent on the OBS machine that waits until recording is active"
   (MCP), `SetCurrentProgramScene`'s fields, `wait_for`'s arguments, and where the MCP server
   runs. Pass: both choices right, fields equal `p.json` and `m.json`, the platform is Linux.
3. **Agent**, from `/llms.txt`: the Linux AppImage of the newest stable release with its
   SHA-256; `SetInputSettings`'s request fields; an MCP client config and a three-call
   session; how to claim an issue; the percent of libobs ported and its commit. Pass: four of
   five correct, each citing a fetched URL whose body contains the fact.

**D. Judgement** (two or more failures is FAIL; the judge quotes the element it faults)

1. On the first screen, `/` could not be mistaken for a template: the real application
   readable, one headline figure with its receipt, one primary action.
2. Of ten sentences sampled across the five pages, none is a superlative, or an absolute
   promise without a receipt beside it.
3. Limits are as easy to find as the pitch: on the page, next to the download they limit.
4. Colour carries only the meanings of §6: hazard marks real cautions (beta, unsigned, the
   permission-skipping prompt); the tally is unlit unless the console is connected.

## 12. Non-goals

No framework, bundler, analytics, cookie banner or third-party embed. No server-side search,
hosted MCP endpoint or embedding service. No hand-edited copy of upstream docs. No blog, no
light theme, no new workflow files. No claim the build cannot check.
