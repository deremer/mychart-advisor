#!/usr/bin/env python3
"""Report word sequences shared between tracked files and a private reference folder.

Usage: python3 scripts/dev/overlap_check.py <reference_dir> [--n 8]

Maintainers run this against private reference material (for example docs/input/) before publishing, to
catch phrasing carried over by accident. It prints matching sequences with file names. It never writes.
"""
import argparse
import os
import re
import subprocess


def words(text):
    return re.findall(r"[a-z0-9']+", text.lower())


def shingles(ws, n):
    return {" ".join(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("reference")
    ap.add_argument("--n", type=int, default=8)
    a = ap.parse_args()
    ref = {}
    for root, _, files in os.walk(a.reference):
        for f in files:
            if f.endswith((".md", ".py", ".txt", ".json", ".yaml")):
                with open(os.path.join(root, f), errors="ignore") as fh:
                    for s in shingles(words(fh.read()), a.n):
                        ref.setdefault(s, os.path.relpath(os.path.join(root, f), a.reference))
    tracked = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout.split("\n")
    hits = 0
    for f in tracked:
        if not f or f.endswith((".pdf", ".PDF")) or not os.path.isfile(f):
            continue
        with open(f, errors="ignore") as fh:
            common = shingles(words(fh.read()), a.n) & ref.keys()
        for s in sorted(common):
            print(f"{f}  <->  {ref[s]}:  {s}")
            hits += 1
    print(f"{hits} shared {a.n}-word sequences")


if __name__ == "__main__":
    main()
