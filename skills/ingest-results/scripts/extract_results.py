#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pdfplumber>=0.11"]
# ///
"""Extract text and lab values from patient-portal result PDFs into a case folder's analysis/data.

Usage, from the case folder (the folder with AGENTS.md):
    uv run extract_results.py [--root DIR] [--results-dir NAME] [--data-dir DIR] [--since YYYY-MM-DD]
                              [--portal auto|mychart|generic] [--backend pdftotext|pdfplumber] [--json]

Writes under the data directory (default <root>/analysis/data):
    text/<file>.txt   extracted text of every result PDF
    manifest.csv      one row per PDF: collected, result date, file, text file, character counts, adapter,
                      status, and the run that first saw it
    labs_long.csv     one row per analyte per draw, with unit and parsed reference limits when printed
    labs_wide.csv     analyte by draw time
    labs_trend.md     the same as a markdown table

Prints counts, files first seen on this run (or since --since), and files that need a human or agent to
read them directly: no text layer, no result printed, or lab ranges present but no values parsed.

Exit codes: 0 success (warnings included), 2 results folder missing, 3 no text backend available.
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pdftext  # noqa: E402
import portals  # noqa: E402

# Preferred row order for the trend table: common chemistry, blood counts, coagulation, and inflammatory
# markers. Analytes not listed follow in the order first seen.
ORDER = ["Sodium", "Potassium", "Chloride", "CO2", "Bicarbonate", "Anion Gap", "BUN", "Creatinine", "eGFR",
         "Glucose", "Calcium", "Calcium, Total", "Magnesium", "Phosphorus", "Protein, Total", "Albumin",
         "Bilirubin, Total", "Bilirubin, Direct", "Alkaline Phosphatase", "AST", "ALT", "WBC", "Abs Neut",
         "Abs Lymph", "Abs Mono", "Abs Eosin", "Hemoglobin", "Hematocrit", "RBC", "MCV", "RDW-CV",
         "Platelet Count", "PT Sec", "INR", "APTT", "CRP", "SED RATE", "ESR", "Procalcitonin", "Lactate"]
ALIASES = {"Estimated Glomerular Filtration Rate": "eGFR"}
EMPTY_CONTENT = 3  # alphanumeric characters left after removing header lines and section labels


def split_ref(ref):
    """'136 - 145 mmol/L' -> ('mmol/L', '136', '145'). '<20 Units' -> ('Units', '', '20')."""
    m = re.match(r"^\s*([\d.,]+)\s*(?:-|to)\s*([\d.,]+)\s*(.*)$", ref)
    if m:
        return m.group(3).strip(), m.group(1), m.group(2)
    m = re.match(r"^\s*(<=?|>=?)\s*([\d.,]+)\s*(.*)$", ref)
    if m:
        return (m.group(3).strip(), "", m.group(2)) if m.group(1).startswith("<") else (m.group(3).strip(), m.group(2), "")
    return "", "", ""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.getcwd(), help="case folder, default the working directory")
    ap.add_argument("--results-dir", default="Test Results", help="result PDF folder, relative to root")
    ap.add_argument("--data-dir", default=None, help="output folder, default <root>/analysis/data")
    ap.add_argument("--since", default=None, help="also list files first seen on or after this date, YYYY-MM-DD")
    ap.add_argument("--portal", default="auto", choices=["auto", *portals.ADAPTERS])
    ap.add_argument("--backend", default=None, choices=["pdftotext", "pdfplumber"])
    ap.add_argument("--json", action="store_true", help="print a JSON summary instead of text")
    a = ap.parse_args()

    src = os.path.join(a.root, a.results_dir)
    if not os.path.isdir(src):
        print(f"No results folder at {src}", file=sys.stderr)
        return 2
    which = pdftext.backend(a.backend)
    if not which:
        print("No PDF text backend. Install poppler (pdftotext) or `pip install pdfplumber`.", file=sys.stderr)
        return 3
    data = a.data_dir or os.path.join(a.root, "analysis", "data")
    txtdir = os.path.join(data, "text")
    os.makedirs(txtdir, exist_ok=True)
    run = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    mpath = os.path.join(data, "manifest.csv")
    first_seen = {}
    if os.path.exists(mpath):
        with open(mpath, newline="") as fh:
            for r in csv.DictReader(fh):
                first_seen[r["file"]] = r.get("first_seen") or "earlier run"

    pdfs, other = pdftext.list_files(src)
    names = pdftext.text_names(pdfs)
    manifest, rows, attention = [], [], []
    for pdf in pdfs:
        base = os.path.basename(pdf)
        tfile = names[pdf]
        text = pdftext.extract(pdf, os.path.join(txtdir, tfile), which)
        adapter = portals.pick(text, a.portal)
        coll, res = adapter.result_header(text)
        total, content = pdftext.total_chars(text), pdftext.content_chars(text)
        status = "ok"
        if total < 20:
            status = "no-text-layer"
        elif content < EMPTY_CONTENT:
            status = "no-result-printed"
        parsed, note = adapter.parse_labs(pdf, text) if status == "ok" else ([], "")
        if status == "ok" and note:
            status = "labs-not-parsed"
        elif status == "ok" and adapter is portals.mychart and adapter.has_labs(text) and not parsed:
            status = "labs-not-parsed"
        if status != "ok":
            attention.append((status, base, note))
        manifest.append({"collected": coll, "result_date": res, "file": base, "text_file": f"text/{tfile}",
                         "chars": total, "content_chars": content, "adapter": adapter.NAME, "status": status,
                         "lab_values": len(parsed), "first_seen": first_seen.get(base, run)})
        for name, value, flag, ref, page in parsed:
            unit, lo, hi = split_ref(ref)
            rows.append({"collected": coll, "analyte": ALIASES.get(name, name), "value": value, "flag": flag,
                         "ref": ref, "unit": unit, "ref_low": lo, "ref_high": hi, "page": page, "file": base})

    def when(s):
        return portals.mychart.parse_time(s) or portals.generic.parse_time(s) or datetime.max

    manifest.sort(key=lambda r: (when(r["collected"]), r["file"]))
    with open(mpath, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(manifest[0]) if manifest else ["file"], quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(manifest)

    rows.sort(key=lambda r: (when(r["collected"]), r["file"]))
    fields = ["collected", "analyte", "value", "flag", "ref", "unit", "ref_low", "ref_high", "page", "file"]
    with open(os.path.join(data, "labs_long.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    draws = sorted({r["collected"] for r in rows}, key=when)
    piv = defaultdict(dict)
    for r in rows:
        piv[r["analyte"]][r["collected"]] = r
    analytes = [n for n in ORDER if n in piv] + [n for n in dict.fromkeys(r["analyte"] for r in rows) if n not in ORDER]
    cols = [when(d).strftime("%m/%d %H:%M") if when(d) != datetime.max else (d or "no date") for d in draws]
    md = ["# Serial labs by draw time", "",
          "Generated by the ingest-results extractor. Asterisk marks a lab flag. Blank means not drawn or not "
          "reported. Mechanical extraction: verify any value you cite against the source PDF.", "",
          "| Analyte | Ref | " + " | ".join(cols) + " |", "|---|---|" + "---|" * len(cols)]
    wide = [["analyte", "ref"] + cols]
    for n in analytes:
        ref = next(iter(piv[n].values()))["ref"]
        cells = [(piv[n][d]["value"] + ("*" if piv[n][d]["flag"] else "")) if d in piv[n] else "" for d in draws]
        md.append(f"| {n} | {ref} | " + " | ".join(cells) + " |")
        wide.append([n, ref] + cells)
    with open(os.path.join(data, "labs_trend.md"), "w") as fh:
        fh.write("\n".join(md) + "\n")
    with open(os.path.join(data, "labs_wide.csv"), "w", newline="") as fh:
        csv.writer(fh).writerows(wide)

    new = [m for m in manifest if m["file"] not in first_seen]
    since = []
    if a.since:
        since = [m for m in manifest if m["file"] in first_seen and re.match(r"\d{4}-\d{2}-\d{2}", m["first_seen"])
                 and m["first_seen"][:10] >= a.since]
    summary = {"backend": which, "pdfs": len(manifest), "lab_values": len(rows), "text_files": len(os.listdir(txtdir)),
               "new": [m["file"] for m in new], "since": [m["file"] for m in since],
               "attention": [{"status": s, "file": f, "note": n} for s, f, n in attention],
               "not_pdf": [os.path.basename(p) for p in other]}
    if a.json:
        print(json.dumps(summary, indent=2))
        return 0
    print(f"{len(manifest)} result PDFs, {len(rows)} lab values, {len(new)} new on this run (text backend: {which})")
    for m in new[:200]:
        print(f"  NEW: {m['collected'] or 'no collection time'} | {m['file']}")
    if len(new) > 200:
        print(f"  ... {len(new) - 200} more, see manifest.csv")
    if a.since:
        print(f"{len(since)} earlier files first seen since {a.since}:")
        for m in since[:200]:
            print(f"  SINCE: {m['first_seen']} | {m['collected']} | {m['file']}")
    labels = {"no-text-layer": "NO TEXT LAYER, read the PDF directly or OCR it",
              "no-result-printed": "NO RESULT PRINTED, confirm by reading the PDF",
              "labs-not-parsed": "LAB RANGES BUT NO VALUES PARSED, read by hand"}
    for status, f, note in attention:
        print(f"  {labels[status]}: {f}" + (f" ({note})" if note else ""))
    for p in other:
        print(f"  NOT A PDF, read directly: {os.path.basename(p)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
