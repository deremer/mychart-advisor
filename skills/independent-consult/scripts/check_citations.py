#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Check numbered-citation integrity in a markdown report.

Usage:
    python3 check_citations.py FILE.md [--json]

A citation scope runs from the start of the file, or the end of the previous sources list, to a heading
whose text ends in "Sources" (any level). Within each scope, every bracketed number such as [3] or [3, 7]
must have a numbered entry in the sources list, and every entry must be cited at least once. Entries
should be numbered 1..N without gaps. Code blocks and markdown links are ignored.

Exit codes: 0 clean, 1 problems found, 2 unreadable file.
"""
import argparse
import json
import re
import sys

CITE = re.compile(r"\[(\d+(?:\s*[,–-]\s*\d+)*)\](?!\()")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
ENTRY = re.compile(r"^\s*(\d+)\.\s+\S")


def expand(group):
    nums = set()
    for part in re.split(r"\s*,\s*", group):
        if re.search(r"[–-]", part):
            a, b = [int(x) for x in re.split(r"\s*[–-]\s*", part)]
            nums.update(range(a, b + 1))
        else:
            nums.add(int(part))
    return nums


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    try:
        with open(a.file, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 2

    scopes, body, entries, in_sources, fence = [], [], {}, False, False
    for n, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            fence = not fence
            continue
        if fence:
            continue
        h = HEADING.match(line)
        if h:
            if in_sources:
                scopes.append((body, entries))
                body, entries, in_sources = [], {}, False
            if h.group(2).rstrip(":").lower().endswith("sources"):
                in_sources = True
                continue
        if in_sources:
            m = ENTRY.match(line)
            if m:
                entries[int(m.group(1))] = n
        else:
            body.append((n, line))
    if in_sources:
        scopes.append((body, entries))
    elif body and any(CITE.search(l) for _, l in body):
        scopes.append((body, {}))

    problems = []
    for i, (body, entries) in enumerate(scopes, 1):
        cited, first_order = {}, []
        for n, line in body:
            for m in CITE.finditer(line):
                for num in sorted(expand(m.group(1))):
                    cited.setdefault(num, n)
                    if num not in first_order:
                        first_order.append(num)
        for num, ln in sorted(cited.items()):
            if num not in entries:
                problems.append(f"scope {i}: [{num}] cited at line {ln} has no sources entry")
        for num, ln in sorted(entries.items()):
            if num not in cited:
                problems.append(f"scope {i}: sources entry {num} (line {ln}) is never cited")
        if entries and sorted(entries) != list(range(1, max(entries) + 1)):
            problems.append(f"scope {i}: sources are not numbered 1..{max(entries)} without gaps")
        if first_order and first_order != sorted(first_order):
            problems.append(f"scope {i}: sources are not numbered in order of first citation (warning)")

    errors = [p for p in problems if not p.endswith("(warning)")]
    if a.json:
        print(json.dumps({"scopes": len(scopes), "problems": problems}, indent=2))
    else:
        print(f"{len(scopes)} citation scope(s), {len(errors)} error(s), {len(problems) - len(errors)} warning(s)")
        for p in problems:
            print("  " + p)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
