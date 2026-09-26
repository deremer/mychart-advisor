#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Freeze a read-only snapshot of a case folder's primary record text for a blinded consult.

Usage, from the case folder:
    python3 build_snapshot.py [--root DIR] [--out DIR] [--family-observations FILE] [--no-redact] [--json]

The snapshot holds only primary material: extracted text of every result, note, and other record, the
manifests, the mechanical lab table, and optionally a sanitized family-observations file the user approved.
It never holds summaries, indexes, change notes, conference notes, question sheets, or the case AGENTS.md.

By default every entry in .advisor/identifiers.txt (4+ characters) is replaced in the copied text with a
stable token such as [ID-3], so a blind agent cannot leak it into a web search. File names are unchanged
so citations still map to the original PDFs.

Writes into --out (default consult/<today>/snapshot):
    AGENTS.md              blind rules (copied from references/rules-blind.md)
    _method/               role prompts, schemas, taxonomy, report template, for a separate blind session
    work/                  empty, receives blind-stage outputs
    SNAPSHOT.md            what is here and what is not
    INDEX.csv              every record: kind, time, file, text path, status, sorted by time
    text/ notes-text/ other-text/
    manifest.csv notes-manifest.csv other-manifest.csv labs_long.csv
    family-observations.md (if given)
    snapshot.json          source PDF list with sizes and SHA-256, for diff_snapshot.py

Exit codes: 0 success, 2 case not ingested or counts do not match, 3 output exists (pass a new --out).
"""
import argparse
import csv
import datetime
import hashlib
import json
import os
import re
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REFS = os.path.join(os.path.dirname(HERE), "references")
RULES = os.path.join(REFS, "rules-blind.md")
METHOD = ["roles.md", "schemas.md", "family-taxonomy.md", "report-template.md", "lessons.md"]
SOURCES = [("result", "Test Results", "manifest.csv", "text"),
           ("note", "Care Team Notes", "notes-manifest.csv", "notes-text"),
           ("other", "Other Records", "other-manifest.csv", "other-text")]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_identifiers(root):
    path = os.path.join(root, ".advisor", "identifiers.txt")
    if not os.path.exists(path):
        return []
    with open(path, encoding="utf-8") as fh:
        ids = [ln.strip() for ln in fh if len(ln.strip()) >= 4 and not ln.startswith("#")]
    return sorted(set(ids), key=len, reverse=True)


def redactor(ids):
    if not ids:
        return lambda s: (s, 0)
    tokens = {i.lower(): f"[ID-{n}]" for n, i in enumerate(ids, 1)}
    pat = re.compile("|".join(r"(?<!\w)" + re.escape(i) + r"(?!\w)" for i in ids), re.IGNORECASE)

    def sub(text):
        count = [0]

        def rep(m):
            count[0] += 1
            return tokens[m.group(0).lower()]
        return pat.sub(rep, text), count[0]
    return sub


def iso(s):
    for fmt in ("%b %d, %Y %I:%M %p", "%Y-%m-%d %H:%M", "%m/%d/%Y %I:%M %p"):
        try:
            return datetime.datetime.strptime(s.strip(), fmt).strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            continue
    return ""


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--out", default=None)
    ap.add_argument("--family-observations", default=None, help="sanitized observations file the user approved")
    ap.add_argument("--no-redact", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    root = os.path.abspath(a.root)
    data = os.path.join(root, "analysis", "data")
    today = datetime.date.today().isoformat()
    out = os.path.abspath(a.out or os.path.join(root, "consult", today, "snapshot"))
    if os.path.exists(out) and os.listdir(out):
        print(f"{out} already exists. Pass a new --out.", file=sys.stderr)
        return 3

    problems, sources = [], []
    for kind, folder, manifest, textdir in SOURCES:
        src = os.path.join(root, folder)
        mpath = os.path.join(data, manifest)
        pdfs = []
        if os.path.isdir(src):
            pdfs = [f for f in os.listdir(src) if os.path.isfile(os.path.join(src, f)) and not f.startswith(".")]
        if not pdfs:
            continue
        if not os.path.exists(mpath):
            problems.append(f"{folder} has {len(pdfs)} files but {manifest} is missing. Run ingest-results first.")
            continue
        with open(mpath, newline="") as fh:
            rows = list(csv.DictReader(fh))
        if len(rows) != len(pdfs):
            problems.append(f"{folder}: {len(pdfs)} files on disk, {len(rows)} in {manifest}. Run ingest-results first.")
        sources.append((kind, folder, manifest, textdir, rows))
    if problems:
        for p in problems:
            print(p, file=sys.stderr)
        return 2
    if not sources:
        print("No records found. Add PDFs and run ingest-results first.", file=sys.stderr)
        return 2

    redact = redactor([] if a.no_redact else load_identifiers(root))
    os.makedirs(out, exist_ok=True)
    index, files, redactions = [], [], 0
    for kind, folder, manifest, textdir, rows in sources:
        os.makedirs(os.path.join(out, textdir), exist_ok=True)
        shutil.copy2(os.path.join(data, manifest), os.path.join(out, manifest))
        for r in rows:
            src_txt = os.path.join(data, r["text_file"]) if r.get("text_file") else ""
            rel = r.get("text_file", "")
            if src_txt and os.path.exists(src_txt):
                with open(src_txt, encoding="utf-8", errors="ignore") as fh:
                    text, n = redact(fh.read())
                redactions += n
                with open(os.path.join(out, rel), "w", encoding="utf-8") as fh:
                    fh.write(text)
            when = iso(r.get("collected", "")) if kind == "result" else r.get("service_time", "")
            index.append({"kind": kind, "time": when, "file": r["file"], "folder": folder, "text_file": rel,
                          "status": r.get("status", r.get("metadata_from", ""))})
            pdf = os.path.join(root, folder, r["file"])
            if os.path.exists(pdf):
                files.append({"folder": folder, "file": r["file"], "bytes": os.path.getsize(pdf), "sha256": sha256(pdf)})
    labs = os.path.join(data, "labs_long.csv")
    if os.path.exists(labs):
        shutil.copy2(labs, os.path.join(out, "labs_long.csv"))
    if a.family_observations:
        with open(a.family_observations, encoding="utf-8") as fh:
            text, n = redact(fh.read())
        redactions += n
        with open(os.path.join(out, "family-observations.md"), "w", encoding="utf-8") as fh:
            fh.write(text)
    shutil.copy2(RULES, os.path.join(out, "AGENTS.md"))
    os.makedirs(os.path.join(out, "_method"), exist_ok=True)
    os.makedirs(os.path.join(out, "work"), exist_ok=True)
    for name in METHOD:
        shutil.copy2(os.path.join(REFS, name), os.path.join(out, "_method", name))

    index.sort(key=lambda r: (r["time"] or "9999", r["kind"], r["file"]))
    with open(os.path.join(out, "INDEX.csv"), "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["kind", "time", "file", "folder", "text_file", "status"], quoting=csv.QUOTE_ALL)
        w.writeheader()
        w.writerows(index)
    counts = {k: sum(1 for r in index if r["kind"] == k) for k in ("result", "note", "other")}
    with open(os.path.join(out, "SNAPSHOT.md"), "w", encoding="utf-8") as fh:
        fh.write(
            f"# Snapshot, frozen {datetime.datetime.now():%Y-%m-%d %H:%M}\n\n"
            f"{counts['result']} results, {counts['note']} notes, {counts['other']} other records.\n\n"
            "Contents: extracted text of every released record (`text/`, `notes-text/`, `other-text/`), their "
            "manifests, `INDEX.csv` sorted by time, and `labs_long.csv`. The lab table is a mechanical extraction, "
            "so check the text file before relying on a number.\n\n"
            + ("`family-observations.md` holds the family's observations, sanitized to observation only and "
               "approved by the user. Cite it as family report.\n\n" if a.family_observations else "")
            + "Not here, on purpose: any summary, index, interpretation, or prior analysis of this case. Also not "
            "here: the medication administration record, vital-sign flowsheets, the images themselves, pathology "
            "slides, outside records not downloaded, and the patient.\n\n"
            + ("Identifiers from the case folder are replaced with tokens such as [ID-3]. The same token always "
               "means the same person or place.\n" if redactions else ""))
    snap = {"created": datetime.datetime.now().isoformat(timespec="seconds"), "root": root, "files": files,
            "counts": counts, "redactions": redactions}
    with open(os.path.join(out, "snapshot.json"), "w") as fh:
        json.dump(snap, fh, indent=2)

    if a.json:
        print(json.dumps({"out": out, "counts": counts, "redactions": redactions}, indent=2))
    else:
        print(f"Snapshot at {out}: {counts['result']} results, {counts['note']} notes, {counts['other']} other, "
              f"{redactions} identifier redactions")
    return 0


if __name__ == "__main__":
    sys.exit(main())
