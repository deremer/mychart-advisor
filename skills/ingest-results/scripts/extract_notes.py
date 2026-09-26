#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pdfplumber>=0.11"]
# ///
"""Extract text and a manifest from patient-portal care team note PDFs into a case folder's analysis/data.

Usage, from the case folder (the folder with AGENTS.md):
    uv run extract_notes.py [--root DIR] [--notes-dir NAME] [--data-dir DIR] [--since YYYY-MM-DD]
                            [--portal auto|mychart|generic] [--backend pdftotext|pdfplumber] [--json]

Writes under the data directory (default <root>/analysis/data):
    notes-text/<file>.txt   extracted text of every note PDF
    notes-manifest.csv      one row per note: service time, note type, author, credential, file, text file,
                            character count, where the metadata came from, and the run that first saw it

Reads, if present:
    notes-overrides.csv     corrections for notes whose file name does not match their content.
                            Columns: file, service_time (YYYY-MM-DD HH:MM), note_type, author, credential.
                            The file column matches the name with surrounding spaces removed.

The service time in a portal file name is the time the portal lists. The note body may carry a different
date of service or signed time. When they disagree, the body wins, and the fix goes in notes-overrides.csv.

Exit codes: 0 success (warnings included), 2 notes folder missing, 3 no text backend available.
"""
import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdftext  # noqa: E402
import portals  # noqa: E402


def load_overrides(path):
    out = {}
    if os.path.exists(path):
        with open(path, newline="") as fh:
            for r in csv.DictReader(fh):
                out[r["file"].strip()] = (r["service_time"], r["note_type"], r["author"], r.get("credential", ""))
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.getcwd(), help="case folder, default the working directory")
    ap.add_argument("--notes-dir", default="Care Team Notes", help="note PDF folder, relative to root")
    ap.add_argument("--data-dir", default=None, help="output folder, default <root>/analysis/data")
    ap.add_argument("--since", default=None, help="also list files first seen on or after this date, YYYY-MM-DD")
    ap.add_argument("--portal", default="auto", choices=["auto", *portals.ADAPTERS])
    ap.add_argument("--backend", default=None, choices=["pdftotext", "pdfplumber"])
    ap.add_argument("--json", action="store_true", help="print a JSON summary instead of text")
    a = ap.parse_args()

    src = os.path.join(a.root, a.notes_dir)
    if not os.path.isdir(src):
        print(f"No notes folder at {src}", file=sys.stderr)
        return 2
    which = pdftext.backend(a.backend)
    if not which:
        print("No PDF text backend. Install poppler (pdftotext) or `pip install pdfplumber`.", file=sys.stderr)
        return 3
    data = a.data_dir or os.path.join(a.root, "analysis", "data")
    txtdir = os.path.join(data, "notes-text")
    os.makedirs(txtdir, exist_ok=True)
    run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    overrides = load_overrides(os.path.join(data, "notes-overrides.csv"))

    mpath = os.path.join(data, "notes-manifest.csv")
    first_seen = {}
    if os.path.exists(mpath):
        with open(mpath, newline="") as fh:
            for r in csv.DictReader(fh):
                first_seen[r["file"]] = r.get("first_seen") or "earlier run"

    pdfs, other = pdftext.list_files(src)
    names = pdftext.text_names(pdfs)
    rows, empty = [], []
    for pdf in pdfs:
        base = os.path.basename(pdf)
        tfile = names[pdf]
        text = pdftext.extract(pdf, os.path.join(txtdir, tfile), which)
        chars = pdftext.total_chars(text)
        if chars < 20:
            empty.append(base)
        adapter = portals.ADAPTERS["mychart"] if a.portal == "auto" else portals.ADAPTERS[a.portal]
        parsed = adapter.parse_note_name(base)
        if base.strip() in overrides:
            when, ntype, author, cred = overrides[base.strip()]
            source = "override"
        elif parsed:
            when, ntype, author, cred = parsed
            source = "file name"
        else:
            when, ntype, author, cred = "", "UNPARSED", "", ""
            source = "unparsed"
        rows.append({"service_time": when, "note_type": ntype, "author": author, "credential": cred, "file": base,
                     "text_file": f"notes-text/{tfile}", "chars": chars, "metadata_from": source,
                     "first_seen": first_seen.get(base, run)})

    rows.sort(key=lambda r: (r["service_time"] or "9999", r["file"].strip()))
    with open(mpath, "w", newline="") as fh:
        fields = ["service_time", "note_type", "author", "credential", "file", "text_file", "chars",
                  "metadata_from", "first_seen"]
        w = csv.DictWriter(fh, fieldnames=fields, quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(rows)

    unparsed = [r["file"] for r in rows if r["metadata_from"] == "unparsed"]
    new = [r for r in rows if r["file"] not in first_seen]
    since = []
    if a.since:
        since = [r for r in rows if r["file"] in first_seen and re.match(r"\d{4}-\d{2}-\d{2}", r["first_seen"])
                 and r["first_seen"][:10] >= a.since]
    summary = {"backend": which, "notes": len(rows), "text_files": len(os.listdir(txtdir)),
               "new": [r["file"] for r in new], "since": [r["file"] for r in since], "unparsed": unparsed,
               "no_text_layer": empty, "not_pdf": [os.path.basename(p) for p in other]}
    if a.json:
        print(json.dumps(summary, indent=2))
        return 0
    print(f"{len(rows)} notes, {len(unparsed)} unparsed names, {len(new)} new on this run (text backend: {which})")
    for f in unparsed:
        print(f"  UNPARSED NAME, read the note and add a row to notes-overrides.csv: {f}")
    for r in new[:200]:
        print(f"  NEW: {r['service_time'] or 'no service time'} | {r['file']}")
    if len(new) > 200:
        print(f"  ... {len(new) - 200} more, see notes-manifest.csv")
    if a.since:
        print(f"{len(since)} earlier notes first seen since {a.since}:")
        for r in since[:200]:
            print(f"  SINCE: {r['first_seen']} | {r['service_time']} | {r['file']}")
    for f in empty:
        print(f"  NO TEXT LAYER, read the PDF directly or OCR it: {f}")
    for p in other:
        print(f"  NOT A PDF, read directly: {os.path.basename(p)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
