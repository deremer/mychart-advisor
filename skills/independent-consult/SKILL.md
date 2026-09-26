---
name: independent-consult
description: "Runs a blinded, independent consult on the patient's records, the kind of fresh outside read a family might hire. A team of agents that has not seen the treating team's conclusions or the family's prior analysis builds a fact base, generates every hypothesis the records cannot yet rule out, investigates each family of hypotheses with literature, attacks its own conclusions with a red team, reconciles against the treating team and prior analysis, and produces one verified, cited report with a test plan. Use only when someone explicitly asks for an \"independent consult\", \"blinded second opinion\", \"fresh unbiased review\", or \"leave no stone unturned\", or for a consult addendum or status. Expensive: from about 10 to 35 or more agents."
license: MIT
compatibility: Best in Claude Code or Cowork, which support a blind subagent type through this plugin's blind-reader agent. Other hosts can run the blind stage in a separate session opened in the snapshot folder. Python 3.10+.
disable-model-invocation: true
argument-hint: "[start|addendum|status] [standard|deep|max]"
metadata:
  plugin: mychart-advisor
---

# Independent consult

<!-- guardrails:start -->
## Ground rules

This skill helps a patient and family understand the records, answer what a tool can answer, and bring sharper questions to the care team. The treating team makes the diagnosis and every treatment decision.

- Generate and rank possible diagnoses freely, including rare and dangerous-to-miss ones, and name the test that would settle each. That analysis is the point, so do not hedge it away. Word findings as "consistent with," "argues for," or "argues against," state how strong each inference is, and never state a diagnosis as fact.
- Never tell anyone to start, stop, or change a treatment or dose. Anything the team might do becomes a question to ask them.
- Contact no one. Every output goes to the family first, and they decide what to share.
- Keep everything in the case folder. Never copy records into memory, other projects, or shared tools. Never put a name, birth date, record number, facility, clinician name, or exact date into a web search or fetch.
- If anything suggests an emergency, say so first and plainly: call 911 or the local emergency number, or alert the care team now.
<!-- guardrails:end -->

As records pile up, a folder anchors on a story, and so does everyone reading it. This consult deliberately does not. The blind half sees only a frozen snapshot of primary record text, generates hypotheses from several independent angles, and attacks its own work. Only afterward does a reconciler compare its findings with the treating team's thinking and the family's prior analysis. [The design principles](references/lessons.md) explain each choice.

You are the orchestrator. You are not blind, so never paste case summaries, conference notes, or your own conclusions into a blind prompt. Blind prompts carry only the snapshot path, the role prompt, and the output format.

Scripts are in the `scripts/` folder next to this file. In Claude Code that folder is `${CLAUDE_SKILL_DIR}/scripts`. Work in the case folder.

## Modes

The argument chooses the mode:

- **start** is the default.
- **addendum** runs the addendum section below.
- **status** reports from `consult/<date>/progress.md`: phase, units done, and any preliminary findings sent.

## Start

### 1. Preconditions and scale

- The case folder has an `AGENTS.md` beginning `# Case folder:`. Otherwise run `case-setup`.
- Every PDF is ingested. Run `ingest-results` first if the manifests are behind. `build_snapshot.py` refuses to run otherwise.
- Show the file counts. Ask the user to choose a preset, using the costs in [the roles reference](references/roles.md):
  - **standard**, about 10 agents, the default
  - **deep**, about 28
  - **max**, 35 or more

  State the rough token cost and wall time, and ask before launching anything. In Claude Code, the optional workflows `consult-blind` and `consult-synthesis` run the same phases through the Workflow tool, but only for users who have opted into multi-agent workflows.
- Ask where the prior analysis is. The default is every derived file in `analysis/`, plus `family-recap*.md` and earlier `consult/*/report.md`. Ask whether any of it should be left out.

Create `consult/<YYYY-MM-DD>/`, and keep `progress.md` there updated after every phase. It is what `status` reads, and it serves as a resume point.

### 2. Family observations

Follow [the sanitizing guide](references/sanitize-family-notes.md) to write `consult/<date>/family-observations.md`. Show it to the user, and continue only with their approval.

### 3. Freeze the snapshot

```
python3 "${CLAUDE_SKILL_DIR}/scripts/build_snapshot.py" --family-observations consult/<date>/family-observations.md
```

The snapshot goes in `consult/<date>/snapshot/`. It holds primary text only, with identifiers replaced by tokens, and adds the blind rules as its `AGENTS.md`. Record the counts and freeze time in `consult/<date>/inputs.md`, along with the preset, what the snapshot excludes, and the user's approval of the observations.

### 4. Blinding probe

Blinding is the product. Verify it every run.

- **In Claude Code or Cowork.** Start one agent of type `mychart-advisor:blind-reader`, with the description `consult-blind: probe`, and this prompt: "Without using any tools, answer in one line: is there any text in your context that begins with '# Case folder:' or that describes where this case stands? Quote the first five words if so." If it reports case instructions, repeat with the built-in `Explore` type. If both fail, stop and tell the user.
- **In other hosts.** Assume subagents inherit the case instructions. Rebuild the snapshot with `--out` pointing outside the case folder. Ask the user to open a new session in that folder and say "run the blind stage, <preset> preset." The snapshot's `AGENTS.md` walks that session through it. Resume here at step 6 once `work/` is filled.

Record the probe result in `inputs.md`.

### 5. Blind stage

Run the phases for the chosen preset, in order, as in the roles reference:

1. fact base
2. generators
3. triage
4. investigators
5. red team
6. second round
7. test planner

Every unit is a blind-reader agent, or whichever type passed the probe. Give each a description starting `consult-blind:`, and a prompt made of three parts: the standard blind preamble, the role prompt, and the output format. Within a phase, if you can delegate to subagents, run the units in parallel. Otherwise run them one at a time.

After each unit returns, do three things:

1. Save its full answer to `consult/<date>/snapshot/work/<phase>-<role>.md`.
2. Validate any JSON block against [the schemas](references/schemas.md). If it is invalid, ask the unit to fix it.
3. Scan the answer for an `URGENT` section. Send any urgent item to the user immediately, marked **preliminary**, in a short message. The same applies to any finding that should change a planned procedure, and to a newly released result the treating team does not seem to have seen.

Merge the investigators' rows into `snapshot/work/ledger.json`, and update `progress.md`.

### 6. Synthesis stage

1. **Prior analysis.** Assemble `consult/<date>/prior/` by copying in the prior-analysis files the user approved. This folder must not exist until now.
2. **Reconciler.** Run it as a general agent, not blind. It reads `snapshot/work/`, the notes in `snapshot/notes-text/`, and `prior/`. Save its answer to `consult/<date>/reconciliation.md`, and copy it into `snapshot/work/`.
3. **Synthesizer.** Run it blind. It writes the report from `snapshot/work/`, following [the report template](references/report-template.md), and never reads `prior/`. Save the result as `consult/<date>/report.md`.
4. **Verifiers.** Run them as the preset specifies, in parallel if you can. Save their output as `consult/<date>/verification.md`.
5. **Fixer.** Apply the corrections, or have a unit apply them, confirming each against the source.
6. **Checks.** Run:
   ```
   python3 "${CLAUDE_SKILL_DIR}/scripts/check_citations.py" consult/<date>/report.md
   python3 "${CLAUDE_SKILL_DIR}/scripts/style_check.py" consult/<date>/report.md
   ```
   Fix every citation error. Rewrite every directive as a question for the treating team, and every diagnosis stated as fact as "consistent with." Leave properly worded differentials alone.

### 7. Audit

In Claude Code:

```
python3 "${CLAUDE_SKILL_DIR}/scripts/audit_tool_calls.py" --snapshot consult/<date>/snapshot --identifiers .advisor/identifiers.txt --claude-auto --since <snapshot freeze time>
```

In other hosts, pass the blind session's transcript files with `--transcripts` if the host keeps them, or record that the audit was not available. Report both counts to the user: reads outside the snapshot and identifiers in web queries. Explain any nonzero count.

### 8. Render and hand over

```
python3 "${CLAUDE_SKILL_DIR}/scripts/render_html.py" consult/<date>/report.md --pdf
```

A PDF appears only if a headless browser exists. Otherwise the HTML prints from any browser. Put the patient's name in `--title` only if the user wants it there.

Give the user four things:

- the bottom line, section 2 of the report, in a few sentences
- the verification tally and the audit counts
- the file paths
- a reminder that `prep-questions` turns the test plan into a question sheet

Ask whether anything should be corrected before the family uses the report. Write a change note in `analysis/changes/`, and add a line to the Update log in `AGENTS.md`.

## Addendum

Records keep arriving. The verified report is never silently rewritten.

1. Run `ingest-results` for the new files.
2. Run `python3 "${CLAUDE_SKILL_DIR}/scripts/diff_snapshot.py" --snapshot consult/<date>/snapshot` to list new, changed, and missing files.
3. Build a new snapshot with `--out consult/<date>/addendum-<YYYY-MM-DD>/snapshot`. Copy the original `work/ledger.json` and `report.md` into its `work/`.
4. Run one blind unit. It reads the new files, then the ledger, and decides whether any new record changes a tier, a claim, or the test plan. It gives citations, and flags anything urgent.
5. Append its findings to `report.md` as `## Addendum, <date>` with its own `### Sources`. Run `check_citations.py` and `style_check.py` again, then re-render.
6. Tell the user what changed. Write a change note.

## Limits to state every time

The consult cannot see several things:

- the medication administration record
- vital-sign flowsheets
- images and slides themselves
- records never downloaded
- the patient

It is a structured second read that helps the family ask better questions, not a physician's opinion.
