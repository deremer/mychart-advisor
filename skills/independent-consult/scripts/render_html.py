#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Render a consult report from markdown to a standalone, printable HTML file, and optionally to PDF.

Usage:
    python3 render_html.py report.md [--out report.html] [--title TEXT] [--pdf]

Supports the markdown the report uses: headings, paragraphs, bold, italics, inline code, links, ordered
and unordered lists, tables, block quotes, horizontal rules, and fenced code. Every page carries a
confidentiality line. The patient's name appears only if it is in the title you pass.

--pdf prints the HTML to PDF with a headless Chrome, Chromium, or Edge if one is installed, and says so
if none is found. Exit codes: 0 success, 1 PDF requested but no browser found.
"""
import argparse
import html
import os
import re
import shutil
import subprocess
import sys

CSS = """
body{font:15px/1.55 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;color:#1d1d1f;max-width:820px;margin:0 auto;padding:32px 20px}
h1{font-size:26px;margin:.2em 0 .6em}h2{font-size:20px;margin:1.6em 0 .5em;border-bottom:1px solid #ddd;padding-bottom:.2em}
h3{font-size:16px;margin:1.3em 0 .4em}table{border-collapse:collapse;width:100%;margin:1em 0;font-size:13px}
th,td{border:1px solid #ccc;padding:5px 7px;vertical-align:top;text-align:left}th{background:#f3f3f3}
blockquote{margin:1em 0;padding:.4em 1em;border-left:4px solid #999;background:#f7f7f7}
code{background:#f3f3f3;padding:0 3px;border-radius:3px;font-size:13px}pre{background:#f3f3f3;padding:10px;overflow:auto}
.conf{font-size:11px;color:#666;border-bottom:1px solid #ddd;padding-bottom:6px;margin-bottom:18px}
@media print{body{padding:0;max-width:none}.conf{position:running(header)}a{color:inherit}}
@page{margin:18mm 14mm;@bottom-right{content:counter(page) " / " counter(pages);font-size:10px}}
"""
CONF = ("Confidential. Prepared for the patient's family to understand the records and prepare questions for "
        "the care team. Not a diagnosis or medical advice.")


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<![*\w])\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r'<a href="\2">\1</a>', s)
    return s


def convert(md):
    out, lines, i = [], md.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.strip().startswith("```"):
            j = i + 1
            while j < len(lines) and not lines[j].strip().startswith("```"):
                j += 1
            out.append("<pre><code>" + html.escape("\n".join(lines[i + 1:j])) + "</code></pre>")
            i = j + 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)", line)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
            i += 1
            continue
        if re.match(r"^\s*(-{3,}|\*{3,})\s*$", line):
            out.append("<hr>")
            i += 1
            continue
        if line.lstrip().startswith("|") and i + 1 < len(lines) and re.match(r"^\s*\|?\s*:?-+", lines[i + 1]):
            head = [c.strip() for c in line.strip().strip("|").split("|")]
            rows, i = [], i + 2
            while i < len(lines) and lines[i].lstrip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            out.append("<table><thead><tr>" + "".join(f"<th>{inline(c)}</th>" for c in head) + "</tr></thead><tbody>"
                       + "".join("<tr>" + "".join(f"<td>{inline(c)}</td>" for c in r) + "</tr>" for r in rows)
                       + "</tbody></table>")
            continue
        if line.lstrip().startswith(">"):
            buf = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                buf.append(lines[i].lstrip()[1:].strip())
                i += 1
            out.append("<blockquote>" + inline(" ".join(buf)) + "</blockquote>")
            continue
        if re.match(r"^\s*([-*]|\d+\.)\s+", line):
            ordered = bool(re.match(r"^\s*\d+\.", line))
            tag, items = ("ol" if ordered else "ul"), []
            while i < len(lines) and re.match(r"^\s*([-*]|\d+\.)\s+", lines[i]):
                items.append(re.sub(r"^\s*([-*]|\d+\.)\s+", "", lines[i]))
                i += 1
                while i < len(lines) and lines[i].startswith("   ") and lines[i].strip():
                    items[-1] += " " + lines[i].strip()
                    i += 1
            out.append(f"<{tag}>" + "".join(f"<li>{inline(t)}</li>" for t in items) + f"</{tag}>")
            continue
        if not line.strip():
            i += 1
            continue
        buf = []
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#{1,6}\s|\s*[-*]\s|\s*\d+\.\s|\s*\||\s*>|```)", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        out.append("<p>" + inline(" ".join(buf)) + "</p>")
    return "\n".join(out)


def find_browser():
    candidates = ["google-chrome", "chromium", "chromium-browser", "microsoft-edge", "chrome",
                  "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                  "/Applications/Chromium.app/Contents/MacOS/Chromium",
                  "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"]
    for c in candidates:
        path = shutil.which(c) or (c if os.path.exists(c) else None)
        if path:
            return path
    return None


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file")
    ap.add_argument("--out", default=None)
    ap.add_argument("--title", default="Independent consult report")
    ap.add_argument("--pdf", action="store_true")
    a = ap.parse_args()
    with open(a.file, encoding="utf-8") as fh:
        body = convert(fh.read())
    out = a.out or os.path.splitext(a.file)[0] + ".html"
    doc = (f"<!doctype html><html lang=\"en\"><head><meta charset=\"utf-8\"><title>{html.escape(a.title)}</title>"
           f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\"><style>{CSS}</style></head>"
           f"<body><div class=\"conf\">{CONF}</div>{body}</body></html>")
    with open(out, "w", encoding="utf-8") as fh:
        fh.write(doc)
    print(f"Wrote {out}")
    if a.pdf:
        browser = find_browser()
        if not browser:
            print("No headless browser found. The HTML file can be printed to PDF from any browser.", file=sys.stderr)
            return 1
        pdf = os.path.splitext(out)[0] + ".pdf"
        subprocess.run([browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
                        f"--print-to-pdf={pdf}", "file://" + os.path.abspath(out)],
                       check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"Wrote {pdf}" if os.path.exists(pdf) else "PDF rendering failed. Print the HTML from a browser instead.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
