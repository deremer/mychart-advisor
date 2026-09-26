#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Create or repair a mychart-advisor case folder. Never overwrites an existing file.

Usage:
    python3 scaffold.py --root CASE_DIR [--facts facts.json] [--dry-run] [--json]

facts.json is a flat object whose keys fill the {{PLACEHOLDERS}} in the templates:
    PATIENT_LABEL, AGE, RELATIONSHIP, SETTING, FACILITY, START_DATE, REASON, ATTENDING, OUTPATIENT, PORTAL
Missing keys become "not given". TODAY is filled automatically.

Folder structure and the starting content of every derived file come from assets/case-folder-layout.md,
so that file is the single source of truth for the layout.

Prints what it created and what already existed. Exit codes: 0 success, 2 bad arguments or unreadable facts.
"""
import argparse
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.join(os.path.dirname(HERE), "assets")
KEYS = ["PATIENT_LABEL", "AGE", "RELATIONSHIP", "SETTING", "FACILITY", "START_DATE", "REASON", "ATTENDING",
        "OUTPATIENT", "PORTAL"]


def read(name):
    with open(os.path.join(ASSETS, name), encoding="utf-8") as fh:
        return fh.read()


def parse_layout(md):
    """Return (dirs, files) from the layout document. dirs is a list of relative paths. files maps a
    relative path to its starting content, taken from the first fenced block under a '## <path>' heading.
    Headings inside fenced blocks are content, not section breaks."""
    sections, current, in_fence = {}, None, False
    for line in md.splitlines(keepends=True):
        if line.startswith("```"):
            in_fence = not in_fence
        elif not in_fence and line.startswith("## "):
            current = line[3:].strip()
            sections[current] = ""
            continue
        if current is not None:
            sections[current] += line
        else:
            sections.setdefault("", "")
            sections[""] += line

    def first_block(text):
        m = re.search(r"^```[^\n]*\n(.*?)^```", text, re.DOTALL | re.MULTILINE)
        return m.group(1) if m else None

    tree = first_block(sections[""]).splitlines()[1:]
    dirs, stack = [], []
    for line in tree:
        if not line.strip():
            continue
        name = re.split(r"\s{2,}", line.strip())[0]
        depth = (len(line) - len(line.lstrip(" "))) // 2 - 1
        stack = stack[:depth]
        if name.endswith("/"):
            stack.append(name.rstrip("/"))
            dirs.append("/".join(stack))
    files = {}
    for heading, body in sections.items():
        if re.match(r"^(notes|analysis)/[^\s<]+\.(md|csv)$", heading):
            block = first_block(body)
            if block is not None:
                files[heading] = block
    return dirs, files


def fill(template, facts):
    values = {k: (str(facts.get(k) or "").strip() or "not given") for k in KEYS}
    values["TODAY"] = datetime.date.today().isoformat()
    return re.sub(r"\{\{(\w+)\}\}", lambda m: values.get(m.group(1), m.group(0)), template)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", required=True, help="case folder to create or repair")
    ap.add_argument("--facts", help="JSON file of template values")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    facts = {}
    if a.facts:
        try:
            with open(a.facts, encoding="utf-8") as fh:
                facts = json.load(fh)
        except (OSError, ValueError) as exc:
            print(f"Cannot read facts: {exc}", file=sys.stderr)
            return 2

    dirs, files = parse_layout(read("case-folder-layout.md"))
    files = {
        "AGENTS.md": fill(read("case-AGENTS.template.md"), facts),
        "CLAUDE.md": "@AGENTS.md\n",
        "START-HERE.md": fill(read("START-HERE.template.md"), facts),
        ".advisor/identifiers.txt": "",
        **files,
    }
    created, existing = [], []
    for d in dirs:
        path = os.path.join(a.root, d)
        (existing if os.path.isdir(path) else created).append(d + "/")
        if not a.dry_run:
            os.makedirs(path, exist_ok=True)
    for rel, content in files.items():
        path = os.path.join(a.root, rel)
        if os.path.exists(path):
            existing.append(rel)
            continue
        created.append(rel)
        if not a.dry_run:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(content)

    if a.json:
        print(json.dumps({"root": os.path.abspath(a.root), "created": created, "existing": existing}, indent=2))
    else:
        verb = "Would create" if a.dry_run else "Created"
        print(f"{verb} {len(created)} paths, {len(existing)} already present in {os.path.abspath(a.root)}")
        for p in created:
            print(f"  + {p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
