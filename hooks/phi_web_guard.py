#!/usr/bin/env python3
"""PreToolUse hook: block a web search or fetch that contains a case identifier.

Reads the hook payload on stdin. Walks up from the session's working directory to find a case folder's
.advisor/identifiers.txt. Blocks (exit code 2, reason on stderr) when the query, URL, or prompt contains
any listed identifier of 4+ characters, or a redaction token such as [ID-3] from a consult snapshot.
Outside a case folder it allows everything. It never prints the identifier it matched.
"""
import json
import os
import re
import sys


def find_identifiers(start):
    d = os.path.abspath(start)
    while True:
        path = os.path.join(d, ".advisor", "identifiers.txt")
        if os.path.isfile(path):
            return path
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def main():
    try:
        payload = json.load(sys.stdin)
    except ValueError:
        return 0
    blob = json.dumps(payload.get("tool_input", {})).lower()
    if re.search(r"\[id-\d+\]", blob):
        print("Blocked by mychart-advisor: the web request contains a redaction token from the case snapshot. "
              "Search general clinical terms only.", file=sys.stderr)
        return 2
    path = find_identifiers(payload.get("cwd") or os.getcwd())
    if not path:
        return 0
    with open(path, encoding="utf-8", errors="ignore") as fh:
        ids = [ln.strip().lower() for ln in fh if len(ln.strip()) >= 4 and not ln.startswith("#")]
    for i in ids:
        if re.search(r"(?<!\w)" + re.escape(i) + r"(?!\w)", blob):
            print("Blocked by mychart-advisor: the web request contains a patient or care-team identifier from "
                  ".advisor/identifiers.txt. Rewrite it with general clinical terms only.", file=sys.stderr)
            return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
