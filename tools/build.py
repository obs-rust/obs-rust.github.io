#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = ["jsonschema>=4.22", "pydantic>=2.7", "pillow>=11"]
# ///
"""Build obs-rust.com into _site/.

Usage: uv run tools/build.py --obs-studio PATH [--out _site] [--offline]

Inputs (see DESIGN.md §5):
  * src/*.html           hand-authored page templates ({{placeholders}})
  * assets/              copied verbatim
  * PATH (obs-studio)    README + docs/ for the corpus and features ledger;
                         its obs-websocket submodule SHA pins protocol.json
  * GitHub API           language bytes, stars, latest release (GITHUB_TOKEN optional)

Every JSON input is parsed into a typed model from tools/models.py at the boundary.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import html
import json
import os
import re
import shutil
import subprocess
import sys
import urllib.request
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path

from pydantic import JsonValue

sys.path.insert(0, str(Path(__file__).resolve().parent))
import corpus as corpusmod  # noqa: E402
import mcp as mcpmod
import sitedocs  # noqa: E402
from models import (  # noqa: E402
    Channel,
    Limit,
    Checksums,
    HeroImage,
    DownloadGroup,
    DownloadOption,
    GhAsset,
    GhCommitRef,
    Chunk,
    Conversion,
    CorpusFile,
    Doc,
    Feature,
    Feed,
    GhLanguages,
    GhRelease,
    GhReleases,
    GhRepo,
    Ledger,
    LedgerItem,
    PageContext,
    RepoStats,
    WsField,
    WsProtocol,
    WsRequest,
    WsRequestMessage,
    WsRequestPayload,
)

ROOT = Path(__file__).resolve().parent.parent
SITE = "https://obs-rust.com"
REPO = "obs-rust/obs-studio"
WS_REPO = "obs-rust/obs-websocket"
esc = html.escape


# ---------------------------------------------------------------- fetching
def fetch(url: str, accept: str = "application/vnd.github+json") -> bytes:
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "obs-rust-site-build"})
    tok = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if tok and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {tok}")
    with urllib.request.urlopen(req, timeout=60) as r:
        body: bytes = r.read()
    return body


def gh(path: str) -> bytes:
    return fetch(f"https://api.github.com/{path}")


def cached[T](name: str, offline: bool, producer: Callable[[], bytes], parse: Callable[[bytes], T]) -> T:
    """parse(producer()) and cache the raw bytes; offline (or on a network error) parse the cache."""
    cache = ROOT / ".cache" / name
    if not offline:
        try:
            data = producer()
            value = parse(data)
            cache.parent.mkdir(exist_ok=True)
            cache.write_bytes(data)
            return value
        except Exception as e:  # noqa: BLE001 - network is best effort
            print(f"warn: {name}: {e}; using cache", file=sys.stderr)
    if cache.exists():
        return parse(cache.read_bytes())
    raise SystemExit(f"no data for {name} (offline and no cache)")


def raw_bytes(b: bytes) -> bytes:
    return b


# ---------------------------------------------------------------- stats
def repo_stats(offline: bool) -> tuple[RepoStats, GhRelease | None, list[GhRelease]]:
    langs = cached("languages.json", offline, lambda: gh(f"repos/{REPO}/languages"), GhLanguages.model_validate_json)
    repo = cached("repo.json", offline, lambda: gh(f"repos/{REPO}"), GhRepo.model_validate_json)
    rels = cached("releases.json", offline, lambda: gh(f"repos/{REPO}/releases?per_page=20"),
                  GhReleases.model_validate_json).root
    # pin the figure: resolve the leaderboard branch to a commit, then read conversion.json at that commit
    lb = cached("leaderboard-commit.json", offline, lambda: gh(f"repos/{REPO}/commits/leaderboard"),
                GhCommitRef.model_validate_json)
    conv = cached("conversion.json", offline, lambda: fetch(
        f"https://raw.githubusercontent.com/{REPO}/{lb.sha}/conversion.json", "*/*"), Conversion.model_validate_json)
    total = langs.total() or 1

    def pct(lang: str) -> float:
        return round(100 * langs.bytes_of(lang) / total, 1)

    r, c, x = pct("Rust"), pct("C"), pct("C++")
    ours = [x for x in rels if x.tag_name.startswith("obs-studio-rust-v")]
    rel = ours[0] if ours else (rels[0] if rels else None)
    stats = RepoStats(
        rust_pct=r, c_pct=c, cpp_pct=x, other_pct=round(max(0.0, 100 - r - c - x), 1),
        rust_mb=f"{langs.bytes_of('Rust') / 1e6:.1f}", c_mb=f"{langs.bytes_of('C') / 1e6:.1f}",
        cpp_mb=f"{langs.bytes_of('C++') / 1e6:.1f}",
        libobs_pct=f"{conv.libobs.all.percent:.1f}",
        app_pct=f"{conv.app.percent:.1f}",
        conv_commit=conv.commit, conv_date=conv.date, conv_blob_sha=lb.sha,
        stars=repo.stargazers_count, forks=repo.forks_count,
    )
    return stats, rel, rels


def human_size(n: int) -> str:
    return f"{n / 1e6:.0f} MB" if n >= 1e6 else f"{n / 1e3:.0f} KB"


DL_GROUPS: tuple[DownloadGroup, ...] = (
    DownloadGroup("Windows", "x64 · arm64", (
        DownloadOption("-windows-x64.msi", "Installer · x64"), DownloadOption("-windows-arm64.msi", "Installer · arm64"),
        DownloadOption("-windows-x64.zip", "Portable · x64"), DownloadOption("-windows-arm64.zip", "Portable · arm64"))),
    DownloadGroup("macOS", "Apple silicon · Intel", (
        DownloadOption("-macos-arm64.dmg", "Apple silicon"), DownloadOption("-macos-x86_64.dmg", "Intel"))),
    DownloadGroup("Linux", "x86_64", (
        DownloadOption(".AppImage", "AppImage · any distro"),
        DownloadOption("-ubuntu-26.04-x86_64.deb", ".deb · Ubuntu 26.04"), DownloadOption(".flatpak", "Flatpak bundle"))),
)


HERO_SRC = "docs/images/appimage-main-window.png"
HERO_MAX_BYTES = 120_000


def hero_image(obs: Path, out: Path) -> HeroImage:
    """Re-encode the AppImage test's main-window screenshot as WebP; fail the build if it is missing."""
    from PIL import Image

    src = obs / HERO_SRC
    if not src.is_file():
        raise SystemExit(f"hero: {HERO_SRC} missing from the obs-studio checkout (sparse path?)")
    dest = out / "assets" / "main-window.webp"
    with Image.open(src) as im:
        w, h = im.size
        im.convert("RGB").save(dest, "WEBP", quality=82, method=6)
    size = dest.stat().st_size
    if size > HERO_MAX_BYTES:
        raise SystemExit(f"hero: main-window.webp is {size} bytes (> {HERO_MAX_BYTES})")
    return HeroImage(hero_src="/assets/main-window.webp", hero_w=w, hero_h=h, hero_kb=f"{size / 1e3:.0f}")


def release_checksums(rel: GhRelease | None, offline: bool) -> Checksums | None:
    if rel is None:
        return None
    asset = next((x for x in rel.assets if x.name == "SHA256SUMS"), None)
    if asset is None:
        return None
    url = asset.browser_download_url
    return cached(f"sha256sums-{rel.tag_name}.txt", offline, lambda: fetch(url, "*/*"), Checksums.parse)


def channels(rels: list[GhRelease], offline: bool) -> list[Channel]:
    """Newest stable and newest beta obs-studio-rust-v* releases; each must ship SHA256SUMS."""
    ours = [x for x in rels if x.tag_name.startswith("obs-studio-rust-v")]
    picks = [("Stable", "Recommended. The newest release that is not a prerelease.",
              next((x for x in ours if not x.prerelease), None)),
             ("Beta", "Newest build from master: the latest fixes, less testing.",
              next((x for x in ours if x.prerelease), None))]
    out: list[Channel] = []
    for name, note, rel in picks:
        if rel is None:
            continue
        sums = release_checksums(rel, offline)
        if sums is None:
            raise SystemExit(f"downloads: {rel.tag_name} has no SHA256SUMS asset")
        out.append(Channel(name=name, note=note, rel=rel, sums=sums))
    if not out:
        raise SystemExit("downloads: no obs-studio-rust-v* release")
    return out


def channel_assets(ch: Channel, group: DownloadGroup) -> list[tuple[DownloadOption, GhAsset, str]]:
    """The group's packages present in this release, each with its SHA-256; fails on a missing hash
    and on an OS with no package at all."""
    found: list[tuple[DownloadOption, GhAsset, str]] = []
    for opt in group.options:
        asset = next((x for x in ch.rel.assets if x.name.endswith(opt.suffix)), None)
        if asset is None:
            continue
        digest = ch.sums.by_name.get(asset.name)
        if digest is None:
            raise SystemExit(f"downloads: {asset.name} has no line in {ch.rel.tag_name}'s SHA256SUMS")
        found.append((opt, asset, digest))
    if not found:
        raise SystemExit(f"downloads: {ch.rel.tag_name} has no {group.os_name} package")
    return found


VERIFY = {"Windows": "Get-FileHash <file>", "macOS": "shasum -a 256 <file>", "Linux": "sha256sum <file>"}


def render_downloads(chans: list[Channel]) -> str:
    out: list[str] = []
    for ch in chans:
        cards: list[str] = []
        for group in DL_GROUPS:
            items = "".join(
                f'<li><a href="{esc(asset.browser_download_url)}">{esc(opt.label)}'
                f'<span>{human_size(asset.size)}</span></a>'
                f'<code class="sha" title="SHA-256 of {esc(asset.name)}">{digest}</code></li>'
                for opt, asset, digest in channel_assets(ch, group))
            cards.append(f'<div class="plate card" data-os="{group.os_name.lower()}"><span class="tag">{esc(group.arch)}</span>'
                         f'<div class="os">{group.os_name}</div><ul>{items}</ul>'
                         f'<p class="verify">Verify: <code>{esc(VERIFY[group.os_name])}</code> must equal the SHA-256.</p></div>')
        date = (ch.rel.published_at or "")[:10]
        out.append(f'<div class="chan" id="{ch.name.lower()}"><h3><b>{ch.name}</b> <a href="{esc(ch.rel.html_url)}">'
                   f'{esc(ch.rel.name or ch.rel.tag_name)}</a> <span>{date}</span></h3><p class="muted">{esc(ch.note)}</p>'
                   f'<div class="dl">{"".join(cards)}</div></div>')
    return "".join(out)


LIMITS: tuple[Limit, ...] = (
    Limit("Windows", "Windows SmartScreen warns on the first start of the portable build: choose More info, then Run anyway.",
          r"SmartScreen warns on the first start"),
    Limit("macOS", "Packages are signed and notarized only when the project's release credentials are configured; "
          "an unnotarized app is allowed once in System Settings → Privacy & Security → Open Anyway.",
          r"signed and notarized when the project's release credentials are\s+configured"),
    Limit("Linux", "The Flatpak bundle does not update itself and is not on Flathub: install the next release's bundle the same way.",
          r"does not update itself yet"),
    Limit("Linux", "The AppImage is tested on AlmaLinux 8, Ubuntu 22.04 and 24.04, Arch Linux and NixOS; the .deb targets Ubuntu 26.04.",
          r"The AppImage is tested on AlmaLinux 8"),
    Limit("All", "It installs beside upstream OBS and imports its settings once, on first start; later upstream changes are not "
          "imported. Going back is safe: upstream's files are never changed.",
          r"later upstream changes are\s+not imported again"),
    Limit("Windows, macOS", "A new app identity, so the OS may ask for capture permissions again.",
          r"the OS may\s+ask for capture permissions again"),
)


def render_limits(readme: str, obs_sha: str) -> str:
    rows: list[str] = []
    for lim in LIMITS:
        m = re.search(lim.readme_pattern, readme)
        if m is None:
            raise SystemExit(f"limits: README no longer says {lim.readme_pattern!r}; update LIMITS")
        line = readme.count("\n", 0, m.start()) + 1
        rows.append(f'<li><b>{esc(lim.os)}</b><span>{esc(lim.text)}</span>'
                    f'<a class="receipt" href="https://github.com/{REPO}/blob/{obs_sha}/README.md#L{line}">README.md:{line}</a></li>')
    return "".join(rows)


# ---------------------------------------------------------------- features ledger
MD_LINK = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def md_inline(s: str) -> str:
    s = esc(MD_LINK.sub(r"\1", s))
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return re.sub(r"\*\*([^*]+)\*\*", r"\1", s)


@dataclass(slots=True)
class _LedgerDraft:
    """A ledger bullet while its continuation lines are still being read."""

    section: str
    area: str
    text: str


def _feature(item: LedgerItem) -> Feature:
    m = re.match(r"\*\*(.+?)\*\*\s*(.*)", item.text)
    name, rest = (m.group(1), m.group(2)) if m else (item.text, "")
    d = re.search(r"\*([A-Za-z, ]+)\*,\s*(\d{4}-\d{2}-\d{2})", rest)
    platforms, date = (d.group(1), d.group(2)) if d else ("", "")
    desc = re.split(r"\s\*[A-Za-z, ]+\*,\s*\d{4}", rest)[0].strip()
    pr = (re.findall(r"\[#(\d+)\]\(https://github.com/obs-rust/obs-studio/pull/\d+\)", rest) or [""])[0]
    return Feature(section=item.section, area=item.area, text=item.text, name=name, platforms=platforms, date=date,
                   desc=desc, pr=pr)


def parse_ledger(text: str) -> Ledger:
    drafts: list[_LedgerDraft] = []
    cur: _LedgerDraft | None = None
    section, area = "", ""
    for line in text.splitlines():
        if line.startswith("## "):
            section, area = line[3:].strip(), ""
        elif line.startswith("### "):
            area = line[4:].strip()
        if line.startswith("- "):
            cur = _LedgerDraft(section=section, area=area, text=line[2:].strip())
            drafts.append(cur)
        elif cur and line.startswith("  ") and line.strip():
            cur.text += " " + line.strip()
        elif not line.strip() or line.startswith("#"):
            cur = None
    items = [LedgerItem(section=d.section, area=d.area, text=d.text) for d in drafts]
    feats = [_feature(i) for i in items if i.section == "Features" and i.text.startswith("**")]
    fixed = [i for i in items if i.section == "Fixed upstream bugs"]
    return Ledger(features=feats, fixed=fixed)


def render_feature_cards(feats: list[Feature], n: int = 9) -> str:
    out: list[str] = []
    for f in sorted(feats, key=lambda f: f.date, reverse=True)[:n]:
        name = md_inline(f.name.rstrip("."))
        desc = md_inline(f.desc)
        if len(desc) > 220:
            desc = desc[:217].rsplit(" ", 1)[0] + "…"
        href = f"https://github.com/obs-rust/obs-studio/pull/{f.pr}" if f.pr else \
            "https://github.com/obs-rust/obs-studio/blob/master/docs/features.md"
        out.append(f'<a class="plate card" href="{href}"><h3>{name}</h3><p>{desc}</p>'
                   f'<div class="m"><span class="tag rust">{esc(f.area)}</span>'
                   f'<span class="tag">{esc(f.platforms)}</span><span>{esc(f.date)}</span></div></a>')
    return "".join(out)


# ---------------------------------------------------------------- corpus
CORPUS_ROOT_FILES = ["README.md", "AGENTS.md", "BUILD.md", "CONTRIBUTING.md", "SECURITY.md", "CODESTYLE.md",
                     "CONSTITUTION.md"]


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
    lines = t.splitlines()
    out: list[str] = []
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
    sections: list[tuple[str, str]] = []
    head = ""
    buf: list[str] = []
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
    out: list[tuple[str, str]] = []
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
def protocol_md_reference(p: WsProtocol) -> str:
    """Render protocol.json as compact markdown for the corpus."""
    out = ["# obs-websocket v5 protocol reference (generated)", ""]
    out.append("## Enums")
    for e in p.enums:
        out.append(f"### {e.enumType}")
        for i in e.enumIdentifiers:
            out.append(f"- `{i.enumIdentifier}` = `{i.enumValue}`: {i.description}")
        out.append("")
    out.append("## Requests")
    for r in p.requests:
        out.append(f"### {r.requestType}")
        out.append(f"Category: {r.category}. Since {r.initialVersion}. Complexity {r.complexity}/5."
                   + (" DEPRECATED." if r.deprecated else ""))
        out.append(r.description)
        if r.requestFields:
            out.append("Request fields:")
            for f in r.requestFields:
                opt = " (optional" + (f", default {f.valueOptionalBehavior}" if f.valueOptionalBehavior else "") + ")" \
                    if f.valueOptional else ""
                rest = f" restrictions: {f.valueRestrictions}" if f.valueRestrictions else ""
                out.append(f"- `{f.valueName}` {f.valueType}{opt}{rest}: {f.valueDescription}")
        if r.responseFields:
            out.append("Response fields:")
            for f in r.responseFields:
                out.append(f"- `{f.valueName}` {f.valueType}: {f.valueDescription}")
        out.append("")
    out.append("## Events")
    for e in p.events:
        out.append(f"### {e.eventType}")
        out.append(f"Category: {e.category}. Subscription: {e.eventSubscription}. Since {e.initialVersion}.")
        out.append(e.description)
        for f in e.dataFields:
            out.append(f"- `{f.valueName}` {f.valueType}: {f.valueDescription}")
        out.append("")
    return "\n".join(out)


def md_desc(s: str) -> str:
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    return s.replace("\n", "<br>")


def fields_table(fields: list[WsField], kind: str) -> str:
    if not fields:
        return ""
    rows: list[str] = []
    for f in fields:
        opt = ""
        if f.valueOptional:
            ob = f.valueOptionalBehavior or ""
            opt = f'<span class="tag haz" title="{esc(ob)}">optional</span>'
        restr = f'<div class="restr">{esc(f.valueRestrictions)}</div>' if f.valueRestrictions else ""
        rows.append(f'<tr><td><code>{esc(f.valueName)}</code>{opt}</td><td class="ty">{esc(f.valueType)}</td>'
                    f'<td>{md_desc(f.valueDescription)}{restr}</td></tr>')
    return f'<h3>{kind}</h3><div class="tw"><table class="ft"><tbody>{"".join(rows)}</tbody></table></div>'


def example_value(value_type: str) -> JsonValue:
    """A placeholder value of an obs-websocket field type, for example messages."""
    match value_type:
        case "String":
            return ""
        case "Number":
            return 0
        case "Boolean":
            return True
        case "Object":
            return {}
        case t if t.startswith("Array"):
            return []
        case _:
            return None


def example_request_data(r: WsRequest) -> dict[str, JsonValue]:
    return {f.valueName: example_value(f.valueType) for f in r.requestFields if not f.valueOptional}


def example_message(r: WsRequest) -> str:
    msg = WsRequestMessage(d=WsRequestPayload(requestType=r.requestType, requestId="1",
                                              requestData=example_request_data(r) if r.requestFields else None))
    return json.dumps(msg.model_dump(mode="json", exclude_none=True), indent=2)


def render_ws_items(p: WsProtocol) -> tuple[str, str]:
    cats = sorted({r.category for r in p.requests} | {e.category for e in p.events})
    items: list[str] = []
    for r in p.requests:
        rid = r.requestType
        ex = example_message(r)
        items.append(
            f'<article class="it" id="{rid}" data-kind="request" data-cat="{esc(r.category)}" data-search="{esc((rid + " " + r.description).lower())}">'
            f'<header><a class="nm" href="#{rid}">{rid}</a><span class="tag cu">request</span>'
            f'<span class="tag">{esc(r.category)}</span><span class="tag">v{esc(r.initialVersion)}</span>'
            f'{"<span class=\"tag haz\">deprecated</span>" if r.deprecated else ""}'
            f'<span class="cx" title="complexity">{"●" * r.complexity}{"○" * (5 - r.complexity)}</span>'
            f'<button class="try" data-req="{rid}" title="Load into the live console">Try ▸</button></header>'
            f'<p>{md_desc(r.description)}</p>'
            f'{fields_table(r.requestFields, "Request fields")}{fields_table(r.responseFields, "Response fields")}'
            f'<details><summary>Example message</summary><pre>{esc(ex)}</pre></details></article>')
    for e in p.events:
        eid = e.eventType
        items.append(
            f'<article class="it" id="{eid}" data-kind="event" data-cat="{esc(e.category)}" data-search="{esc((eid + " " + e.description).lower())}">'
            f'<header><a class="nm" href="#{eid}">{eid}</a><span class="tag rust">event</span>'
            f'<span class="tag">{esc(e.category)}</span><span class="tag">{esc(e.eventSubscription)}</span>'
            f'<span class="tag">v{esc(e.initialVersion)}</span>'
            f'{"<span class=\"tag haz\">deprecated</span>" if e.deprecated else ""}</header>'
            f'<p>{md_desc(e.description)}</p>{fields_table(e.dataFields, "Data fields")}</article>')
    for en in p.enums:
        nid = en.enumType
        rows = "".join(f'<tr><td><code>{esc(i.enumIdentifier)}</code></td><td class="ty">{esc(str(i.enumValue))}</td>'
                       f'<td>{md_desc(i.description)}</td></tr>' for i in en.enumIdentifiers)
        items.append(
            f'<article class="it" id="{nid}" data-kind="enum" data-cat="enums" data-search="{esc(nid.lower())}">'
            f'<header><a class="nm" href="#{nid}">{nid}</a><span class="tag haz">enum</span>'
            f'<span class="tag">{len(en.enumIdentifiers)} values</span></header>'
            f'<div class="tw"><table class="ft"><tbody>{rows}</tbody></table></div></article>')
    nav: list[str] = []
    for c in cats:
        reqs = [r.requestType for r in p.requests if r.category == c]
        evs = [e.eventType for e in p.events if e.category == c]
        links = "".join(f'<a href="#{n}" data-for="{n}">{n}</a>' for n in reqs) + \
            "".join(f'<a href="#{n}" data-for="{n}" class="ev">{n}</a>' for n in evs)
        nav.append(f'<details open><summary>{esc(c)} <span>{len(reqs) + len(evs)}</span></summary>{links}</details>')
    nav.append('<details open><summary>enums <span>' + str(len(p.enums)) + '</span></summary>'
               + "".join(f'<a href="#{e.enumType}" data-for="{e.enumType}">{e.enumType}</a>' for e in p.enums) + '</details>')
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
<link rel="preload" href="/assets/fonts/big-shoulders-stencil-display.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css">
<link rel="stylesheet" href="/assets/site.css">"""


NAV_ITEMS = [("home", "/", "Home"), ("download", "/#download", "Download"), ("websocket", "/websocket/", "WebSocket API"),
             ("mcp", "/mcp/", "MCP"), ("examples", "/examples/", "Examples"), ("ai", "/ai/", "AI corpus")]


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
<div><h2>Project</h2><ul>
<li><a href="https://github.com/obs-rust/obs-studio">obs-studio</a></li>
<li><a href="https://github.com/obs-rust/obs-studio/releases">Releases</a></li>
<li><a href="https://github.com/obs-rust/obs-studio/blob/master/docs/features.md">Features ledger</a></li>
<li><a href="https://github.com/obs-rust/constitution/blob/main/CONSTITUTION.md">Constitution</a></li></ul></div>
<div><h2>Build</h2><ul>
<li><a href="/websocket/">WebSocket API</a></li><li><a href="/mcp/">MCP server</a></li><li><a href="/examples/">Examples</a></li>
<li><a href="https://github.com/obs-rust/obs-studio/issues?q=is%3Aopen+label%3Aready">Ready issues</a></li>
<li><a href="https://github.com/obs-rust/obs-studio/blob/master/docs/rust-port/testing-policy.md">Testing policy</a></li></ul></div>
<div><h2>Agents &amp; community</h2><ul>
<li><a href="/llms.txt">llms.txt</a></li><li><a href="/llms-full.txt">llms-full.txt</a></li>
<li><a href="https://discord.gg/6MWWX4x9pf">Discord</a></li><li><a href="https://www.reddit.com/r/ObsRust/">r/ObsRust</a></li></ul></div>
</div>
<p class="fine">OBS-Rust is an independent project, not affiliated with or endorsed by the <a href="https://obsproject.com">OBS Project</a>. OBS Studio is GPL-2.0-or-later; credit to every OBS contributor who built the foundation. Built {{build_date}} from <a href="https://github.com/obs-rust/obs-studio/commit/{{obs_sha}}">obs-studio@{{obs_sha_short}}</a> · <a href="https://github.com/obs-rust/obs-rust.github.io">site source</a>.</p>
</div></footer>"""

def render(tpl: str, ctx: Mapping[str, str], page_path: str) -> str:
    def head_sub(m: re.Match[str]) -> str:
        title, _, desc = m.group(1).partition("|")
        return head(title, desc, page_path)
    tpl = re.sub(r"^\{\{head:(.*)\}\}$", head_sub, tpl, flags=re.M)
    tpl = re.sub(r"\{\{nav:(\w+)\}\}", lambda m: nav(m.group(1)), tpl)
    tpl = tpl.replace("{{footer}}", FOOTER)

    def sub(m: re.Match[str]) -> str:
        k = m.group(1)
        if k not in ctx:
            raise SystemExit(f"{page_path}: unknown placeholder {{{{{k}}}}}")
        return ctx[k]
    return re.sub(r"\{\{(\w+)\}\}", sub, tpl)


# ---------------------------------------------------------------- main
@dataclass(frozen=True, slots=True)
class Args:
    obs_studio: Path
    out: Path
    offline: bool


def parse_args() -> Args:
    ap = argparse.ArgumentParser()
    ap.add_argument("--obs-studio", required=True, type=Path)
    ap.add_argument("--out", default=ROOT / "_site", type=Path)
    ap.add_argument("--offline", action="store_true")
    ns = ap.parse_args()
    return Args(obs_studio=Path(ns.obs_studio).resolve(), out=Path(ns.out).resolve(), offline=bool(ns.offline))


def main() -> None:
    a = parse_args()
    obs, out = a.obs_studio, a.out
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(ROOT / "assets", out / "assets")
    hero_img = hero_image(obs, out)
    for f in ["CNAME", ".nojekyll"]:
        if (ROOT / f).exists():
            shutil.copy(ROOT / f, out / f)

    def git(*x: str) -> str:
        return subprocess.run(["git", "-C", str(obs), *x], capture_output=True, text=True).stdout.strip()

    obs_sha = git("rev-parse", "HEAD") or "master"
    ws_sha = (git("ls-tree", "HEAD", "plugins/obs-websocket").split() or ["", "", "master"])[2]
    now = dt.datetime.now(dt.timezone.utc)

    # protocol
    def raw(path: str) -> Callable[[], bytes]:
        return lambda: fetch(f"https://raw.githubusercontent.com/{WS_REPO}/{ws_sha}/{path}", "*/*")

    proto_bytes = cached("protocol.json.raw", a.offline, raw("docs/generated/protocol.json"), raw_bytes)
    proto_md = cached("protocol.md", a.offline, raw("docs/generated/protocol.md"), raw_bytes).decode()
    proto = WsProtocol.model_validate_json(proto_bytes)
    (out / "websocket").mkdir(parents=True)
    (out / "websocket" / "protocol.json").write_bytes(proto_bytes)

    stats, rel, rels_all = repo_stats(a.offline)
    chans = channels(rels_all, a.offline)
    ledger = parse_ledger((obs / "docs/features.md").read_text())

    # corpus
    def make_doc(group: str, path: str, text: str, url: str) -> Doc:
        doc_slug = slug(path.rsplit(".", 1)[0])
        return Doc(group=group, path=path, text=text, url=url, title=first_heading(text, Path(path).stem),
                   slug=doc_slug, site_url=f"/ai/docs/{doc_slug}.md", tier=corpusmod.tier(path),
                   source=(url.replace("/blob/master/", f"/blob/{obs_sha}/") if url.startswith("https://github.com/")
                           else url))

    docs: list[Doc] = []
    for group, rel_path, p in corpus_sources(obs):
        text = p.read_text(errors="replace")
        if p.suffix == ".rst":
            text = rst_to_md(text)
        docs.append(make_doc(group, rel_path, text, f"https://github.com/{REPO}/blob/master/{rel_path}"))
    docs.append(make_doc("websocket", "obs-websocket/docs/generated/protocol.md", proto_md,
                         f"https://github.com/{WS_REPO}/blob/{ws_sha}/docs/generated/protocol.md"))
    docs.append(make_doc("websocket", "obs-websocket/reference.md", protocol_md_reference(proto), f"{SITE}/websocket/"))
    surface = mcpmod.load_surface(obs)
    sessions = mcpmod.load_sessions(ROOT, surface)
    mcp_md = mcpmod.corpus_markdown(surface, sessions)
    docs.append(make_doc("mcp", "mcp/reference.md", mcp_md, f"{SITE}/mcp/"))
    # site documents for agents (DESIGN.md P0 #2): install, choose an API, copy an example
    n_ro = sum(1 for t in surface.tools if t.annotations.readOnlyHint)
    docs.append(make_doc("site", "site/download.md", sitedocs.download_md(
        chans, DL_GROUPS, (obs / "README.md").read_text(), human_size), f"{SITE}/#download"))
    docs.append(make_doc("site", "site/control.md", sitedocs.control_md(
        len(proto.requests), len(proto.events), len(proto.enums), len(surface.tools), n_ro), f"{SITE}/websocket/"))
    docs.append(make_doc("site", "site/examples.md", sitedocs.examples_md(
        (ROOT / "src" / "examples.html").read_text()), f"{SITE}/examples/"))
    (out / "ai" / "docs").mkdir(parents=True)
    ledger_items: list[LedgerItem] = [*ledger.features, *ledger.fixed]
    for d in docs:
        (out / "ai" / "docs" / f"{d.slug}.md").write_text(
            f"---\ntitle: {json.dumps(d.title)}\nsource: {d.source}\ncommit: {obs_sha}\n"
            f"tier: {d.tier}\ntokens_est: {corpusmod.tokens_est(d.text)}\n---\n{d.text.strip()}\n")
    chunks: list[Chunk] = []
    for d in docs:
        if d.path == "obs-websocket/reference.md":
            chunks += corpusmod.ws_chunks(d, proto, SITE)
        elif d.path == "mcp/reference.md":
            chunks += corpusmod.mcp_chunks(d, surface, SITE, mcpmod.fields_rows)
        elif d.path == "obs-websocket/docs/generated/protocol.md":
            # narrative only (connecting, auth, opcodes); items come from protocol.json as typed chunks
            chunks += corpusmod.prose_chunks(dataclasses.replace(d, text=d.text.split("\n# Enums")[0]), d.title)
        elif d.path == "docs/features.md":
            chunks += corpusmod.prose_chunks(dataclasses.replace(d, text=d.text.split("\n## Features")[0]), d.title)
            chunks += corpusmod.ledger_chunks(d, ledger_items)
        else:
            chunks += corpusmod.prose_chunks(d, d.title)
    ids = [c.id for c in chunks]
    if len(ids) != len(set(ids)):
        raise SystemExit(f"corpus: duplicate chunk ids: {sorted({i for i in ids if ids.count(i) > 1})[:10]}")
    corpus_file = CorpusFile(schema_version=corpusmod.SCHEMA_VERSION, generated=now.isoformat(timespec="seconds"),
                             obs_studio_commit=obs_sha, obs_websocket_commit=ws_sha,
                             docs=[d.ref() for d in docs], chunks=chunks)
    (out / "ai" / "corpus.json").write_text(json.dumps(corpus_file.model_dump(mode="json"), separators=(",", ":")))
    (out / "ai" / "corpus").mkdir()
    for g in sorted({c.group for c in chunks}):
        (out / "ai" / "corpus" / f"{g}.jsonl").write_text(
            "\n".join(json.dumps(c.model_dump(mode="json"), separators=(",", ":")) for c in chunks if c.group == g)
            + "\n")

    groups = {"project": "Project", "docs": "Project docs", "rust-port": "Rust port process",
              "knowledge": "Hard-won lessons", "libobs-api": "libobs C API reference", "websocket": "obs-websocket v5",
              "mcp": "MCP server (agent control)"}
    title = "# OBS Studio Rust (obs-rust)"
    blurb = ("> obs-studio-rust is an independent, hybrid Rust/C/C++ rewrite of OBS Studio that keeps the libobs C "
             "ABI, the obs-websocket v5 protocol and the plugin/scripting APIs compatible. It ships stable and beta builds for "
             f"Windows, macOS and Linux, and a local MCP server for agents. Source: https://github.com/{REPO}.")
    full = [title, "", blurb, ""]
    for d in docs:
        full.append(f"\n\n<!-- ===== {d.path} | {d.source} ===== -->\n")
        full.append(d.text.strip())
    (out / "llms-full.txt").write_text("\n".join(full) + "\n")

    # llms-ctx.txt: the core bundle that fits a context window (DESIGN.md §7, budget 300 KB)
    core = ["site/download.md", "site/control.md", "site/examples.md", "README.md", "AGENTS.md", "docs/rust-port/mcp.md", "docs/rust-port/control-api.md",
            "mcp/reference.md", "docs/rust-port/coordination.md", "docs/rust-port/testing-policy.md",
            "obs-websocket/reference.md"]
    by_path = {d.path: d for d in docs}
    missing_core = [c for c in core if c not in by_path]
    if missing_core:
        raise SystemExit(f"llms-ctx: core docs missing: {missing_core}")
    latest_tag = "; ".join(f"{c.name.lower()} {c.rel.tag_name}" for c in chans)
    ctx_txt = [title, "", blurb, "",
               f"Core context bundle, generated {now:%Y-%m-%d} from obs-studio@{obs_sha[:9]}. "
               f"Everything else: {SITE}/llms.txt (index) and {SITE}/llms-full.txt (all docs).", "",
               "## Download", f"Releases: {latest_tag}. Install the stable release unless you need a fix that is "
               f"only in the beta. Every file with its SHA-256: {SITE}/ai/docs/site-download.md", ""]
    for c in chans:
        ctx_txt += [f"{c.name} ({c.rel.tag_name}, {c.rel.html_url}): " + ", ".join(
            x.name for x in c.rel.assets if x.name.startswith("OBS-Studio-Rust-") and "symbols" not in x.name), ""]
    for c in core:
        d = by_path[c]
        ctx_txt += [f"\n\n<!-- ===== {d.path} | {d.source} ===== -->\n", d.text.strip()]
    (out / "llms-ctx.txt").write_text("\n".join(ctx_txt) + "\n")
    ctx_kb = (out / "llms-ctx.txt").stat().st_size / 1024
    if ctx_kb > 300:
        raise SystemExit(f"llms-ctx.txt is {ctx_kb:.0f} KB, over the 300 KB budget")

    def feed(name: str, path: str) -> Feed:
        return Feed(name=name, path=path, size=(out / path.lstrip("/")).stat().st_size)

    feeds = [feed("llms-ctx.txt: core bundle, one context window", "/llms-ctx.txt"),
             feed("llms-full.txt: every document", "/llms-full.txt"),
             feed("corpus.json: typed chunks with breadcrumbs, for retrieval", "/ai/corpus.json"),
             feed("protocol.json: obs-websocket v5 spec", "/websocket/protocol.json")]
    header = [title, "", blurb, "",
              f"Generated {now:%Y-%m-%d} from obs-studio@{obs_sha[:9]} and obs-websocket@{ws_sha[:9]}. "
              f"Releases: {latest_tag}. corpus.json has schema_version "
              f"{corpusmod.SCHEMA_VERSION}, {len(chunks)} chunks, and is also split per group under /ai/corpus/<group>.jsonl.", ""]
    extra = {
        "Control OBS": [
            f"- [MCP server]({SITE}/mcp/index.md): {len(surface.tools)} typed tools to control a local "
            "obs-studio-rust from an agent: client config, requirements, sessions, reference",
            f"- [MCP schema (JSON)]({SITE}/mcp/schema.json): pre-fetched tools/list + resources/list + ToolError",
            f"- [WebSocket API reference (HTML)]({SITE}/websocket/): every obs-websocket v5 request, event and enum, "
            "with a live console",
            f"- [Examples]({SITE}/examples/): Rust, Python, JS and raw-socket clients, batch requests, scripts, plugins"],
    }
    ws_items, ws_nav = render_ws_items(proto)
    mstats = mcpmod.write_artifacts(out, surface, sessions, obs_sha, now.isoformat(timespec="seconds"),
                                    ROOT / "tools" / "vendor")
    (out / "mcp" / "index.md").write_text(
        f"---\ntitle: obs-studio-rust MCP server\nsource_commit: {obs_sha}\nurl: {SITE}/mcp/\n---\n" + mcp_md)
    man = sitedocs.manifest([sitedocs.manifest_doc(out, d.slug, d.path, d.title, d.tier, d.group, d.source)
                             for d in docs], now.isoformat(timespec="seconds"), obs_sha, ws_sha)
    (out / "ai" / "manifest.json").write_text(json.dumps(man.model_dump(mode="json"), indent=1) + "\n")
    router = sitedocs.router_rows(out)
    (out / "llms.txt").write_text(corpusmod.llms_txt(docs, header + sitedocs.router_llms(router), SITE, feeds, extra))
    mref, mnav = mcpmod.render_reference(surface.tools)
    hero = mcpmod.render_transcript(next(x for x in sessions if x.slug == "record-when-ready"))
    ctx = PageContext(
        stats=stats, mcp=mstats, hero=hero_img,
        release_tag=esc(rel.tag_name) if rel else "—",
        release_name=esc(rel.name or rel.tag_name) if rel else "releases",
        release_url=esc(rel.html_url) if rel else f"https://github.com/{REPO}/releases",
        release_date=(rel.published_at or "")[:10] if rel else "",
        downloads=render_downloads(chans),
        cta_version=esc(chans[0].rel.tag_name.removeprefix("obs-studio-rust-")),
        release_line=" · ".join(f'{c.name}: <a href="{esc(c.rel.html_url)}">{esc(c.rel.name or c.rel.tag_name)}</a>'
                                for c in chans),
        limits=render_limits((obs / "README.md").read_text(), obs_sha),
        feature_cards=render_feature_cards(ledger.features),
        n_features=len(ledger.features), n_fixed=len(ledger.fixed),
        n_requests=len(proto.requests), n_events=len(proto.events), n_enums=len(proto.enums),
        corpus_docs=len(docs), corpus_chunks=len(chunks),
        corpus_mb=f"{(out / 'llms-full.txt').stat().st_size / 1e6:.1f}",
        ctx_kb=f"{ctx_kb:.0f}",
        ai_router=sitedocs.router_html(router),
        ai_doc_list="".join(
            f"<h3>{esc(groups.get(g, g))}</h3>" + "".join(
                f'<a href="{d.site_url}" title="{esc(d.path)}">{esc(d.title)}</a>'
                for d in docs if d.group == g) for g in groups),
        build_date=f"{now:%Y-%m-%d}", obs_sha=obs_sha, obs_sha_short=obs_sha[:9],
        ws_sha=ws_sha, ws_sha_short=ws_sha[:9],
        ws_items=ws_items, ws_nav=ws_nav,
        mcp_protocol=surface.protocol, mcp_ref=mref, mcp_ref_nav=mnav,
        mcp_sessions=mcpmod.render_sessions(sessions), mcp_hero_tx=hero,
        mcp_json_pretty=esc(json.dumps(surface.mcp_json.model_dump(mode="json", exclude_none=True),
                                       separators=(",", ":"))),
        mcp_resources="".join(f'<article class="tool"><header><span class="nm">{esc(r.uri)}</span>'
                              f'<span class="tag">{esc(r.mimeType)}</span></header><p>{esc(r.description)}</p></article>'
                              for r in surface.resources),
    )
    placeholders = ctx.as_mapping()
    pages: list[str] = []
    for tpl in sorted((ROOT / "src").rglob("*.html")):
        rel_path = tpl.relative_to(ROOT / "src")
        dest = out / (rel_path if rel_path.name in ("index.html", "404.html")
                      else rel_path.with_suffix("") / "index.html")
        page_path = "/" + str(dest.parent.relative_to(out)).replace(".", "").strip("/")
        page_path = page_path.rstrip("/") + "/"
        dest.parent.mkdir(parents=True, exist_ok=True)
        # nav() emits {{stars}}, so render twice-safe: nav first then ctx
        dest.write_text(render(tpl.read_text(), placeholders, page_path))
        if rel_path.name != "404.html":
            pages.append(page_path)
    pages += ["/llms.txt", "/llms-ctx.txt", "/llms-full.txt", "/mcp/schema.json", "/mcp/index.md"]
    (out / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(f"<url><loc>{SITE}{p}</loc><lastmod>{now:%Y-%m-%d}</lastmod></url>" for p in pages) + "</urlset>\n")
    (out / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {SITE}/sitemap.xml\n")
    print(f"built {len(pages)} pages, {len(docs)} docs, {len(chunks)} chunks, "
          f"{ctx.corpus_mb} MB llms-full, {ctx.n_requests} requests → {out}")


if __name__ == "__main__":
    main()
