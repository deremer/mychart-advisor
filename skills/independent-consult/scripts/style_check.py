#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Scan a report for treatment directives and diagnoses stated as fact, plus optional house-style rules.

Usage:
    python3 style_check.py FILE.md [--strict] [--banned FILE] [--json]

Always checks:
  - treatment directives ("stop taking", "you should start", "increase the dose", "we recommend treatment")
  - a diagnosis stated as fact ("the patient has <condition>")
Possible diagnoses worded as "consistent with", "argues for", or "ask whether" are expected and never flagged.

--strict also flags em dashes, semicolons, and any word or phrase listed one per line in --banned.

Exit codes: 0 clean, 1 findings. Findings are for a human or agent to rewrite, as questions for the team.
"""
import argparse
import json
import re
import sys

VERBS = r"(?:start|stop|begin|discontinue|hold|increase|decrease|raise|lower|double|halve|change|switch|give|take|prescribe|order|add|remove)"
DIRECTIVES = [
    (r"\b(?:you|the team|they|doctors?|physicians?|the family)\s+(?:should|must|need to|ought to|have to)\s+" + VERBS + r"\b",
     "directive to act"),
    (r"\bstop taking\b|\bstart taking\b", "medication directive"),
    (r"\b(?:increase|decrease|raise|lower|double|halve)\s+(?:the|his|her|their)?\s*dose\b", "dosing directive"),
    (r"\b(?:we|I)\s+recommend\s+(?:starting|stopping|treating|treatment|therapy|a course|surgery|the drug)", "treatment recommendation"),
    (r"^\s*(?:[-*]\s*)?(?:Start|Stop|Discontinue|Increase|Decrease|Give|Prescribe)\s+(?:the\s+)?[a-z]", "imperative directive"),
]
FACT_DX = [
    (r"\b(?:the patient|he|she|they|[A-Z][a-z]+)\s+(?:has|have|is suffering from)\s+(?!been\b|had\b|not\b|no\b|a history\b|received\b|a\s+(?:normal|negative)\b)"
     r"(?:[a-z-]+\s+){0,3}(?:disease|syndrome|cancer|carcinoma|lymphoma|leukemia|infection|hepatitis|failure|thrombosis|sepsis|tumou?r)\b",
     "diagnosis stated as fact"),
    (r"\bthe diagnosis is\b|\bdiagnosed with\b(?![^.]*\b(?:by|per|according to)\b)", "diagnosis asserted (check it is attributed to the team)"),
]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--banned", default=None)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    with open(a.file, encoding="utf-8") as fh:
        lines = fh.read().splitlines()
    banned = []
    if a.banned:
        with open(a.banned, encoding="utf-8") as fh:
            banned = [ln.strip() for ln in fh if ln.strip() and not ln.startswith("#")]

    findings, fence = [], False
    for n, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            fence = not fence
        if fence or line.lstrip().startswith(">"):
            continue
        rules = DIRECTIVES + FACT_DX
        for pat, label in rules:
            for m in re.finditer(pat, line, re.IGNORECASE if label != "imperative directive" else 0):
                findings.append({"line": n, "rule": label, "text": m.group(0).strip()})
        if a.strict:
            if "—" in line:
                findings.append({"line": n, "rule": "em dash", "text": "—"})
            if ";" in line and not line.lstrip().startswith("|"):
                findings.append({"line": n, "rule": "semicolon", "text": ";"})
            for b in banned:
                if re.search(r"(?<!\w)" + re.escape(b) + r"(?!\w)", line, re.IGNORECASE):
                    findings.append({"line": n, "rule": "banned word", "text": b})

    if a.json:
        print(json.dumps({"findings": findings}, indent=2))
    else:
        print(f"{len(findings)} finding(s)")
        for f in findings:
            print(f"  line {f['line']}: {f['rule']}: {f['text']}")
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main())
