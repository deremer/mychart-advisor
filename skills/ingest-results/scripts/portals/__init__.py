"""Portal adapters. Each module exposes the same functions:

    NAME                       adapter name, recorded in the manifest
    detect(text) -> bool       whether this adapter recognizes a result PDF's text
    result_header(text)        -> (collected, result_date) as printed
    parse_time(s)              -> datetime or None, for sorting
    parse_labs(pdf, text)      -> (rows, note), rows of (analyte, value, flag, ref, page)
    parse_note_name(filename)  -> (service_time 'YYYY-MM-DD HH:MM', note_type, author, credential) or None

Manifest and CSV schemas are the same whatever the adapter, so the skills never care which one ran.
"""
from . import generic, mychart

ADAPTERS = {"mychart": mychart, "generic": generic}
AUTO_ORDER = [mychart, generic]


def pick(text, name="auto"):
    if name != "auto":
        return ADAPTERS[name]
    for a in AUTO_ORDER:
        if a.detect(text):
            return a
    return generic
