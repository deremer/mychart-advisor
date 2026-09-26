#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""List records in the case folder that are new, changed, or gone since a consult snapshot was frozen.

Usage:
    python3 diff_snapshot.py --snapshot consult/<date>/snapshot [--root DIR] [--json]

Exit codes: 0 no differences, 1 differences found, 2 snapshot.json missing.
"""
import argparse
import hashlib
import json
import os
import sys

FOLDERS = ["Test Results", "Care Team Notes", "Other Records"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    path = os.path.join(a.snapshot, "snapshot.json")
    if not os.path.exists(path):
        print(f"No snapshot.json in {a.snapshot}", file=sys.stderr)
        return 2
    with open(path) as fh:
        snap = json.load(fh)
    before = {(f["folder"], f["file"]): f["sha256"] for f in snap["files"]}
    now = {}
    for folder in FOLDERS:
        src = os.path.join(a.root, folder)
        if os.path.isdir(src):
            for name in os.listdir(src):
                p = os.path.join(src, name)
                if os.path.isfile(p) and not name.startswith("."):
                    now[(folder, name)] = sha256(p)
    new = sorted(k for k in now if k not in before)
    gone = sorted(k for k in before if k not in now)
    changed = sorted(k for k in now if k in before and now[k] != before[k])
    result = {"snapshot_created": snap["created"], "new": [f"{d}/{f}" for d, f in new],
              "changed": [f"{d}/{f}" for d, f in changed], "gone": [f"{d}/{f}" for d, f in gone]}
    if a.json:
        print(json.dumps(result, indent=2))
    else:
        print(f"Since snapshot {snap['created']}: {len(new)} new, {len(changed)} changed, {len(gone)} gone")
        for label in ("new", "changed", "gone"):
            for f in result[label]:
                print(f"  {label.upper()}: {f}")
    return 1 if (new or changed or gone) else 0


if __name__ == "__main__":
    sys.exit(main())
