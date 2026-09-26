"""Generic adapter for portals without a dedicated parser.

Extracts text only. Tries common collection-time labels for the manifest. Parses no lab values, so the
agent reads these files directly. Add a new adapter module beside this one for another portal, with the
same functions, and register it in portals/__init__.py.
"""
import re
from datetime import datetime

NAME = "generic"

LABELS = r"(?:Collected on|Collected|Collection Date(?:/Time)?|Specimen Collected|Date Collected|Date of Service|Exam Date)"


def detect(text):
    return True


def result_header(text):
    m = re.search(LABELS + r"\s*[:\-]?\s*([^\n|]{6,40})", text, re.IGNORECASE)
    return (m.group(1).strip() if m else ""), ""


def parse_time(s):
    for fmt in ("%b %d, %Y %I:%M %p", "%m/%d/%Y %I:%M %p", "%m/%d/%Y %H:%M", "%m/%d/%Y", "%Y-%m-%d %H:%M",
                "%Y-%m-%d", "%B %d, %Y"):
        try:
            return datetime.strptime(s.strip(), fmt)
        except ValueError:
            continue
    return None


def parse_labs(pdf, text):
    return [], ""


def parse_note_name(filename):
    return None
