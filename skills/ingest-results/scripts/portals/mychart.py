"""Epic MyChart adapter.

Result PDFs ("Test Details"): a header line with name, DOB, and MRN, a "Collected on" specimen time, a
"Result date", then one block per analyte: the analyte name, a "Normal range:" or "Normal value:" line,
the value with an optional flag, and a row of axis tick labels that text extraction renders with every
character doubled ("44..22" is 4.2). Some panels print two columns of analytes side by side.

Note PDFs are named "<Note type> by <Author>, <Cred> at <M/D/YYYY> <h-mm AM>.pdf". macOS shows "/" in file
names as ":", and some downloads use "-". Some names drop the comma before the credential or the dash in
the time ("657" for 6:57), and a few carry leading or trailing spaces.
"""
import re
from collections import defaultdict
from datetime import datetime

NAME = "mychart"

# ---------------------------------------------------------------------------------------------- results

def detect(text):
    return "Collected on" in text or "Normal range:" in text or "Normal value:" in text


def result_header(text):
    coll = re.search(r"Collected on ([^\n|]*)", text)
    res = re.search(r"Result date: ([^\n|]*)", text)
    return (coll.group(1).strip() if coll else ""), (res.group(1).strip() if res else "")


def parse_time(s):
    for fmt in ("%b %d, %Y %I:%M %p", "%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


def has_labs(text):
    return bool(re.search(r"^\s*Normal (range|value):", text, re.MULTILINE))


VALUE = re.compile(r"^\s*([<>]?\s?[\d.,]+)\s*(High|Low|Abnormal|Critical|HH|LL|H|L)?\s*$")
SKIP_PREFIXES = ("Ordering", "Authorizing", "Collection", "Collected", "Specimen", "Result", "Resulting",
                 "Name:", "Legal Name", "Diff", "Value", "Results", "Normal", "Lab comment", "Performed")


def name_tokens(text):
    """Words of the patient name from the header, so a wrapped header line is never read as an analyte."""
    toks = set()
    for m in re.finditer(r"(?:Legal )?Name:\s*([^|\n]+)", text):
        toks.update(t for t in re.split(r"\s+", m.group(1).strip()) if t)
    return toks


def _page_of(text, offset):
    return text.count("\f", 0, offset) + 1


def parse_single_column(text):
    """Analyte blocks laid out one per line group. Returns (name, value, flag, ref, page)."""
    out = []
    lines = text.split("\n")
    offsets, pos = [], 0
    for ln in lines:
        offsets.append(pos)
        pos += len(ln) + 1
    i = 0
    while i < len(lines):
        name = lines[i].strip().lstrip("\f")
        nxt = lines[i + 1].strip() if i + 1 < len(lines) else ""
        if (name and re.match(r"^[A-Za-z(][^:]{0,70}$", name) and not name.startswith(SKIP_PREFIXES)
                and re.match(r"^Normal (range|value):", nxt)):
            ref = re.sub(r"^Normal (range|value):", "", nxt).strip()
            j, val = i + 2, None
            while j < len(lines) and j < i + 8:
                s = lines[j].strip()
                m = VALUE.match(lines[j])
                if s and m:
                    val = (m.group(1).replace(" ", "").rstrip(","), m.group(2) or "")
                    break
                if s and re.search(r"\d+\s+\d", s):
                    break  # reached the tick row without a value
                j += 1
            if val:
                out.append((name, val[0], val[1], ref, _page_of(text, offsets[i])))
                i = j
        i += 1
    return out


def parse_two_column(pdf):
    """Panels printed in two side-by-side columns. Needs pdfplumber word positions.
    Returns (name, value, flag, ref, page)."""
    import pdfplumber
    # Axis ticks render with every character doubled. A real value such as 330 merely starts with a doubled
    # digit, so require every token on the row to be fully doubled and at least two tokens per row.
    tick = re.compile(r"^(?:(\d)\1|(\.)\2)+$")
    num = re.compile(r"^[<>]?\d+(\.\d+)?$")
    flags = {"High", "Low", "Abnormal", "Critical", "H", "L"}
    out = []

    def column(words, page, skip):
        rows = defaultdict(list)
        for w in words:
            rows[round(w["top"] / 4)].append(w)
        cur, state = None, None
        for k in sorted(rows):
            toks = [w["text"] for w in sorted(rows[k], key=lambda w: w["x0"])]
            text = " ".join(toks)
            if text.startswith("Normal"):
                if cur:
                    cur["ref"] = re.sub(r"^Normal (range|value):", "", text).strip()
                    state = "val"
                continue
            if len(toks) >= 2 and all(tick.match(t) for t in toks):
                continue
            if state == "val":
                vals = [t for t in toks if num.match(t.replace(",", ""))]
                if vals and len(toks) <= 3:
                    out.append((cur["name"], vals[0], next((t for t in toks if t in flags), ""), cur["ref"], page))
                    cur, state = None, None
                    continue
                if toks[0] == "Value":
                    continue
            if skip and all(t.strip(",|") in skip for t in toks):
                continue
            if "DOB:" in text or "MRN:" in text:
                continue
            if re.match(r"^[A-Za-z(]", text) and len(toks) <= 7 and not text.startswith(SKIP_PREFIXES):
                cur, state = {"name": text, "ref": ""}, "ref"

    with pdfplumber.open(pdf) as doc:
        for n, pg in enumerate(doc.pages, 1):
            words = pg.extract_words()
            skip = name_tokens(pg.extract_text() or "")
            split = pg.width / 2
            if any(w["text"] == "Normal" and w["x0"] > split - 10 for w in words):
                column([w for w in words if w["x0"] < split - 5], n, skip)
                column([w for w in words if w["x0"] >= split - 5], n, skip)
            else:
                column(words, n, skip)
    return out


def is_two_column(pdf):
    try:
        import pdfplumber
    except ImportError:
        return None
    with pdfplumber.open(pdf) as doc:
        for pg in doc.pages:
            split = pg.width / 2
            if any(w["text"] == "Normal" and w["x0"] > split - 10 for w in pg.extract_words()):
                return True
    return False


def parse_labs(pdf, text):
    """Returns (rows, note). Rows are (name, value, flag, ref, page). note explains a skipped parse."""
    if not has_labs(text):
        return [], ""
    two = is_two_column(pdf)
    if two is None:
        # No pdfplumber. Layout text from pdftotext keeps columns aligned, so split it by character offset.
        rows = parse_text_columns(text)
        return rows, "" if rows else "pdfplumber missing, lab values not parsed"
    return (parse_two_column(pdf) if two else parse_single_column(text)), ""


def parse_text_columns(text):
    """Parse layout-preserved text, splitting two-column pages at the right column's character offset."""
    rows = []
    for page_no, page in enumerate(text.split("\f"), 1):
        offsets = [m.start() for ln in page.splitlines() for m in re.finditer(r"Normal (?:range|value):", ln)
                   if m.start() > 20]
        if offsets:
            col = min(offsets)
            left = "\n".join(ln[:col].rstrip() for ln in page.splitlines())
            right = "\n".join(ln[col:] for ln in page.splitlines())
            parts = [left, right]
        else:
            parts = [page]
        for part in parts:
            rows += [(n, v, f, r, page_no) for n, v, f, r, _ in parse_single_column(part)]
    return rows


# ------------------------------------------------------------------------------------------------ notes

CREDENTIALS = {"MD", "DO", "PA-C", "PA", "NP", "APRN", "CRNA", "CNM", "RN", "LPN", "PT", "DPT", "PTA", "OTR/L",
               "OT/L", "OT", "COTA", "SLP", "CCC-SLP", "RRT", "RD", "RDN", "RPh", "PharmD", "MSW", "LCSW", "LMSW",
               "PhD", "PsyD", "CNS", "MBBS"}

NOTE_NAME = re.compile(
    r"^\s*(?P<type>.+?) by (?P<author>.+?) at (?P<m>\d{1,2})[:/-](?P<d>\d{1,2})[:/-](?P<y>\d{4})"
    r"\s+(?P<h>\d{1,2})[-:]?(?P<mi>\d{2})\s?(?P<ap>AM|PM)\s*\.pdf\s*$", re.IGNORECASE)


def parse_note_name(filename):
    """Returns (service_time 'YYYY-MM-DD HH:MM', note_type, author, credential) or None."""
    m = NOTE_NAME.match(filename)
    if not m:
        return None
    g = m.groupdict()
    try:
        when = datetime.strptime(f"{g['m']}/{g['d']}/{g['y']} {g['h']}:{g['mi']} {g['ap'].upper()}",
                                 "%m/%d/%Y %I:%M %p")
    except ValueError:
        return None
    author, cred = g["author"].strip(), ""
    if "," in author:
        author, cred = [s.strip() for s in author.split(",", 1)]
    else:
        parts = author.rsplit(" ", 1)
        if len(parts) == 2 and parts[1].replace(":", "/") in CREDENTIALS:
            author, cred = parts
    return when.strftime("%Y-%m-%d %H:%M"), g["type"].strip(), author, cred.replace(":", "/")
