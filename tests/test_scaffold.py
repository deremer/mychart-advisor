"""case-setup scaffold: complete, idempotent, never overwrites."""
import json
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCAFFOLD = os.path.join(ROOT, "skills", "case-setup", "scripts", "scaffold.py")
sys.path.insert(0, os.path.dirname(SCAFFOLD))
import scaffold  # noqa: E402

REQUIRED = [
    "AGENTS.md", "CLAUDE.md", "START-HERE.md", "Test Results", "Care Team Notes", "Other Records",
    "notes/patient-history.md", "notes/bedside-status.md", "panel/seats",
    "analysis/results-index.md", "analysis/results-summary.md", "analysis/notes-index.md",
    "analysis/notes-summary.md", "analysis/recap-discrepancies.md", "analysis/data/notes-overrides.csv",
    "analysis/changes", "analysis/questions", "analysis/conference", "consult", ".advisor/identifiers.txt",
]


def run(*args):
    return subprocess.run([sys.executable, SCAFFOLD, *args], capture_output=True, text=True)


def test_creates_full_layout(tmp_path):
    facts = tmp_path / "facts.json"
    facts.write_text(json.dumps({"PATIENT_LABEL": "Test Person", "REASON": "fictional"}))
    case = tmp_path / "case"
    assert run("--root", str(case), "--facts", str(facts)).returncode == 0
    for rel in REQUIRED:
        assert (case / rel).exists(), rel
    agents = (case / "AGENTS.md").read_text()
    assert agents.startswith("# Case folder: Test Person")
    assert "Facility: not given" in agents and "{{" not in agents
    assert (case / "CLAUDE.md").read_text().strip() == "@AGENTS.md"
    assert "## 10. Questions the notes raise" in (case / "analysis/notes-summary.md").read_text()


def test_rerun_never_overwrites(tmp_path):
    case = tmp_path / "case"
    run("--root", str(case))
    (case / "notes/bedside-status.md").write_text("family content")
    out = json.loads(run("--root", str(case), "--json").stdout)
    assert out["created"] == []
    assert (case / "notes/bedside-status.md").read_text() == "family content"


def test_layout_parser_sees_every_derived_file():
    with open(os.path.join(ROOT, "skills", "case-setup", "assets", "case-folder-layout.md")) as fh:
        dirs, files = scaffold.parse_layout(fh.read())
    assert "Care Team Notes" in dirs and "analysis/data" in dirs
    assert set(files) == {"notes/patient-history.md", "notes/bedside-status.md", "analysis/results-index.md",
                          "analysis/results-summary.md", "analysis/notes-index.md", "analysis/notes-summary.md",
                          "analysis/recap-discrepancies.md", "analysis/data/notes-overrides.csv"}
