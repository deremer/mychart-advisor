"""Static checks on every skill: Agent Skills spec compliance, shared guardrails, links, portability."""
import os
import re

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKILLS = os.path.join(ROOT, "skills")
GUARDRAILS = os.path.join(SKILLS, "case-setup", "assets", "guardrails.md")
EXPECTED = ["case-setup", "patient-intake", "record-observations", "ingest-results", "ask-the-records",
            "design-panel", "case-conference", "prep-questions", "independent-consult"]
NAMES = sorted(d for d in os.listdir(SKILLS) if os.path.isfile(os.path.join(SKILLS, d, "SKILL.md")))


def frontmatter(text):
    m = re.match(r"^---\n(.*?)\n---\n", text, re.DOTALL)
    assert m, "missing YAML frontmatter"
    fm = {}
    for line in m.group(1).splitlines():
        if re.match(r"^[a-z][a-z0-9_-]*:", line):
            k, v = line.split(":", 1)
            fm[k] = v.strip()
    return fm, text[m.end():]


def read(name):
    with open(os.path.join(SKILLS, name, "SKILL.md"), encoding="utf-8") as fh:
        return fh.read()


def unquote(v):
    if v.startswith('"') and v.endswith('"'):
        return v[1:-1].replace('\\"', '"')
    return v


def test_all_expected_skills_exist():
    assert sorted(NAMES) == sorted(EXPECTED)


@pytest.mark.parametrize("name", NAMES)
def test_frontmatter_follows_spec(name):
    fm, _ = frontmatter(read(name))
    assert fm.get("name") == name, "name must match folder"
    assert re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) and len(name) <= 64
    desc = unquote(fm.get("description", ""))
    assert 50 <= len(desc) <= 1024, len(desc)
    raw = fm["description"]
    if ":" in desc:
        assert raw.startswith('"'), "descriptions containing a colon must be quoted"
    assert not desc.lower().startswith(("use this", "i ", "you ")), "third person"


@pytest.mark.parametrize("name", NAMES)
def test_body_under_500_lines(name):
    assert len(read(name).splitlines()) < 500


@pytest.mark.parametrize("name", NAMES)
def test_guardrails_identical(name):
    with open(GUARDRAILS, encoding="utf-8") as fh:
        want = fh.read().strip()
    text = read(name)
    m = re.search(r"<!-- guardrails:start -->.*?<!-- guardrails:end -->", text, re.DOTALL)
    assert m, "missing guardrail block"
    assert m.group(0).strip() == want


@pytest.mark.parametrize("name", NAMES)
def test_relative_links_resolve(name):
    _, body = frontmatter(read(name))
    for target in re.findall(r"\]\(([^)#]+)\)", body):
        if target.startswith(("http://", "https://")):
            continue
        assert os.path.exists(os.path.join(SKILLS, name, target)), target


@pytest.mark.parametrize("name", NAMES)
def test_no_host_specific_tool_names_in_instructions(name):
    _, body = frontmatter(read(name))
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    for tool in ("Task tool", "Agent tool", "Bash tool", "Read tool", "Grep tool", "spawn_agent", "TodoWrite"):
        assert tool not in body, tool


@pytest.mark.parametrize("name", NAMES)
def test_scripts_referenced_exist(name):
    body = read(name)
    for script in re.findall(r"scripts/([\w.-]+\.py)", body):
        assert os.path.exists(os.path.join(SKILLS, name, "scripts", script)), script
