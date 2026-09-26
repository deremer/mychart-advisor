---
name: case-conference
description: "Convenes a multi-specialty case conference on the patient's records: specialist seats chosen for this case read the indexed chart in parallel and write independent assessments, a contrarian investigator attacks the emerging consensus, a synthesizer writes a conference note with a ranked differential, open disagreements, and questions for the treating team, and a second reader checks every claim against the records. Use when someone says \"case conference\", \"run the panel\", \"tumor board\", \"what are we missing\", \"get a second look\", or \"what could this be\", or after ingest-results recommends a conference. Takes 10 to 20 minutes and a substantial number of tokens."
license: MIT
compatibility: Works best in agents that can run subagents in parallel (Claude Code, Cowork, Codex). Falls back to running seats one at a time elsewhere.
metadata:
  plugin: mychart-advisor
---

# Case conference

<!-- guardrails:start -->
## Ground rules

This skill helps a patient and family understand the records, answer what a tool can answer, and bring sharper questions to the care team. The treating team makes the diagnosis and every treatment decision.

- Generate and rank possible diagnoses freely, including rare and dangerous-to-miss ones, and name the test that would settle each. That analysis is the point, so do not hedge it away. Word findings as "consistent with," "argues for," or "argues against," state how strong each inference is, and never state a diagnosis as fact.
- Never tell anyone to start, stop, or change a treatment or dose. Anything the team might do becomes a question to ask them.
- Contact no one. Every output goes to the family first, and they decide what to share.
- Keep everything in the case folder. Never copy records into memory, other projects, or shared tools. Never put a name, birth date, record number, facility, clinician name, or exact date into a web search or fetch.
- If anything suggests an emergency, say so first and plainly: call 911 or the local emergency number, or alert the care team now.
<!-- guardrails:end -->

A conference exists to widen and sharpen the differential, surface disagreements and gaps, and hand the family specific, well-grounded questions. The failure it guards against is testing one idea at a time. Seats work at once on the same chart, disagree in writing, and the disagreements become questions.

Work in the case folder. Read `AGENTS.md` and `notes/bedside-status.md` first. If `analysis/results-index.md` is empty, run `ingest-results` first. If `panel/panel.md` does not exist, run `design-panel` first, then return here. Role briefs and the conference note structure are in [the roles reference](references/roles.md).

## 1. Mode

Ask which mode, unless the user said:

- **Standard.** Seats read the derived analysis and the latest prior conference note. Use it after a material new result, when continuity matters.
- **Fresh look.** Seats read only primary text, the two indexes, the lab table, the bedside log, and the patient history. No summaries, change notes, prior conferences, or question sheets. Use it when the folder may have anchored on one story, or before a big decision.

## 2. Set up

Create `analysis/conference/<YYYY-MM-DD>/`, adding `-2` if one exists today. Write `inputs.md` there, recording:

- the mode
- the panel version, from the dates in `panel/panel.md`
- the result and note files with times, from the manifests
- the date of the prior conference
- exactly which derived files each seat received

This is the record of what the panel could see.

Reading lists:

- **Standard mode**, in order: `AGENTS.md`, `analysis/results-index.md`, `analysis/results-summary.md`, `analysis/notes-index.md`, `analysis/notes-summary.md`, `analysis/data/labs_trend.md`, `analysis/recap-discrepancies.md`, `notes/patient-history.md`, `notes/bedside-status.md`, and the latest `analysis/conference/*/conference-note.md`.
- **Fresh-look mode:** the "Who and why," "Source rules," and "Citation format" sections of `AGENTS.md` copied into `inputs.md`, both indexes, `labs_trend.md`, `notes/patient-history.md`, and `notes/bedside-status.md`.
- **Both modes:** any seat may open any file in `analysis/data/text/`, `notes-text/`, and `other-text/`.

Show the user the panel from `panel/panel.md` in a few lines: each seat, its framing, and its main "Own" items. Mention the generalist and evidence researcher. Proceed unless they change it.

## 3. Seats, in parallel

The units are:

- each specialist seat from `panel/seats/*.md`
- the clinical generalist
- the evidence researcher

Their briefs are in the roles reference. Before starting, write the evidence researcher's six to ten literature questions from the chart, following its brief.

If you can delegate to subagents, run one per unit in parallel. Give each a self-contained prompt with four parts: its seat brief, the shared seat rules from the roles reference, the reading list for the mode, and the path to write. Otherwise run the units one at a time yourself, and write each file before starting the next, so earlier seats cannot color later ones.

Each unit writes `analysis/conference/<date>/<seat-slug>.md`, in under 1,200 words, and returns a five-line summary. Read the files, not just the summaries.

## 4. Investigator

After every seat has written its file, run the investigator as one unit with the seat file paths. Its brief is in the roles reference. It writes `investigator.md`.

## 5. Synthesizer

Run the synthesizer as one unit with every seat file and `investigator.md`. It writes `conference-note.md` in the structure given in the roles reference, in under 2,000 words, for a family that is intelligent and exhausted and may hand the note to a physician.

## 6. Second reader

Run the second reader as one unit with `conference-note.md`. It checks every factual assertion against the text files and writes `verification.md`. Then correct every "wrong" and "wording" finding in the conference note yourself. Check that every `[n]` has a source entry and every entry is cited.

## 7. Human gate

Show the user:

- a three-sentence cover: the state of the case, the leading possibilities, and the top question
- the verification tally
- the path to `conference-note.md`

Ask whether anything should be corrected before they use it. Send nothing anywhere.

Then write a change note in `analysis/changes/` summarizing what the conference changed, and add a line to the Update log in `AGENTS.md`.

## Notes

- Run a conference when something material changes, not daily.
- In Claude Code, the optional workflow `workflows/case-conference.js` runs the same pipeline through the Workflow tool, for users who opted into multi-agent workflows. The steps above need no extra permission and are the default.
- Seats and the investigator write only inside `analysis/conference/<date>/`.
- The evidence researcher searches general clinical terms only. Before any web query, check that it contains no string from `.advisor/identifiers.txt`.
