# AGENTS.md

Instructions for any AI agent working on this repository. `CLAUDE.md` imports this file. Keep this file as the single source of truth.

## What this repo is

A plugin of agent skills that helps patients and families organize exported patient-portal records, understand them, and bring better questions to the care team. It targets Claude Code and Claude Cowork first, and follows the open Agent Skills format so the skills also run in Codex, Gemini CLI, Cursor, Copilot, and other hosts.

Read `DISCLAIMER.md` before writing any skill text. The purpose statement there governs every prompt in this repo.

## No real case data

This is the rule that outranks every other.

- `docs/input/` holds private reference material from a real case. It is gitignored. Never commit it, never force-add it, never copy its sentences, examples, lab lists, trigger phrases, specialty emphasis, or dates into any tracked file.
- Never add real patient records, names, facilities, clinician names, record numbers, dates of birth, or distinctive clinical details from a real case. All examples, fixtures, and tests use fictional patients.
- `scripts/dev/check-no-case-data.sh` runs as the pre-commit hook (`git config core.hooksPath .githooks`) and in CI. Do not bypass it with `--no-verify`.
- Maintainers keep a local, gitignored `.case-denylist` with one term per line. The guard fails any commit that contains a listed term. Never print, commit, or summarize its contents.
- Stage files by explicit path. Do not use `git add -A` or `git add .`.

## Stance the skills take

The skills generate and rank differential diagnoses freely, including rare and dangerous-to-miss possibilities. They name what to chase and which tests would settle each one. That analysis is the value to the family. The line they hold is narrow: no final diagnosis stated as fact, no treatment, dosing, or stop-medication directive, no contact with anyone, nothing framed as an order to the care team. Guardrail text must never discourage hypothesis generation.

## Layout

```
.claude-plugin/       plugin.json and marketplace.json for Claude Code and Cowork
.agents/plugins/      marketplace.json for Codex
skills/<name>/        SKILL.md plus optional scripts/, references/, assets/
agents/               Claude subagent definitions (blind-reader)
hooks/                Claude hooks (PHI web guard)
workflows/            optional Claude Workflow-tool scripts
evals/                claude plugin eval suite
tests/                pytest, synthetic fixture generator and fixtures
scripts/dev/          contributor tooling
```

## Writing skills

- Follow the Agent Skills spec. `name` is lowercase with hyphens and matches the folder. `description` is third person, 1,024 characters or fewer, says what the skill does and when to use it, uses the words a family would type, and is quoted if it contains a colon.
- Keep each SKILL.md under 500 lines. Put detail in `references/`, linked one level deep. Add a table of contents to any reference longer than 100 lines.
- Write portable instructions. Say "read the file," "search the text," and "run this command," not a host's tool names. Describe parallel work as independent units: if the host can delegate to subagents, run one per unit in parallel, otherwise do them in order and write each result to its file first.
- Claude-only frontmatter such as `disable-model-invocation` or `when_to_use` is allowed. No behavior may depend on it.
- Refer to bundled scripts as `${CLAUDE_SKILL_DIR}/scripts/<name>.py` and also say "the `scripts/` folder next to this SKILL.md," so the path resolves in hosts that do not substitute the variable.
- Skills depend on the case folder, never on another skill's files. Shared rules live in the case `AGENTS.md` that `case-setup` writes.
- Every skill opens with the shared guardrail block from `skills/case-setup/assets/guardrails.md`. Keep the copies identical. `tests/test_skills.py` enforces this.

## Writing scripts

- Python 3.10 or later. Declare dependencies with PEP 723 inline metadata so `uv run` works. The fallback is `python3` with `pip install pdfplumber`.
- Standard library plus `pdfplumber` at runtime. No AGPL dependencies such as PyMuPDF.
- No interactive prompts. Summaries go to stdout, diagnostics to stderr, with distinct exit codes and bounded output.
- Never modify a user's source records.

## Development

```
python3 -m venv .venv && .venv/bin/pip install pdfplumber reportlab pytest
.venv/bin/python tests/fixtures/generate.py      # rebuild synthetic fixtures
.venv/bin/pytest                                 # unit tests
claude --plugin-dir .                            # load the plugin locally
claude plugin eval . --threshold 0.8             # evals, costs tokens
```

## Writing style

Plain sentences a family can follow and a physician can check. Lead with the answer. Prose over bullets, tables where they are clearer. Numbers keep their unit, reference range, and date.
