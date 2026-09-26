"""Shared PDF text extraction for the ingest scripts.

Backends, in order of preference:
  pdftotext -layout   (poppler, if installed). Fast, keeps lab columns aligned.
  pdfplumber          (pure Python). Layout-preserving text, pages separated by form feeds.

Text files are cached next to each other and re-extracted only when the PDF is newer.
"""
import os
import re
import shutil
import subprocess
import sys

PDF_EXT = ".pdf"


def backend(preferred=None):
    """Return the text backend to use: 'pdftotext', 'pdfplumber', or None if neither is available."""
    if preferred in (None, "pdftotext") and shutil.which("pdftotext"):
        return "pdftotext"
    if preferred in (None, "pdfplumber"):
        try:
            import pdfplumber  # noqa: F401
            return "pdfplumber"
        except ImportError:
            pass
    return None


def list_files(src):
    """Every regular file in a source folder, split into PDFs and other files. Extension match ignores case."""
    pdfs, other = [], []
    for name in sorted(os.listdir(src)):
        path = os.path.join(src, name)
        if not os.path.isfile(path) or name.startswith("."):
            continue
        (pdfs if name.lower().endswith(PDF_EXT) else other).append(path)
    return pdfs, other


def text_names(pdfs):
    """Map each PDF path to a text file name. Names are stripped of surrounding spaces. When two PDFs differ
    only by surrounding spaces, the padded one gets a '[dup] ' prefix so neither text file overwrites the other."""
    stripped = [os.path.basename(p).strip() for p in pdfs]
    collide = {n for n in stripped if stripped.count(n) > 1}
    out = {}
    for p in pdfs:
        b = os.path.basename(p)
        s = b.strip()
        name = "[dup] " + s if (b != s and s in collide) else s
        out[p] = os.path.splitext(name)[0] + ".txt"
    return out


def extract(pdf, out, which):
    """Extract one PDF to `out` if the cached text is missing or stale. Returns the text."""
    if not os.path.exists(out) or os.path.getmtime(out) < os.path.getmtime(pdf):
        if which == "pdftotext":
            subprocess.run(["pdftotext", "-layout", pdf, out], check=False,
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            import pdfplumber
            try:
                with pdfplumber.open(pdf) as doc:
                    pages = [pg.extract_text(layout=True) or "" for pg in doc.pages]
                text = "\f".join(pages)
            except Exception as exc:  # a corrupt PDF must not stop the run
                print(f"  EXTRACT FAILED ({exc.__class__.__name__}): {os.path.basename(pdf)}", file=sys.stderr)
                text = ""
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(text)
        if not os.path.exists(out):
            open(out, "w").close()
    with open(out, encoding="utf-8", errors="ignore") as fh:
        return fh.read()


BOILERPLATE = re.compile(r"^\s*(Name:|Legal Name|Collected on|Result date|Ordering|Authorizing|Resulting|"
                         r"Specimen collected|Signed:|Page \d)", re.IGNORECASE)


LABELS = {"results", "result", "value", "component", "components", "narrative", "impression", "lab comment",
          "comment", "specimen", "reference range", "normal range"}


def content_chars(text, title_lines=1):
    """Alphanumeric characters left after removing portal header and footer lines, bare section labels, and
    the title. A result page released with nothing printed scores zero even though the header has text."""
    lines = [ln for ln in text.splitlines()
             if ln.strip() and not BOILERPLATE.match(ln) and ln.strip().strip(":").lower() not in LABELS]
    body = lines[title_lines:]
    return sum(ch.isalnum() for ln in body for ch in ln)


def total_chars(text):
    return sum(ch.isalnum() for ch in text)
