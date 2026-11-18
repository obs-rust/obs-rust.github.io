#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Build obs-rust.com into _site/.

Usage: uv run tools/build.py --obs-studio PATH [--out _site] [--offline]

Inputs (see DESIGN.md §5):
  * src/*.html           hand-authored page templates ({{placeholders}})
  * assets/              copied verbatim
  * PATH (obs-studio)    README + docs/ for the corpus and features ledger;
                         its obs-websocket submodule SHA pins protocol.json
  * GitHub API           language bytes, stars, latest release (GITHUB_TOKEN optional)
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://obs-rust.com"
REPO = "obs-rust/obs-studio"
WS_REPO = "obs-rust/obs-websocket"
esc = html.escape


# ---------------------------------------------------------------- fetching
def fetch(url: str, accept: str = "application/vnd.github+json") -> bytes:
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "obs-rust-site-build"})
    tok = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()


def gh(path: str):
    return json.loads(fetch(f"https://api.github.com/{path}"))


def cached(name: str, offline: bool, producer):
    """Return producer() and cache it; offline falls back to the cache."""
    cache = ROOT / ".cache" / name
    if not offline:
        try:
            data = producer()
            cache.parent.mkdir(exist_ok=True)
            cache.write_bytes(data if isinstance(data, bytes) else json.dumps(data).encode())
            return data
        except Exception as e:  # noqa: BLE001 - network is best effort
            print(f"warn: {name}: {e}; using cache", file=sys.stderr)
    if cache.exists():
        raw = cache.read_bytes()
        return raw if name.endswith((".md", ".json.raw")) else json.loads(raw)
    raise SystemExit(f"no data for {name} (offline and no cache)")


# ---------------------------------------------------------------- stats
def repo_stats(offline: bool) -> dict:
    langs = cached("languages.json", offline, lambda: gh(f"repos/{REPO}/languages"))
    repo = cached("repo.json", offline, lambda: gh(f"repos/{REPO}"))
    rels = cached("releases.json", offline, lambda: gh(f"repos/{REPO}/releases?per_page=20"))
    total = sum(langs.values()) or 1
    pct = lambda k: round(100 * langs.get(k, 0) / total, 1)  # noqa: E731
    r, c, x = pct("Rust"), pct("C"), pct("C++")
    rel = next((x for x in rels if x["tag_name"].startswith("obs-studio-rust-v")), rels[0] if rels else None)
    return {
        "rust_pct": r, "c_pct": c, "cpp_pct": x, "other_pct": round(max(0.0, 100 - r - c - x), 1),
        "rust_mb": f"{langs.get('Rust', 0) / 1e6:.1f}", "c_mb": f"{langs.get('C', 0) / 1e6:.1f}",
        "cpp_mb": f"{langs.get('C++', 0) / 1e6:.1f}",
        "xo_title": "Rust has passed <em>C</em>" if r > c else "Rust is closing on <em>C</em>",
        "stars": repo.get("stargazers_count", 0), "forks": repo.get("forks_count", 0),
        "release": rel,
    }


def human_size(n: int) -> str:
    return f"{n / 1e6:.0f} MB" if n >= 1e6 else f"{n / 1e3:.0f} KB"


DL_GROUPS = [
    ("Windows", "x64 · arm64", [("-windows-x64.msi", "Installer · x64"), ("-windows-arm64.msi", "Installer · arm64"),
                                ("-windows-x64.zip", "Portable · x64"), ("-windows-arm64.zip", "Portable · arm64")]),
    ("macOS", "Apple silicon · Intel", [("-macos-arm64.dmg", "Apple silicon"), ("-macos-x86_64.dmg", "Intel")]),
    ("Linux", "x86_64", [(".AppImage", "AppImage · any distro"), ("-ubuntu-26.04-x86_64.deb", ".deb · Ubuntu 26.04"),
                         (".flatpak", "Flatpak bundle")]),
]


def render_downloads(rel: dict | None) -> str:
    if not rel:
        return '<p>No release found. See <a href="https://github.com/obs-rust/obs-studio/releases">releases</a>.</p>'
    assets = rel.get("assets", [])
    out = []
    for os_name, arch, wants in DL_GROUPS:
        items = []
        for suffix, label in wants:
            a = next((a for a in assets if a["name"].endswith(suffix)), None)
            if a:
                items.append(f'<li><a href="{esc(a["browser_download_url"])}">{esc(label)}'
                             f'<span>{human_size(a["size"])}</span></a></li>')
        if not items:
            items.append(f'<li><a href="{esc(rel["html_url"])}">See release<span>→</span></a></li>')
        out.append(f'<div class="plate card" data-os="{os_name.lower()}"><span class="tag">{esc(arch)}</span>'
                   f'<div class="os">{os_name}</div><ul>{"".join(items)}</ul></div>')
    return "".join(out)


# ---------------------------------------------------------------- features ledger
MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def md_inline(s: str) -> str:
    s = esc(MD_LINK.sub(r"\1", s))
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"\*\*([^*]+)\*\*", r"\1", s)


def parse_ledger(text: str) -> dict:
    items, cur, section, area = [], None, "", ""
    for line in text.splitlines():
        if line.startswith("## "):
            section, area = line[3:].strip(), ""
        elif line.startswith("### "):
            area = line[4:].strip()
        if line.startswith("- "):
            cur = {"section": section, "area": area, "text": line[2:].strip()}
            items.append(cur)
        elif cur and line.startswith("  ") and line.strip():
            cur["text"] += " " + line.strip()
        elif not line.strip() or line.startswith("#"):
            cur = None
    feats = [i for i in items if i["section"] == "Features" and i["text"].startswith("**")]
    fixed = [i for i in items if i["section"] == "Fixed upstream bugs"]
    for f in feats:
        m = re.match(r"\*\*(.+?)\*\*\s*(.*)", f["text"])
        f["name"], rest = (m.group(1), m.group(2)) if m else (f["text"], "")
        d = re.search(r"\*([A-Za-z, ]+)\*,\s*(\d{4}-\d{2}-\d{2})", rest)
        f["platforms"], f["date"] = (d.group(1), d.group(2)) if d else ("", "")
        f["desc"] = re.split(r"\s\*[A-Za-z, ]+\*,\s*\d{4}", rest)[0].strip()
        f["pr"] = (re.findall(r"\[#(\d+)\]\(https://github.com/obs-rust/obs-studio/pull/\d+\)", rest) or [""])[0]
    return {"features": feats, "fixed": fixed}


def render_feature_cards(feats: list[dict], n: int = 9) -> str:
    out = []
    for f in sorted(feats, key=lambda f: f["date"], reverse=True)[:n]:
        name = md_inline(f["name"].rstrip("."))
        desc = md_inline(f["desc"])
        if len(desc) > 220:
            desc = desc[:217].rsplit(" ", 1)[0] + "…"
        href = f'https://github.com/obs-rust/obs-studio/pull/{f["pr"]}' if f["pr"] else \
            "https://github.com/obs-rust/obs-studio/blob/master/docs/features.md"
        out.append(f'<a class="plate card" href="{href}"><h3>{name}</h3><p>{desc}</p>'
                   f'<div class="m"><span class="tag rust">{esc(f["area"])}</span>'
                   f'<span class="tag">{esc(f["platforms"])}</span><span>{esc(f["date"])}</span></div></a>')
    return "".join(out)


# ---------------------------------------------------------------- corpus
CORPUS_ROOT_FILES = ["README.md", "AGENTS.md", "BUILD.md", "CONTRIBUTING.md", "SECURITY.md"]


def corpus_sources(obs: Path) -> list[tuple[str, str, Path]]:
    """(group, repo-relative path, absolute path) in corpus order."""
    out = [("project", f, obs / f) for f in CORPUS_ROOT_FILES if (obs / f).exists()]
    for group, pattern in [("docs", "docs/*.md"), ("rust-port", "docs/rust-port/*.md"),
                           ("knowledge", "docs/knowledge/*.md"), ("libobs-api", "docs/sphinx/*.rst")]:
        for p in sorted(obs.glob(pattern)):
            out.append((group, str(p.relative_to(obs)), p))
    return out


def rst_to_md(t: str) -> str:
    """Light RST→markdown: headings, code directives, roles. Good enough for LLM reading."""
    lines, out = t.splitlines(), []
    marks = {"=": "#", "-": "##", "^": "###", '"': "####", "~": "###", "*": "#"}
    i = 0
    while i < len(lines):
        ln = lines[i]
        nxt = lines[i + 1] if i + 1 < len(lines) else ""
        if ln.strip() and nxt and len(set(nxt.strip())) == 1 and nxt.strip()[0] in marks \
                and len(nxt.strip()) >= len(ln.strip()) and not ln.startswith(" "):
            out.append(f"{marks[nxt.strip()[0]]} {ln.strip()}")
            i += 2
            continue
        if len(set(ln.strip())) == 1 and ln.strip()[:1] in marks and len(ln.strip()) > 3:
            i += 1
            continue
        ln = re.sub(r":(?:c:)?(?:func|type|member|macro|data|var|struct|enum|ref|doc):`~?([^`<]+?)(?:\s*<[^>]+>)?`", r"`\1`", ln)
        ln = re.sub(r"``([^`]+)``", r"`\1`", ln)
        m = re.match(r"\.\. (?:c:)?(function|type|member|macro|var|struct|enum|enumerator)::\s*(.+)", ln)
        if m:
            out.append(f"\n`{m.group(2).strip()}`")
            i += 1
            continue
        out.append(ln)
        i += 1
    return "\n".join(out)


def first_heading(text: str, fallback: str) -> str:
    m = re.search(r"^#{1,3}\s+(.+)$", text, re.M)
    return re.sub(r"[`*]", "", m.group(1)).strip() if m else fallback


def chunk(text: str, limit: int = 1600) -> list[tuple[str, str]]:
    """Split on headings, then pack paragraphs to ~limit chars. Returns (heading, text)."""
    sections, head, buf = [], "", []
    in_code = False
    for line in text.splitlines():
        if line.startswith("```"):
            in_code = not in_code
        if not in_code and re.match(r"^#{1,4}\s", line):
            if "".join(buf).strip():
                sections.append((head, "\n".join(buf).strip()))
            head, buf = line.lstrip("#").strip(), [line]
        else:
            buf.append(line)
    if "".join(buf).strip():
        sections.append((head, "\n".join(buf).strip()))
    out = []
    for h, body in sections:
        if len(body) <= limit:
            out.append((h, body))
            continue
        cur = ""
        for para in re.split(r"\n\s*\n", body):
            if cur and len(cur) + len(para) > limit:
                out.append((h, cur.strip()))
                cur = ""
            cur += para + "\n\n"
        if cur.strip():
            out.append((h, cur.strip()))
    return out


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


# ---------------------------------------------------------------- websocket protocol
def protocol_md_reference(p: dict) -> str:
    """Render protocol.json as compact markdown for the corpus."""
    out = ["# obs-websocket v5 protocol reference (generated)", ""]
    out.append("## Enums")
    for e in p["enums"]:
        out.append(f"### {e['enumType']}")
        for i in e["enumIdentifiers"]:
            out.append(f"- `{i['enumIdentifier']}` = `{i['enumValue']}`: {i['description']}")
        out.append("")
    out.append("## Requests")
    for r in p["requests"]:
        out.append(f"### {r['requestType']}")
        out.append(f"Category: {r['category']}. Since {r['initialVersion']}. Complexity {r['complexity']}/5."
                   + (" DEPRECATED." if r["deprecated"] else ""))
        out.append(r["description"])
        if r["requestFields"]:
            out.append("Request fields:")
            for f in r["requestFields"]:
                opt = " (optional" + (f", default {f['valueOptionalBehavior']}" if f.get("valueOptionalBehavior") else "") + ")" \
                    if f.get("valueOptional") else ""
                rest = f" restrictions: {f['valueRestrictions']}" if f.get("valueRestrictions") else ""
                out.append(f"- `{f['valueName']}` {f['valueType']}{opt}{rest}: {f['valueDescription']}")
        if r["responseFields"]:
            out.append("Response fields:")
            for f in r["responseFields"]:
                out.append(f"- `{f['valueName']}` {f['valueType']}: {f['valueDescription']}")
        out.append("")
    out.append("## Events")
    for e in p["events"]:
        out.append(f"### {e['eventType']}")
        out.append(f"Category: {e['category']}. Subscription: {e['eventSubscription']}. Since {e['initialVersion']}.")
        out.append(e["description"])
        for f in e["dataFields"]:
            out.append(f"- `{f['valueName']}` {f['valueType']}: {f['valueDescription']}")
        out.append("")
    return "\n".join(out)


def md_desc(s: str) -> str:
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s.replace("\n", "<br>")


def fields_table(fields: list[dict], kind: str) -> str:
    if not fields:
        return ""
    rows = []
    for f in fields:
        opt = ""
        if f.get("valueOptional"):
            ob = f.get("valueOptionalBehavior") or ""
            opt = f'<span class="tag haz" title="{esc(ob)}">optional</span>'
        restr = f'<div class="restr">{esc(f["valueRestrictions"])}</div>' if f.get("valueRestrictions") else ""
        rows.append(f'<tr><td><code>{esc(f["valueName"])}</code>{opt}</td><td class="ty">{esc(f["valueType"])}</td>'
                    f'<td>{md_desc(f["valueDescription"])}{restr}</td></tr>')
    return f'<h4>{kind}</h4><table class="ft"><tbody>{"".join(rows)}</tbody></table>'


def example_request_data(r: dict) -> dict:
    ex = {}
    for f in r["requestFields"]:
        if f.get("valueOptional"):
            continue
        t = f["valueType"]
        ex[f["valueName"]] = {"String": "", "Number": 0, "Boolean": True, "Object": {}}.get(t, [] if t.startswith("Array") else None)
    return ex


def render_ws_items(p: dict) -> tuple[str, str]:
    cats = sorted({r["category"] for r in p["requests"]} | {e["category"] for e in p["events"]})
    items = []
    for r in p["requests"]:
        rid = r["requestType"]
        ex = json.dumps({"op": 6, "d": {"requestType": rid, "requestId": "1",
                                       **({"requestData": example_request_data(r)} if r["requestFields"] else {})}}, indent=2)
        items.append(
            f'<article class="it" id="{rid}" data-kind="request" data-cat="{esc(r["category"])}" data-search="{esc((rid + " " + r["description"]).lower())}">'
            f'<header><a class="nm" href="#{rid}">{rid}</a><span class="tag cu">request</span>'
            f'<span class="tag">{esc(r["category"])}</span><span class="tag">v{esc(r["initialVersion"])}</span>'
            f'{"<span class=\"tag haz\">deprecated</span>" if r["deprecated"] else ""}'
            f'<span class="cx" title="complexity">{"●" * r["complexity"]}{"○" * (5 - r["complexity"])}</span>'
            f'<button class="try" data-req="{rid}" title="Load into the live console">Try ▸</button></header>'
            f'<p>{md_desc(r["description"])}</p>'
            f'{fields_table(r["requestFields"], "Request fields")}{fields_table(r["responseFields"], "Response fields")}'
            f'<details><summary>Example message</summary><pre>{esc(ex)}</pre></details></article>')
    for e in p["events"]:
        eid = e["eventType"]
        items.append(
            f'<article class="it" id="{eid}" data-kind="event" data-cat="{esc(e["category"])}" data-search="{esc((eid + " " + e["description"]).lower())}">'
            f'<header><a class="nm" href="#{eid}">{eid}</a><span class="tag rust">event</span>'
            f'<span class="tag">{esc(e["category"])}</span><span class="tag">{esc(e["eventSubscription"])}</span>'
            f'<span class="tag">v{esc(e["initialVersion"])}</span>'
            f'{"<span class=\"tag haz\">deprecated</span>" if e["deprecated"] else ""}</header>'
            f'<p>{md_desc(e["description"])}</p>{fields_table(e["dataFields"], "Data fields")}</article>')
    for en in p["enums"]:
        nid = en["enumType"]
        rows = "".join(f'<tr><td><code>{esc(i["enumIdentifier"])}</code></td><td class="ty">{esc(str(i["enumValue"]))}</td>'
                       f'<td>{md_desc(i["description"])}</td></tr>' for i in en["enumIdentifiers"])
        items.append(
            f'<article class="it" id="{nid}" data-kind="enum" data-cat="enums" data-search="{esc(nid.lower())}">'
            f'<header><a class="nm" href="#{nid}">{nid}</a><span class="tag haz">enum</span>'
            f'<span class="tag">{len(en["enumIdentifiers"])} values</span></header>'
            f'<table class="ft"><tbody>{rows}</tbody></table></article>')
    nav = []
    for c in cats:
        reqs = [r["requestType"] for r in p["requests"] if r["category"] == c]
        evs = [e["eventType"] for e in p["events"] if e["category"] == c]
        links = "".join(f'<a href="#{n}" data-for="{n}">{n}</a>' for n in reqs) + \
            "".join(f'<a href="#{n}" data-for="{n}" class="ev">{n}</a>' for n in evs)
        nav.append(f'<details open><summary>{esc(c)} <span>{len(reqs) + len(evs)}</span></summary>{links}</details>')
    nav.append('<details open><summary>enums <span>' + str(len(p["enums"])) + '</span></summary>'
               + "".join(f'<a href="#{e["enumType"]}" data-for="{e["enumType"]}">{e["enumType"]}</a>' for e in p["enums"]) + '</details>')
    return "".join(items), "".join(nav)


# ---------------------------------------------------------------- partials
def head(title: str, desc: str, path: str = "/") -> str:
    return f"""<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{SITE}{path}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{SITE}{path}">
<meta property="og:image" content="{SITE}/assets/obs-rust-bot-logo.png">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0b0c0d">
<link rel="icon" href="/assets/obs-rust-badge.svg" type="image/svg+xml">
<link rel="alternate" type="text/plain" title="llms.txt" href="/llms.txt">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Stencil+Display:wght@800;900&family=Barlow+Condensed:wght@500;600;700&family=Barlow:wght@400;500;600&family=JetBrains+Mono:wght@500;600;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="/assets/site.css">"""


NAV_ITEMS = [("home", "/", "Home"), ("download", "/#download", "Download"), ("websocket", "/websocket/", "WebSocket API"),
             ("examples", "/examples/", "Examples"), ("ai", "/ai/", "AI corpus")]


def nav(active: str) -> str:
    lis = "".join(f'<li><a href="{h}"{" aria-current=\"page\"" if k == active else ""}>{t}</a></li>'
                  for k, h, t in NAV_ITEMS if k != "home")
    return f"""<a class="skip" href="#main">Skip to content</a>
<nav class="nav"><div class="wrap">
<a class="brand" href="/"><img src="/assets/obs-rust-badge.svg" alt="" width="34" height="34"><span>OBS <em>Rust</em></span></a>
<ul>{lis}</ul>
<a class="gh" href="https://github.com/obs-rust/obs-studio">GitHub ★ {{{{stars}}}}</a>
</div></nav>"""


FOOTER = """<footer class="site"><div class="wrap">
<div class="cols">
<div><a class="brand" href="/"><img src="/assets/obs-rust-badge.svg" alt="" width="34" height="34"><span>OBS <em>Rust</em></span></a>
<p class="muted" style="margin-top:12px;font-size:15px;max-width:40ch">An independent, hybrid Rust/C/C++ rewrite of OBS Studio. Judged by the work.</p></div>
<div><h4>Project</h4><ul>
<li><a href="https://github.com/obs-rust/obs-studio">obs-studio</a></li>
<li><a href="https://github.com/obs-rust/obs-studio/releases">Releases</a></li>
<li><a href="https://github.com/obs-rust/obs-studio/blob/master/docs/features.md">Features ledger</a></li>
<li><a href="https://github.com/obs-rust/constitution/blob/main/CONSTITUTION.md">Constitution</a></li></ul></div>
<div><h4>Build</h4><ul>
<li><a href="/websocket/">WebSocket API</a></li><li><a href="/examples/">Examples</a></li>
<li><a href="https://github.com/obs-rust/obs-studio/issues?q=is%3Aopen+label%3Aready">Ready issues</a></li>
<li><a href="https://github.com/obs-rust/obs-studio/blob/master/docs/rust-port/testing-policy.md">Testing policy</a></li></ul></div>
<div><h4>Agents &amp; community</h4><ul>
<li><a href="/llms.txt">llms.txt</a></li><li><a href="/llms-full.txt">llms-full.txt</a></li>
<li><a href="https://discord.gg/6MWWX4x9pf">Discord</a></li><li><a href="https://www.reddit.com/r/ObsRust/">r/ObsRust</a></li></ul></div>
</div>
<p class="fine">OBS-Rust is an independent project, not affiliated with or endorsed by the <a href="https://obsproject.com">OBS Project</a>. OBS Studio is GPL-2.0-or-later; credit to every OBS contributor who built the foundation. Built {{build_date}} from <a href="https://github.com/obs-rust/obs-studio/commit/{{obs_sha}}">obs-studio@{{obs_sha_short}}</a> · <a href="https://github.com/obs-rust/obs-rust.github.io">site source</a>.</p>
</div></footer>"""


def render(tpl: str, ctx: dict, page_path: str) -> str:
    def head_sub(m):
        title, _, desc = m.group(1).partition("|")
        return head(title, desc, page_path)
    tpl = re.sub(r"\{\{head:([^}]*)\}\}", head_sub, tpl)
    tpl = re.sub(r"\{\{nav:(\w+)\}\}", lambda m: nav(m.group(1)), tpl)
    tpl = tpl.replace("{{footer}}", FOOTER)

    def sub(m):
        k = m.group(1)
        if k not in ctx:
            raise SystemExit(f"{page_path}: unknown placeholder {{{{{k}}}}}")
        return str(ctx[k])
    return re.sub(r"\{\{(\w+)\}\}", sub, tpl)


# ---------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--obs-studio", required=True, type=Path)
    ap.add_argument("--out", default=ROOT / "_site", type=Path)
    ap.add_argument("--offline", action="store_true")
    a = ap.parse_args()
    obs: Path = a.obs_studio.resolve()
    out: Path = a.out.resolve()
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "assets", out / "assets")
    for f in ["CNAME", ".nojekyll"]:
        if (ROOT / f).exists():
            shutil.copy(ROOT / f, out / f)

    git = lambda *x: subprocess.run(["git", "-C", str(obs), *x], capture_output=True, text=True).stdout.strip()  # noqa: E731
    obs_sha = git("rev-parse", "HEAD") or "master"
    ws_sha = (git("ls-tree", "HEAD", "plugins/obs-websocket").split() or ["", "", "master"])[2]
    now = dt.datetime.now(dt.timezone.utc)

    # protocol
    raw = lambda path: lambda: fetch(f"https://raw.githubusercontent.com/{WS_REPO}/{ws_sha}/{path}", "*/*")  # noqa: E731
    proto_bytes = cached("protocol.json.raw", a.offline, raw("docs/generated/protocol.json"))
    proto_md = cached("protocol.md", a.offline, raw("docs/generated/protocol.md")).decode()
    proto = json.loads(proto_bytes)
    (out / "websocket").mkdir(parents=True)
    (out / "websocket" / "protocol.json").write_bytes(proto_bytes)

    stats = repo_stats(a.offline)
    ledger = parse_ledger((obs / "docs/features.md").read_text())
    rel = stats["release"]

    # corpus
    docs = []
    for group, rel_path, p in corpus_sources(obs):
        text = p.read_text(errors="replace")
        if p.suffix == ".rst":
            text = rst_to_md(text)
        docs.append({"group": group, "path": rel_path, "text": text,
                     "url": f"https://github.com/{REPO}/blob/master/{rel_path}"})
    docs.append({"group": "websocket", "path": "obs-websocket/docs/generated/protocol.md", "text": proto_md,
                 "url": f"https://github.com/{WS_REPO}/blob/{ws_sha}/docs/generated/protocol.md"})
    docs.append({"group": "websocket", "path": "obs-websocket/reference.md", "text": protocol_md_reference(proto),
                 "url": f"{SITE}/websocket/"})
    chunks = []
    (out / "ai" / "docs").mkdir(parents=True)
    for d in docs:
        d["title"] = first_heading(d["text"], Path(d["path"]).stem)
        d["slug"] = slug(d["path"].rsplit(".", 1)[0])
        d["site_url"] = f"/ai/docs/{d['slug']}.md"
        (out / "ai" / "docs" / f"{d['slug']}.md").write_text(
            f"<!-- source: {d['url']} -->\n{d['text'].strip()}\n")
        for n, (h, t) in enumerate(chunk(d["text"])):
            chunks.append({"id": f"{d['slug']}#{n}", "doc": d["slug"], "group": d["group"], "title": d["title"],
                           "heading": h, "source": d["url"], "text": t})
    (out / "ai" / "corpus.json").write_text(json.dumps({
        "generated": now.isoformat(timespec="seconds"), "obs_studio_commit": obs_sha, "obs_websocket_commit": ws_sha,
        "docs": [{k: d[k] for k in ("slug", "group", "title", "path", "url", "site_url")} for d in docs],
        "chunks": chunks}, separators=(",", ":")))

    groups = {"project": "Project", "docs": "Project docs", "rust-port": "Rust port process",
              "knowledge": "Hard-won lessons", "libobs-api": "libobs C API reference", "websocket": "obs-websocket v5"}
    llms = [f"# OBS Studio Rust (obs-rust)", "",
            "> obs-studio-rust is an independent, hybrid Rust/C/C++ rewrite of OBS Studio that keeps the libobs C "
            "ABI, the obs-websocket v5 protocol and the plugin/scripting APIs compatible. Source: "
            f"https://github.com/{REPO}. Beta downloads: https://github.com/{REPO}/releases.", "",
            f"Generated {now:%Y-%m-%d} from obs-studio@{obs_sha[:9]} and obs-websocket@{ws_sha[:9]}. "
            f"The whole corpus in one file: {SITE}/llms-full.txt. Chunked JSON for retrieval: {SITE}/ai/corpus.json "
            f"(fields: id, doc, group, title, heading, source, text). Raw protocol: {SITE}/websocket/protocol.json.", ""]
    for g, label in groups.items():
        llms.append(f"## {label}")
        for d in docs:
            if d["group"] == g:
                llms.append(f"- [{d['title']}]({SITE}{d['site_url']}): {d['path']}")
        llms.append("")
    llms += ["## Optional", f"- [WebSocket API reference (HTML)]({SITE}/websocket/)",
             f"- [Examples]({SITE}/examples/)", f"- [Contributing with an AI agent](https://github.com/{REPO}#readme)", ""]
    (out / "llms.txt").write_text("\n".join(llms))
    full = [llms[0], "", llms[2], ""]
    for d in docs:
        full.append(f"\n\n<!-- ===== {d['path']} | {d['url']} ===== -->\n")
        full.append(d["text"].strip())
    (out / "llms-full.txt").write_text("\n".join(full) + "\n")

    ws_items, ws_nav = render_ws_items(proto)
    ctx = {
        **{k: v for k, v in stats.items() if k != "release"},
        "release_tag": esc(rel["tag_name"]) if rel else "—",
        "release_name": esc(rel["name"] or rel["tag_name"]) if rel else "releases",
        "release_url": esc(rel["html_url"]) if rel else f"https://github.com/{REPO}/releases",
        "release_date": rel["published_at"][:10] if rel else "",
        "downloads": render_downloads(rel),
        "feature_cards": render_feature_cards(ledger["features"]),
        "n_features": len(ledger["features"]), "n_fixed": len(ledger["fixed"]),
        "n_requests": len(proto["requests"]), "n_events": len(proto["events"]), "n_enums": len(proto["enums"]),
        "corpus_docs": len(docs), "corpus_chunks": len(chunks),
        "corpus_mb": f"{(out / 'llms-full.txt').stat().st_size / 1e6:.1f}",
        "build_date": f"{now:%Y-%m-%d}", "obs_sha": obs_sha, "obs_sha_short": obs_sha[:9],
        "ws_sha": ws_sha, "ws_sha_short": ws_sha[:9],
        "ws_items": ws_items, "ws_nav": ws_nav,
    }
    pages = []
    for tpl in sorted((ROOT / "src").rglob("*.html")):
        rel_path = tpl.relative_to(ROOT / "src")
        dest = out / (rel_path if rel_path.name == "index.html" else rel_path.with_suffix("") / "index.html")
        page_path = "/" + str(dest.parent.relative_to(out)).replace(".", "").strip("/")
        page_path = page_path.rstrip("/") + "/"
        dest.parent.mkdir(parents=True, exist_ok=True)
        # nav() emits {{stars}}, so render twice-safe: nav first then ctx
        dest.write_text(render(tpl.read_text(), ctx, page_path))
        pages.append(page_path)
    for extra in ["/llms.txt", "/llms-full.txt"]:
        pages.append(extra)
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{now:%Y-%m-%d}</lastmod></url>" for p in pages) + "</urlset>\n")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print(f"built {len(pages)} pages, {len(docs)} docs, {len(chunks)} chunks, "
          f"{ctx['corpus_mb']} MB llms-full, {ctx['n_requests']} requests → {out}")


if __name__ == "__main__":
    main()
