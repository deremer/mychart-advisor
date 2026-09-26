#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pdfplumber>=0.11"]
# ///
"""Extract text from miscellaneous records (medication lists, outside records, discharge papers).

Usage, from the case folder:
    uv run extract_other.py [--root DIR] [--src-dir NAME] [--data-dir DIR] [--backend pdftotext|pdfplumber] [--json]

Writes under the data directory (default <root>/analysis/data):
    other-text/<file>.txt   extracted text of every PDF in the folder
    other-manifest.csv      file, text file, character count, status, first_seen

Images and other non-PDF files are listed for the agent to read directly.

Exit codes: 0 success, 2 folder missing (not an error for a case without other records), 3 no text backend.
"""
import argparse
import csv
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdftext  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--src-dir", default="Other Records")
    ap.add_argument("--data-dir", default=None)
    ap.add_argument("--backend", default=None, choices=["pdftotext", "pdfplumber"])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    src = os.path.join(a.root, a.src_dir)
    if not os.path.isdir(src):
        print(f"No folder at {src}, nothing to extract", file=sys.stderr)
        return 2
    which = pdftext.backend(a.backend)
    if not which:
        print("No PDF text backend. Install poppler (pdftotext) or `pip install pdfplumber`.", file=sys.stderr)
        return 3
    data = a.data_dir or os.path.join(a.root, "analysis", "data")
    txtdir = os.path.join(data, "other-text")
    os.makedirs(txtdir, exist_ok=True)
    run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    mpath = os.path.join(data, "other-manifest.csv")
    first_seen = {}
    if os.path.exists(mpath):
        with open(mpath, newline="") as fh:
            first_seen = {r["file"]: r.get("first_seen") or "earlier run" for r in csv.DictReader(fh)}

    pdfs, other = pdftext.list_files(src)
    names = pdftext.text_names(pdfs)
    rows = []
    for pdf in pdfs:
        base = os.path.basename(pdf)
        text = pdftext.extract(pdf, os.path.join(txtdir, names[pdf]), which)
        chars = pdftext.total_chars(text)
        rows.append({"file": base, "text_file": f"other-text/{names[pdf]}", "chars": chars,
                     "status": "ok" if chars >= 20 else "no-text-layer", "first_seen": first_seen.get(base, run)})
    for p in other:
        base = os.path.basename(p)
        rows.append({"file": base, "text_file": "", "chars": 0, "status": "not-pdf",
                     "first_seen": first_seen.get(base, run)})
    with open(mpath, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["file", "text_file", "chars", "status", "first_seen"], quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

    new = [r for r in rows if r["file"] not in first_seen]
    if a.json:
        print(json.dumps({"files": len(rows), "new": [r["file"] for r in new],
                          "attention": [r for r in rows if r["status"] != "ok"]}, indent=2))
        return 0
    print(f"{len(rows)} other records, {len(new)} new on this run")
    for r in new[:200]:
        print(f"  NEW: {r['file']}")
    for r in rows:
        if r["status"] == "no-text-layer":
            print(f"  NO TEXT LAYER, read the PDF directly or OCR it: {r['file']}")
        elif r["status"] == "not-pdf":
            print(f"  NOT A PDF, read directly: {r['file']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
