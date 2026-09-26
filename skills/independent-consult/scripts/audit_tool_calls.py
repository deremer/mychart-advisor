#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Audit blind-agent transcripts: reads outside the snapshot, and identifiers in web queries.

Usage:
    python3 audit_tool_calls.py --snapshot DIR --identifiers FILE (--transcripts PATH... | --claude-auto)
                                [--since ISO] [--prefix consult-blind:] [--json]

--transcripts takes JSONL files or directories, searched recursively for *.jsonl.
--claude-auto finds Claude Code subagent transcripts for the current working directory under
~/.claude/projects, keeping only agents whose .meta.json description starts with --prefix and, with
--since, files modified after that time.

Any tool call with a file path outside the snapshot counts as an outside read. Any web search or fetch
whose query or URL contains an identifier (case-insensitive) counts as a leak. The report prints counts
and locations, never the identifier itself.

Exit codes: 0 clean, 1 violations found, 2 no transcripts found.
"""
import argparse
import datetime
import glob
import json
import os
import re
import sys

PATH_KEYS = ("file_path", "path", "notebook_path", "directory")
WEB_HINTS = ("websearch", "webfetch", "web_search", "web_fetch", "fetch", "search_web", "browse")


def claude_transcripts(prefix, since):
    project = re.sub(r"[^A-Za-z0-9]", "-", os.path.abspath(os.getcwd()))
    base = os.path.join(os.path.expanduser("~"), ".claude", "projects", project)
    out = []
    for jsonl in glob.glob(os.path.join(base, "*", "subagents", "*.jsonl")):
        if since and os.path.getmtime(jsonl) < since:
            continue
        meta = jsonl[:-len(".jsonl")] + ".meta.json"
        try:
            with open(meta) as fh:
                desc = json.load(fh).get("description", "")
        except (OSError, ValueError):
            continue
        if desc.startswith(prefix):
            out.append(jsonl)
    return out


def tool_uses(obj):
    if isinstance(obj, dict):
        if obj.get("type") == "tool_use" and "name" in obj:
            yield obj.get("name", ""), obj.get("input", {}) or {}
        for v in obj.values():
            yield from tool_uses(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from tool_uses(v)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--identifiers", required=True)
    ap.add_argument("--transcripts", nargs="*", default=[])
    ap.add_argument("--claude-auto", action="store_true")
    ap.add_argument("--prefix", default="consult-blind:")
    ap.add_argument("--since", default=None, help="ISO time; ignore transcripts older than this")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    snapshot = os.path.realpath(a.snapshot)
    ids = []
    if os.path.exists(a.identifiers):
        with open(a.identifiers, encoding="utf-8") as fh:
            ids = [ln.strip().lower() for ln in fh if len(ln.strip()) >= 4 and not ln.startswith("#")]
    since = datetime.datetime.fromisoformat(a.since).timestamp() if a.since else None

    files = []
    for t in a.transcripts:
        files += glob.glob(os.path.join(t, "**", "*.jsonl"), recursive=True) if os.path.isdir(t) else [t]
    if a.claude_auto:
        files += claude_transcripts(a.prefix, since)
    files = sorted(set(files))
    if not files:
        print("No transcripts found to audit.", file=sys.stderr)
        return 2

    calls, outside, leaks = 0, [], []
    for f in files:
        with open(f, encoding="utf-8", errors="ignore") as fh:
            for n, line in enumerate(fh, 1):
                try:
                    obj = json.loads(line)
                except ValueError:
                    continue
                cwd = obj.get("cwd", os.getcwd()) if isinstance(obj, dict) else os.getcwd()
                for name, inp in tool_uses(obj):
                    calls += 1
                    paths = [inp.get(k) for k in PATH_KEYS if isinstance(inp, dict) and isinstance(inp.get(k), str)]
                    if not paths and name.lower() in ("grep", "glob", "ls"):
                        paths = ["."]  # a search with no path covers the whole working directory
                    for p in paths:
                        full = os.path.realpath(p if os.path.isabs(p) else os.path.join(cwd, p))
                        if not (full == snapshot or full.startswith(snapshot + os.sep)):
                            outside.append({"transcript": os.path.basename(f), "line": n, "tool": name, "path": p})
                    if any(h in name.lower() for h in WEB_HINTS):
                        blob = json.dumps(inp).lower()
                        hits = sum(1 for i in ids if i in blob)
                        if hits:
                            leaks.append({"transcript": os.path.basename(f), "line": n, "tool": name, "identifiers": hits})

    report = {"transcripts": len(files), "tool_calls": calls, "outside_reads": len(outside),
              "identifier_leaks": len(leaks), "outside": outside[:50], "leaks": leaks[:50]}
    if a.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"Audited {len(files)} transcripts, {calls} tool calls: {len(outside)} reads outside the snapshot, "
              f"{len(leaks)} web calls containing an identifier")
        for o in outside[:50]:
            print(f"  OUTSIDE: {o['transcript']}:{o['line']} {o['tool']} {o['path']}")
        for l in leaks[:50]:
            print(f"  LEAK: {l['transcript']}:{l['line']} {l['tool']} ({l['identifiers']} identifier matches)")
    return 1 if (outside or leaks) else 0


if __name__ == "__main__":
    sys.exit(main())
