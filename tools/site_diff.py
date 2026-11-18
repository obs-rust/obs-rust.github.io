#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = []
# ///
"""Compare two built sites byte for byte, ignoring build timestamps.

Usage: uv run tools/site_diff.py BASELINE_SITE NEW_SITE [--ignore-dates]

The "generated" ISO timestamp in ai/corpus.json and mcp/schema.json is always normalized.
--ignore-dates also normalizes bare YYYY-MM-DD dates (build date in the footer, sitemap
lastmod, llms*.txt headers), for comparing builds made on different days.
Exits 1 if any file is missing on one side or differs after normalization.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

GENERATED = re.compile(rb'"generated":( ?)"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[^"]*"')
DATE = re.compile(rb"\b\d{4}-\d{2}-\d{2}\b")
TIMESTAMPED = {"ai/corpus.json", "mcp/schema.json"}


@dataclass(frozen=True, slots=True)
class Args:
    baseline: Path
    new: Path
    ignore_dates: bool


@dataclass(frozen=True, slots=True)
class Report:
    compared: int
    normalized: list[str]
    only_baseline: list[str]
    only_new: list[str]
    differing: list[str]

    @property
    def ok(self) -> bool:
        return not (self.only_baseline or self.only_new or self.differing)


def files(root: Path) -> set[str]:
    return {str(p.relative_to(root)) for p in root.rglob("*") if p.is_file()}


def normalize(rel: str, data: bytes, ignore_dates: bool) -> bytes:
    if rel in TIMESTAMPED:
        data = GENERATED.sub(rb'"generated":\1"<timestamp>"', data)
    if ignore_dates:
        data = DATE.sub(b"<date>", data)
    return data


def compare(a: Args) -> Report:
    base, new = files(a.baseline), files(a.new)
    normalized: list[str] = []
    differing: list[str] = []
    for rel in sorted(base & new):
        x, y = (a.baseline / rel).read_bytes(), (a.new / rel).read_bytes()
        if x == y:
            continue
        if normalize(rel, x, a.ignore_dates) == normalize(rel, y, a.ignore_dates):
            normalized.append(rel)
        else:
            differing.append(rel)
    return Report(compared=len(base & new), normalized=normalized, only_baseline=sorted(base - new),
                  only_new=sorted(new - base), differing=differing)


def parse_args() -> Args:
    ap = argparse.ArgumentParser()
    ap.add_argument("baseline", type=Path)
    ap.add_argument("new", type=Path)
    ap.add_argument("--ignore-dates", action="store_true")
    ns = ap.parse_args()
    return Args(baseline=Path(ns.baseline), new=Path(ns.new), ignore_dates=bool(ns.ignore_dates))


def main() -> int:
    r = compare(parse_args())
    for label, items in (("only in baseline", r.only_baseline), ("only in new", r.only_new),
                         ("DIFFERS", r.differing), ("equal after timestamp normalization", r.normalized)):
        for rel in items:
            print(f"{label}: {rel}")
    print(f"site_diff: {r.compared} files compared, {len(r.differing)} differing, "
          f"{len(r.only_baseline) + len(r.only_new)} missing on one side, {len(r.normalized)} equal only after "
          f"normalizing timestamps")
    return 0 if r.ok else 1


if __name__ == "__main__":
    sys.exit(main())
