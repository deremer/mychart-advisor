"""independent-consult scripts: snapshot, diff, audit, citations, style, render."""
import json
import os
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONSULT = os.path.join(ROOT, "skills", "independent-consult", "scripts")
INGEST = os.path.join(ROOT, "skills", "ingest-results", "scripts")
FIXTURES = os.path.join(ROOT, "tests", "fixtures")


def run(script_dir, script, *args, cwd=None):
    p = subprocess.run([sys.executable, os.path.join(script_dir, script), *args], capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout, p.stderr


@pytest.fixture
def ingested(tmp_path):
    case = tmp_path / "case"
    shutil.copytree(os.path.join(FIXTURES, "case-a"), case)
    (case / ".advisor").mkdir()
    with open(case / "expected.json") as fh:
        ids = json.load(fh)["identifiers"]
    (case / ".advisor" / "identifiers.txt").write_text("\n".join(ids) + "\n")
    for s in ("extract_results.py", "extract_notes.py"):
        assert run(INGEST, s, "--root", str(case))[0] == 0
    (case / "analysis" / "results-summary.md").write_text("PRIOR INTERPRETATION that must not reach the snapshot")
    return case


def test_snapshot_refuses_before_ingest(tmp_path):
    case = tmp_path / "case"
    shutil.copytree(os.path.join(FIXTURES, "case-a"), case)
    code, _, err = run(CONSULT, "build_snapshot.py", "--root", str(case))
    assert code == 2 and "ingest-results" in err


def test_snapshot_contents_and_redaction(ingested, tmp_path):
    obs = tmp_path / "obs.md"
    obs.write_text("3/5 evening, spouse: Alex Fixture could not name the date.\n")
    out = ingested / "consult" / "snap"
    code, stdout, err = run(CONSULT, "build_snapshot.py", "--root", str(ingested), "--out", str(out),
                            "--family-observations", str(obs), "--json")
    assert code == 0, err
    info = json.loads(stdout)
    assert info["counts"] == {"result": 21, "note": 12, "other": 0}
    assert info["redactions"] > 0
    for name in ("AGENTS.md", "SNAPSHOT.md", "INDEX.csv", "snapshot.json", "labs_long.csv", "family-observations.md",
                 "_method/roles.md", "work"):
        assert (out / name).exists(), name
    blob = "".join(p.read_text(errors="ignore") for p in out.rglob("*.txt"))
    blob += (out / "family-observations.md").read_text()
    assert "Alex Fixture" not in blob and "99900001" not in blob and "[ID-" in blob
    everything = "".join(p.read_text(errors="ignore") for p in out.rglob("*") if p.is_file() and p.suffix in (".md", ".txt", ".csv"))
    assert "PRIOR INTERPRETATION" not in everything
    assert len(list((out / "notes-text").iterdir())) == 12
    # A second build into the same folder is refused.
    assert run(CONSULT, "build_snapshot.py", "--root", str(ingested), "--out", str(out))[0] == 3


def test_diff_detects_new_file(ingested):
    out = ingested / "consult" / "snap"
    run(CONSULT, "build_snapshot.py", "--root", str(ingested), "--out", str(out))
    assert run(CONSULT, "diff_snapshot.py", "--snapshot", str(out), "--root", str(ingested))[0] == 0
    shutil.copy(ingested / "Test Results" / "Lipase.pdf", ingested / "Test Results" / "Lipase 2.pdf")
    code, stdout, _ = run(CONSULT, "diff_snapshot.py", "--snapshot", str(out), "--root", str(ingested), "--json")
    assert code == 1 and json.loads(stdout)["new"] == ["Test Results/Lipase 2.pdf"]


def test_audit_counts_outside_reads_and_leaks(tmp_path):
    snap = tmp_path / "snap"
    snap.mkdir()
    ids = tmp_path / "ids.txt"
    ids.write_text("Alex Fixture\n99900001\n")
    lines = [
        {"cwd": str(tmp_path), "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": str(snap / "INDEX.csv")}}]}},
        {"cwd": str(tmp_path), "message": {"content": [{"type": "tool_use", "name": "Read", "input": {"file_path": str(tmp_path / "AGENTS.md")}}]}},
        {"cwd": str(tmp_path), "message": {"content": [{"type": "tool_use", "name": "Grep", "input": {"pattern": "x"}}]}},
        {"cwd": str(tmp_path), "message": {"content": [{"type": "tool_use", "name": "WebSearch", "input": {"query": "alex fixture liver"}}]}},
        {"cwd": str(tmp_path), "message": {"content": [{"type": "tool_use", "name": "WebSearch", "input": {"query": "smooth muscle antibody sensitivity"}}]}},
    ]
    t = tmp_path / "agent.jsonl"
    t.write_text("\n".join(json.dumps(l) for l in lines) + "\n")
    code, stdout, _ = run(CONSULT, "audit_tool_calls.py", "--snapshot", str(snap), "--identifiers", str(ids),
                          "--transcripts", str(t), "--json")
    report = json.loads(stdout)
    assert code == 1
    assert report["tool_calls"] == 5 and report["outside_reads"] == 2 and report["identifier_leaks"] == 1
    assert "Alex" not in stdout


def test_citations(tmp_path):
    good = tmp_path / "good.md"
    good.write_text("Sodium 131 [1]. Potassium [2, 1].\n\n```\n[9] in code\n```\n\n## Sources\n1. `a.pdf`\n2. `b.pdf`\n\n"
                    "## Addendum, 2025-03-08\nNew [1].\n\n### Sources\n1. `c.pdf`\n")
    assert run(CONSULT, "check_citations.py", str(good))[0] == 0
    bad = tmp_path / "bad.md"
    bad.write_text("Claim [1]. Claim [3].\n\n## Sources\n1. `a.pdf`\n2. `b.pdf`\n")
    code, stdout, _ = run(CONSULT, "check_citations.py", str(bad))
    assert code == 1 and "[3]" in stdout and "entry 2" in stdout


def test_style_flags_directives_not_differentials(tmp_path):
    ok = tmp_path / "ok.md"
    ok.write_text("The findings are consistent with autoimmune hepatitis and argue against viral hepatitis.\n"
                  "Ask whether a biopsy has been considered.\n> Not medical advice. Stop and call 911 if urgent.\n")
    assert run(CONSULT, "style_check.py", str(ok))[0] == 0
    bad = tmp_path / "bad.md"
    bad.write_text("The team should stop the statin.\nIncrease the dose of lactulose.\nThe patient has autoimmune hepatitis.\n")
    code, stdout, _ = run(CONSULT, "style_check.py", str(bad), "--json")
    rules = {f["rule"] for f in json.loads(stdout)["findings"]}
    assert code == 1 and {"directive to act", "dosing directive", "diagnosis stated as fact"} <= rules


def test_render_html(tmp_path):
    md = tmp_path / "report.md"
    md.write_text("# Report\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n- item **bold**\n\n> footer\n")
    code, _, _ = run(CONSULT, "render_html.py", str(md))
    html = (tmp_path / "report.html").read_text()
    assert code == 0 and "<table>" in html and "<strong>bold</strong>" in html and "Confidential" in html
