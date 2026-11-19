"""/security/: the disclosure tracker (coordinated disclosure with the OBS Project).

Inputs, all public:
  * security/archives.json      aggregates per encrypted archive (DisclosureArchives); never titles or ids
                                of embargoed advisories
  * security/archives/*.zip     the AES-256 encrypted archives themselves, copied byte for byte
  * GitHub advisories API       the published advisories of obs-rust/obs-studio (GhAdvisories)
  * SECURITY.md (obs-studio)    the policy sentences, quoted with commit-pinned line receipts

Fails closed: a zip whose size or SHA-256 differs from archives.json, a stray file beside the zips,
severity counts that do not add up, or a published_ids entry that GitHub does not show as published.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

from models import (DisclosureArchive, DisclosureArchives, GhAdvisory, PublishedFile, PublishedRef, SecurityPage,
                    SeverityCounts)

esc = html.escape
REPO = "obs-rust/obs-studio"
SITE_REPO = "obs-rust/obs-rust.github.io"
REPORT_URL = f"https://github.com/{REPO}/security/advisories/new"
ADVISORIES_API = f"repos/{REPO}/security-advisories?state=published&per_page=100"
ZIP_DIR = "security/archives"
SEVERITIES: tuple[tuple[str, str], ...] = (("critical", "Critical"), ("high", "High"), ("medium", "Medium"), ("low", "Low"))


@dataclass(frozen=True, slots=True)
class Step:
    """One stage of the disclosure process, quoted from SECURITY.md (pattern must still match) or, when the
    policy file does not cover it, receipted by security/archives.json."""

    n: str
    title: str
    text: str
    pattern: str | None


STEPS: tuple[Step, ...] = (
    Step("01", "Report privately", "Use Report a vulnerability on the Security tab of obs-rust/obs-studio, "
         "not a public issue, for a bug a remote party can reach.", r"Report a\s+vulnerability\*\*"),
    Step("02", "Fix under embargo", "A maintainer acknowledges the report within 72 hours; the fix is written and "
         "reviewed in the advisory's private fork, failing test first.", r"\*\*Within 72 hours:\*\*"),
    Step("03", "Share with upstream", "Embargoed advisories go to the OBS Project in numbered AES-256 archives. "
         "The password travels on a separate channel and is not on this site.", None),
    Step("04", "Publish", "The project aims to disclose within 90 days of the report, requests a CVE where it "
         "applies, and credits the reporter.", r"We aim to disclose within 90 days of the report"),
)


def human_size(n: int) -> str:
    return f"{n / 1e6:.1f} MB" if n >= 1e6 else f"{n / 1e3:.0f} KB"


def check_archives(data: DisclosureArchives, root: Path, published: list[GhAdvisory]) -> list[str]:
    """Every way archives.json can disagree with the zips beside it or with GitHub; empty when it agrees."""
    errs: list[str] = []
    numbers = [a.number for a in data.archives]
    if len(numbers) != len(set(numbers)):
        errs.append(f"archives.json: duplicate archive numbers {numbers}")
    listed = {a.file for a in data.archives}
    on_disk = {p.name for p in (root / ZIP_DIR).iterdir()} if (root / ZIP_DIR).is_dir() else set[str]()
    if stray := sorted(on_disk - listed):
        errs.append(f"{ZIP_DIR}: files not in archives.json: {stray}")
    live = {a.ghsa_id for a in published if a.state == "published"}
    for a in data.archives:
        if not a.file.startswith(f"obs-security-disclosure-{a.number}-{a.cutoff}"):
            errs.append(f"archive {a.number}: file {a.file} does not carry its number and cutoff")
        f = root / ZIP_DIR / a.file
        if not f.is_file():
            errs.append(f"archive {a.number}: {ZIP_DIR}/{a.file} is missing")
            continue
        body = f.read_bytes()
        if len(body) != a.size:
            errs.append(f"archive {a.number}: {a.file} is {len(body)} bytes, archives.json says {a.size}")
        if hashlib.sha256(body).hexdigest() != a.sha256:
            errs.append(f"archive {a.number}: {a.file} SHA-256 differs from archives.json")
        if not body.startswith(b"PK\x03\x04") or (body[6] & 1) == 0:
            errs.append(f"archive {a.number}: {a.file} is not an encrypted zip")
        if a.severity.total() != a.advisories:
            errs.append(f"archive {a.number}: severity counts add to {a.severity.total()}, not {a.advisories}")
        if a.with_fix > a.advisories:
            errs.append(f"archive {a.number}: with_fix {a.with_fix} > advisories {a.advisories}")
        if unknown := [g for g in a.published_ids if g not in live]:
            errs.append(f"archive {a.number}: published_ids not published on GitHub: {len(unknown)} id(s)")
    return errs


def quote_line(policy: str, pattern: str) -> int:
    m = re.search(pattern, policy)
    if m is None:
        raise SystemExit(f"security: SECURITY.md no longer says {pattern!r}; update STEPS in tools/security.py")
    return policy.count("\n", 0, m.start()) + 1


def severity_bar(sev: SeverityCounts, label: str, big: bool = False) -> str:
    total = sev.total() or 1
    counts = {"critical": sev.critical, "high": sev.high, "medium": sev.medium, "low": sev.low}
    aria = f"{label}: " + ", ".join(f"{counts[k]} {k}" for k, _ in SEVERITIES)
    segs = "".join(f'<i class="s-{k}" style="flex:{counts[k]} 1 0" title="{n}: {counts[k]}">'
                   f'{counts[k] if big and counts[k] * 100 >= 6 * total else ""}</i>'
                   for k, n in SEVERITIES if counts[k])
    return f'<div class="sevbar{" lg" if big else ""}" role="img" aria-label="{esc(aria)}">{segs}</div>'


def severity_legend(sev: SeverityCounts) -> str:
    total = sev.total() or 1
    counts = {"critical": sev.critical, "high": sev.high, "medium": sev.medium, "low": sev.low}
    return "".join(f'<li class="s-{k}"><i aria-hidden="true"></i><span>{n}</span><b>{counts[k]}</b>'
                   f'<em>{round(100 * counts[k] / total)}%</em></li>' for k, n in SEVERITIES)


def sum_severity(archives: list[DisclosureArchive]) -> SeverityCounts:
    return SeverityCounts(critical=sum(a.severity.critical for a in archives), high=sum(a.severity.high for a in archives),
                          medium=sum(a.severity.medium for a in archives), low=sum(a.severity.low for a in archives))


def render_archive(a: DisclosureArchive) -> str:
    url = f"/{ZIP_DIR}/{a.file}"
    facts = (("Advisories", str(a.advisories)), ("Still embargoed", str(a.embargoed)), ("With a fix", str(a.with_fix)),
             ("Size", human_size(a.size)))
    dl = "".join(f"<div><dt>{k}</dt><dd>{v}</dd></div>" for k, v in facts)
    return f"""<article class="vault plate" id="archive-{a.number}">
<div class="seal"><span class="label">Archive</span><b class="no">{a.number}</b>
<span class="when">cutoff {a.cutoff}<br>sent {a.published}</span><span class="tag cu">AES-256</span></div>
<div class="vbody">
<h3><span class="label">File</span><span class="fn">{esc(a.file)}</span></h3>
<dl class="facts">{dl}</dl>
{severity_bar(a.severity, f"Severity of the {a.advisories} advisories in archive {a.number}")}
<div class="hash"><span class="label">SHA-256</span><code class="sha" id="sha-{a.number}">{a.sha256}</code>
<button class="cp" type="button" data-copy="{a.sha256}" aria-label="Copy the SHA-256 of archive {a.number}">Copy</button></div>
<div class="actions"><a class="btn primary" href="{url}" download>Download archive {a.number} ↓</a>
<span class="muted dlnote">{human_size(a.size)} · encrypted zip · {a.closed_left_out} closed report left out</span></div>
</div></article>"""


def render_open(a: DisclosureArchive) -> str:
    """How to check and open the newest archive: the hash on three systems, then 7-Zip."""
    f = esc(a.file)
    verify = (f'<span class="c"># Linux</span>\nsha256sum {f}\n<span class="c"># macOS</span>\nshasum -a 256 {f}\n'
              f'<span class="c"># Windows (PowerShell)</span>\nGet-FileHash {f}')
    unzip = (f'7z x {f}\n<span class="c"># 7-Zip asks for the password. The OBS Project receives it</span>\n'
             '<span class="c"># on a separate channel; it is not on this site.</span>')
    return (f'<div class="step plate"><span class="label">1 · Verify</span><h3>Check the SHA-256</h3>'
            f'<p class="muted">The output must equal <code>{a.sha256[:12]}…</code>, the full hash on the card above.</p>'
            f'<pre>{verify}</pre></div>'
            f'<div class="step plate"><span class="label">2 · Open</span><h3>Extract with 7-Zip</h3>'
            f'<p class="muted">AES-256 encrypted (WinZip AE-2). One PDF per advisory plus an index.</p>'
            f'<pre>{unzip}</pre></div>')


def render_timeline(data: DisclosureArchives, published: list[GhAdvisory], now: dt.datetime, embargoed: int) -> str:
    events: list[tuple[str, int, str]] = []
    for adv in published:
        date = (adv.published_at or "")[:10]
        sev = adv.severity or "unrated"
        events.append((date, 0, f'<li class="pub"><time datetime="{date}">{date}</time><div><b>Advisory published</b> '
                       f'<a href="{esc(adv.html_url)}">{esc(adv.ghsa_id)}</a> <span class="tag sev s-{sev}">{sev}</span>'
                       f'<p>{esc(adv.summary)}</p></div></li>'))
    for a in data.archives:
        events.append((a.published, 1, f'<li class="arc"><time datetime="{a.published}">{a.published}</time><div>'
                       f'<b>Archive {a.number} sent to the OBS Project</b> <a href="#archive-{a.number}">{a.advisories} advisories</a>'
                       f'<p>Everything reported up to {a.cutoff} and not in an earlier archive.</p></div></li>'))
    events.sort(key=lambda e: (e[0], e[1]))
    today = f"{now:%Y-%m-%d}"
    events.append((today, 2, f'<li class="now"><time datetime="{today}">{today}</time><div><b>Now</b> '
                   f'<span class="muted">{embargoed} advisories embargoed, shared privately with the OBS Project</span></div></li>'))
    return "".join(e[2] for e in events)


def render_advisories(published: list[GhAdvisory]) -> str:
    if not published:
        return '<tr><td colspan="7" class="muted">No advisory is published yet.</td></tr>'
    rows: list[str] = []
    for a in sorted(published, key=lambda x: x.published_at or "", reverse=True):
        sev = a.severity or "unrated"
        score = a.score()
        cve = (f'<a href="https://www.cve.org/CVERecord?id={esc(a.cve_id)}">{esc(a.cve_id)}</a>' if a.cve_id
               else '<span class="muted">not assigned</span>')
        cwe = ", ".join(f'<abbr title="{esc(c.name)}">{esc(c.cwe_id)}</abbr>' for c in a.cwes) or '<span class="muted">—</span>'
        cred = ", ".join(f'<a href="https://github.com/{esc(c.login)}">{esc(c.login)}</a>' for c in a.credits) or "—"
        rows.append(f'<tr><td><a class="ghsa" href="{esc(a.html_url)}">{esc(a.ghsa_id)}</a><p>{esc(a.summary)}</p></td>'
                    f'<td class="cve" data-l="CVE">{cve}</td><td data-l="Severity"><span class="tag sev s-{sev}">{sev}</span></td>'
                    f'<td class="num" data-l="CVSS">{f"{score:.1f}" if score is not None else "—"}</td><td data-l="Weakness">{cwe}</td>'
                    f'<td class="date" data-l="Published">{(a.published_at or "")[:10]}</td><td data-l="Credit">{cred}</td></tr>')
    return "".join(rows)


def build(data: DisclosureArchives, published: list[GhAdvisory], policy: str, root: Path, out: Path,
          obs_sha: str, site_sha: str, now: dt.datetime) -> SecurityPage:
    published = [a for a in published if a.state == "published"]
    errs = check_archives(data, root, published)
    if errs:
        raise SystemExit("security: " + "; ".join(errs))
    if not data.archives:
        raise SystemExit("security: archives.json lists no archive")
    dest = out / ZIP_DIR
    dest.mkdir(parents=True, exist_ok=True)
    for a in data.archives:
        shutil.copyfile(root / ZIP_DIR / a.file, dest / a.file)
    # the published list the page shows, for tools/check.py (the only GHSA ids any page may name)
    listing = PublishedFile(source=f"https://api.github.com/{ADVISORIES_API}", fetched=now.isoformat(timespec="seconds"),
                            published=[PublishedRef(ghsa_id=a.ghsa_id, cve_id=a.cve_id, url=a.html_url) for a in published])
    (out / "security" / "advisories.json").write_text(json.dumps(listing.model_dump(mode="json"), indent=1) + "\n")

    archives = sorted(data.archives, key=lambda a: a.number, reverse=True)
    shared = sum(a.advisories for a in archives)
    in_archive = {g for a in archives for g in a.published_ids}
    reported = shared + sum(1 for a in published if a.ghsa_id not in in_archive)
    embargoed = sum(a.embargoed for a in archives)
    with_fix = sum(a.with_fix for a in archives)
    cutoff = archives[0].cutoff
    sev = sum_severity(archives)

    policy_blob = f"https://github.com/{REPO}/blob/{obs_sha}/SECURITY.md"
    json_blob = f"https://github.com/{SITE_REPO}/blob/{site_sha}/security/archives.json"
    stages = (("Reported", reported, f"private advisories, by {cutoff}", "rep"),
              ("Embargoed", embargoed, "still private today", "emb"),
              ("Sent upstream", shared, "in an encrypted archive", "up"),
              ("Fix prepared", with_fix, "a patch ships in the archive", "fix"),
              ("Published", len(published), "public on GitHub", "pub"))
    pipeline = "".join(f'<li class="stn {cls}"><span class="k">{i:02d}</span><span class="nm">{name}</span>'
                       f'<b>{n}</b><span class="c">{cap}</span></li>' for i, (name, n, cap, cls) in enumerate(stages, 1))
    severity = (severity_bar(sev, f"Severity of the {shared} advisories shared with the OBS Project", big=True)
                + f'<ul class="sevlegend">{severity_legend(sev)}</ul>')
    steps: list[str] = []
    for s in STEPS:
        if s.pattern is None:
            rc = f'<a class="receipt" href="{json_blob}">security/archives.json</a>'
        else:
            line = quote_line(policy, s.pattern)
            rc = f'<a class="receipt" href="{policy_blob}#L{line}">SECURITY.md:{line}</a>'
        steps.append(f'<li class="plate"><span class="k">{s.n}</span><h3>{esc(s.title)}</h3><p>{esc(s.text)}</p>{rc}</li>')
    receipt = (f'Aggregates from <a href="{json_blob}">security/archives.json @ {site_sha[:9]}</a> · '
               f'published advisories from the <a href="https://api.github.com/{ADVISORIES_API}">GitHub advisories API</a>, '
               f'fetched {now:%Y-%m-%d}')
    return SecurityPage(
        sec_reported=reported, sec_embargoed=embargoed, sec_shared=shared, sec_with_fix=with_fix,
        sec_published=len(published), sec_closed=sum(a.closed_left_out for a in archives), sec_cutoff=cutoff,
        sec_pipeline=pipeline, sec_severity=severity, sec_steps="".join(steps),
        sec_timeline=render_timeline(data, published, now, embargoed),
        sec_archives="".join(render_archive(a) for a in archives), sec_open=render_open(archives[0]),
        sec_advisories=render_advisories(published), sec_receipt=receipt,
        sec_report_url=REPORT_URL, sec_policy_url=policy_blob)
