"""Extractor tests against the synthetic fixtures. Run with pytest from the repo root."""
import csv
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "skills", "ingest-results", "scripts")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")
sys.path.insert(0, SCRIPTS)

import extract_results  # noqa: E402
from portals import mychart  # noqa: E402

BACKENDS = ["pdfplumber"] + (["pdftotext"] if shutil.which("pdftotext") else [])


def run(script, *args):
    p = subprocess.run([sys.executable, os.path.join(SCRIPTS, script), *args], capture_output=True, text=True)
    return p.returncode, p.stdout, p.stderr


def read_csv(path):
    with open(path, newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(params=[(c, b) for c in ("case-a", "case-b") for b in BACKENDS], ids=lambda p: f"{p[0]}-{p[1]}")
def extracted(request, tmp_path):
    case, backend = request.param
    root = tmp_path / case
    shutil.copytree(os.path.join(FIXTURES, case), root)
    for script in ("extract_results.py", "extract_notes.py"):
        code, out, err = run(script, "--root", str(root), "--backend", backend)
        assert code == 0, err
    with open(root / "expected.json") as fh:
        expected = json.load(fh)
    return root, expected, backend


def test_counts_match_disk(extracted):
    root, expected, _ = extracted
    data = root / "analysis" / "data"
    results = read_csv(data / "manifest.csv")
    notes = read_csv(data / "notes-manifest.csv")
    assert len(results) == expected["counts"]["results"] == len(os.listdir(root / "Test Results"))
    assert len(notes) == expected["counts"]["notes"] == len(os.listdir(root / "Care Team Notes"))
    assert len(os.listdir(data / "text")) == len(results)
    assert len(os.listdir(data / "notes-text")) == len(notes)


def test_every_seeded_lab_value_is_extracted(extracted):
    root, expected, _ = extracted
    rows = read_csv(root / "analysis" / "data" / "labs_long.csv")
    got = {(r["file"], r["analyte"], r["value"]) for r in rows}
    missing = [e for e in expected["labs"] if (e["file"], e["analyte"], e["value"]) not in got]
    assert not missing, missing
    assert len(rows) == len(expected["labs"]), "extra rows mean a header or tick row was read as a value"


def test_units_and_reference_limits(extracted):
    root, _, _ = extracted
    rows = read_csv(root / "analysis" / "data" / "labs_long.csv")
    for r in rows:
        assert r["collected"], r
        assert int(r["page"]) >= 1
        if r["analyte"] == "INR":
            assert (r["ref_low"], r["ref_high"]) == ("0.9", "1.1")
        if r["analyte"] in ("Sodium", "WBC", "CRP"):
            assert r["unit"] in ("mmol/L", "K/uL", "mg/L")
    if root.name == "case-a":
        # The metabolic panel runs onto a second page. Page numbers must follow it.
        assert {r["page"] for r in rows if r["analyte"] == "ALT"} == {"2"}


def test_trap_files_are_not_dropped(extracted):
    root, expected, _ = extracted
    results = {r["file"] for r in read_csv(root / "analysis" / "data" / "manifest.csv")}
    notes = {r["file"] for r in read_csv(root / "analysis" / "data" / "notes-manifest.csv")}
    traps = expected["traps"]
    if "uppercase_extension" in traps:
        assert traps["uppercase_extension"] in results
    if "leading_space_filename" in traps:
        assert traps["leading_space_filename"] in notes


def test_empty_result_is_flagged_and_nothing_else(extracted):
    root, expected, _ = extracted
    flagged = {r["file"] for r in read_csv(root / "analysis" / "data" / "manifest.csv") if r["status"] != "ok"}
    want = {expected["traps"]["empty_result"]} if "empty_result" in expected["traps"] else set()
    assert flagged == want


def test_note_names_parse(extracted):
    root, _, _ = extracted
    notes = read_csv(root / "analysis" / "data" / "notes-manifest.csv")
    assert all(n["metadata_from"] == "file name" for n in notes)
    times = [n["service_time"] for n in notes]
    assert times == sorted(times)


def test_rerun_reports_nothing_new_and_since_lists_earlier(tmp_path):
    root = tmp_path / "case"
    shutil.copytree(os.path.join(FIXTURES, "case-b"), root)
    run("extract_results.py", "--root", str(root))
    code, out, _ = run("extract_results.py", "--root", str(root), "--json")
    summary = json.loads(out)
    assert summary["new"] == []
    code, out, _ = run("extract_results.py", "--root", str(root), "--json", "--since", "2000-01-01")
    assert len(json.loads(out)["since"]) == summary["pdfs"]


def test_overrides_replace_file_name_metadata(tmp_path):
    root = tmp_path / "case"
    shutil.copytree(os.path.join(FIXTURES, "case-a"), root)
    data = root / "analysis" / "data"
    data.mkdir(parents=True)
    target = " Progress Notes by Dana Placeholder, MD at 3-6-2025 9-05 AM.pdf"
    with open(data / "notes-overrides.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "service_time", "note_type", "author", "credential"])
        w.writerow([target.strip(), "2025-03-06 10:30", "Progress Notes", "Dana Placeholder", "MD"])
    run("extract_notes.py", "--root", str(root))
    row = next(r for r in read_csv(data / "notes-manifest.csv") if r["file"] == target)
    assert (row["service_time"], row["metadata_from"]) == ("2025-03-06 10:30", "override")


def test_missing_folder_exit_code(tmp_path):
    code, _, err = run("extract_results.py", "--root", str(tmp_path))
    assert code == 2 and "No results folder" in err


def test_whitespace_duplicates_get_distinct_text_files(tmp_path):
    import pdftext
    a, b = str(tmp_path / "Lab.pdf"), str(tmp_path / " Lab.pdf")
    names = pdftext.text_names([a, b])
    assert names[a] == "Lab.txt" and names[b] == "[dup] Lab.txt"


@pytest.mark.parametrize("name,expected", [
    ("Progress Notes by Pat Q. Example, MD at 3:4:2025 9-15 AM.pdf", ("2025-03-04 09:15", "Progress Notes", "Pat Q. Example", "MD")),
    ("Consults by Pat Example MD at 12/31/2024 1115 PM.pdf", ("2024-12-31 23:15", "Consults", "Pat Example", "MD")),
    ("  Therapy Note by Sam Example, OTR:L at 1-2-2025 7-05 AM .pdf", ("2025-01-02 07:05", "Therapy Note", "Sam Example", "OTR/L")),
    ("Discharge Summary.pdf", None),
])
def test_parse_note_name_variants(name, expected):
    assert mychart.parse_note_name(name) == expected


@pytest.mark.parametrize("ref,expected", [
    ("136 - 145 mmol/L", ("mmol/L", "136", "145")),
    ("<20 Units", ("Units", "", "20")),
    (">=60 mL/min/1.73m2", ("mL/min/1.73m2", "60", "")),
    ("Negative", ("", "", "")),
])
def test_split_ref(ref, expected):
    assert extract_results.split_ref(ref) == expected


def test_tick_rows_are_never_values():
    text = "Sodium\nNormal range: 136 - 145 mmol/L\nValue\n131 Low\n113366 114455\n"
    assert mychart.parse_single_column(text) == [("Sodium", "131", "Low", "136 - 145 mmol/L", 1)]
    text = "Sodium\nNormal range: 136 - 145 mmol/L\n113366 114455\n"
    assert mychart.parse_single_column(text) == []


@pytest.mark.skipif(not shutil.which("pdftotext"), reason="needs poppler")
@pytest.mark.parametrize("case", ["case-a", "case-b"])
def test_text_column_fallback_without_pdfplumber(case):
    """With pdftotext but no pdfplumber, two-column panels are split by character offset."""
    with open(os.path.join(FIXTURES, case, "expected.json")) as fh:
        expected = json.load(fh)["labs"]
    got = set()
    folder = os.path.join(FIXTURES, case, "Test Results")
    for name in os.listdir(folder):
        text = subprocess.run(["pdftotext", "-layout", os.path.join(folder, name), "-"],
                              capture_output=True, text=True).stdout
        if mychart.has_labs(text):
            got |= {(name, n, v) for n, v, *_ in mychart.parse_text_columns(text)}
    assert got == {(e["file"], e["analyte"], e["value"]) for e in expected}
