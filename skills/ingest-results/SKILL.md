---
name: ingest-results
description: "Ingests newly downloaded patient-portal PDFs (test results, care team notes, and other records from Epic MyChart or another portal) into a case folder. Extracts the text, rebuilds lab trend tables as CSV and markdown, updates the results and notes indexes, the running summaries, and the discrepancy log, refreshes where the case stands, and writes a short what-changed note the family can read on a phone. Offers to record bedside observations first. Use when someone says \"ingest\", \"new results\", \"new notes\", \"I downloaded more files\", \"update the labs\", \"what changed\", or \"refresh the case\"."
license: MIT
compatibility: Python 3.10+ plus either poppler (pdftotext) or pdfplumber. pdfplumber is declared inline, so `uv run` installs it. Any agent that can run commands and edit files.
metadata:
  plugin: mychart-advisor
---

# Ingest new results and notes

<!-- guardrails:start -->
## Ground rules

This skill helps a patient and family understand the records, answer what a tool can answer, and bring sharper questions to the care team. The treating team makes the diagnosis and every treatment decision.

- Generate and rank possible diagnoses freely, including rare and dangerous-to-miss ones, and name the test that would settle each. That analysis is the point, so do not hedge it away. Word findings as "consistent with," "argues for," or "argues against," state how strong each inference is, and never state a diagnosis as fact.
- Never tell anyone to start, stop, or change a treatment or dose. Anything the team might do becomes a question to ask them.
- Contact no one. Every output goes to the family first, and they decide what to share.
- Keep everything in the case folder. Never copy records into memory, other projects, or shared tools. Never put a name, birth date, record number, facility, clinician name, or exact date into a web search or fetch.
- If anything suggests an emergency, say so first and plainly: call 911 or the local emergency number, or alert the care team now.
<!-- guardrails:end -->

Turn new PDFs into indexed, cited, dated understanding. Scripts do the mechanical extraction. You do the reading, cross-checking, and writing. Results say what was measured. Notes say what the team saw, thought, ordered, and gave. Both are primary.

Work in the case folder. If there is no `AGENTS.md` beginning `# Case folder:`, run `case-setup` first. Read `AGENTS.md`, `notes/bedside-status.md`, `notes/patient-history.md`, and both indexes before starting. Detailed row formats and update rules are in [the ingest reference](references/ingest-reference.md). Read it on the first ingest of a session.

## 0. Observations first

Ask: "Before I read the new files, anything you've noticed or been told since the last update?" If yes, run `record-observations` now, so the new records get read against fresh family report. If no, continue.

## 1. Extract

The scripts are in the `scripts/` folder next to this file. In Claude Code that folder is `${CLAUDE_SKILL_DIR}/scripts`. Run each with the case folder as the working directory. Prefer `uv run`, which installs pdfplumber automatically, and fall back to `python3` if `uv` is missing.

```
uv run "${CLAUDE_SKILL_DIR}/scripts/extract_results.py"
uv run "${CLAUDE_SKILL_DIR}/scripts/extract_notes.py"
uv run "${CLAUDE_SKILL_DIR}/scripts/extract_other.py"
```

Either poppler's `pdftotext` or the `pdfplumber` package is enough. If `python3` exits with code 3, neither is present. Ask the user before installing anything. The options are installing poppler, for example `brew install poppler` or `apt install poppler-utils`, or `pip install pdfplumber` into a virtual environment. `extract_other.py` exits with code 2 when there is no `Other Records/` folder. That is normal.

Each script lists files it has not seen before. On a rerun in the same session, pass `--since <YYYY-MM-DD>` to list everything first seen since then. Act on every warning line:

- **NO TEXT LAYER.** The PDF is a scan. Read the PDF directly, or run `ocrmypdf` on a copy if it is installed. Never let it become a missing result.
- **NO RESULT PRINTED.** Open the PDF to confirm. A result page can be released before the value is filled in. Record it as "released with no result printed," and list the test under "Not in the folder" until a result arrives.
- **LAB RANGES BUT NO VALUES PARSED.** Read the values from the text by hand.
- **UNPARSED NAME.** Read the note, find its true type, author, and service time, add a row to `analysis/data/notes-overrides.csv`, and rerun `extract_notes.py`.
- **NOT A PDF.** Read the image or file directly.

## 2. Read every new file

For every new file, read its text in `analysis/data/text/`, `notes-text/`, or `other-text/`. Never trust a file name to say what a file is.

- Results: the collected time, the full body, and any lab comment about specimen quality, dilution, delays, or deviations. For imaging, find the exam time in the report and compare it with the collected time.
- Notes: the attestation if there is one, the interval history, the exam, the medication list, and the assessment from the end backward, because new thinking is usually appended.
- Mismatched content: if a note's content does not match its name, add an override row and rerun.

## 3. Update results

Follow [the ingest reference](references/ingest-reference.md) for row formats.

1. Add a row per new result to `analysis/results-index.md` under the right category, with the value, unit, reference range, and collected time. If it answers something listed under "Not in the folder," remove that entry.
2. In `analysis/results-summary.md`, add the study under its date in section 2, with a finding paragraph and an assessment paragraph. Then reread sections 1 and 3 to 5 and fix every sentence the new result makes wrong. Move answered questions out of section 5.

## 4. Update notes

1. Add a row per new note to `analysis/notes-index.md` under its service. Quote the attestation or the newly appended assessment sentence. Flag carried-forward text, and flag contradictions with another note or a result.
2. In `analysis/notes-summary.md`, add a dated block to section 1 and rows to the timeline (2) and function table (7). Update the medication reconstruction (3) for any start, stop, or dose change. Close items in section 6 that a note resolved and say what closed them. Add history found only in the notes to section 4. Reread sections 9 and 10 and fix what changed. New questions continue the numbering from the results summary.
3. Update "People in the chart" in `AGENTS.md` for any new author or service.

## 5. Cross-check

Compare each new note against the results, the bedside log, and the patient history. Log each conflict in `analysis/recap-discrepancies.md` under "Notes versus results versus family report," in a dated block, with citations. Look for:

- a value the result contradicts
- a plan the results show did not happen
- a templated exam line the family or a therapy note contradicts
- a time that differs from a result's collection time
- history that differs from the family's
- a result that no note has acknowledged yet

## 6. Where the case stands

If anything new changes the picture, add a dated paragraph at the top of "Where the case stands" in `AGENTS.md`. Lead with what changed and what it means for the differential. Name the questions that follow, and say which earlier paragraph it replaces. Be concrete about possibilities. "A platelet count falling by half five days after heparin started argues for heparin-induced thrombocytopenia over simple consumption. The PF4 antibody test is what separates them" is the register. Then add a line to the Update log.

## 7. Change note

Write `analysis/changes/<YYYY-MM-DD>.md`, adding `-2`, `-3` if one exists for today. The family reads this on a phone. It must run 300 words or fewer, not counting the sources and footer, and use plain language. On a first ingest or a large batch, keep to the few findings that matter most and point to the summaries for the rest. Count the words before finishing. It covers:

- what arrived
- what it says, with numbers, units, and ranges
- what it changes in the picture and the differential
- the question it raises

Cite per `AGENTS.md`, and end with the output footer.

If any new file falls in one of the classes below, put **"A case conference is recommended"** in bold on the first line with the one-line reason:

- tissue, cytology, or pathology
- a result that supports or rules out a possibility on the current differential
- a new imaging modality, body region, or finding
- the first note from a newly consulted service
- a start, stop, or dose change of a drug that shapes the course
- a procedure planned, done, or cancelled
- a note stating the team's plan after pending results
- a change in disposition or discharge date

If `panel/panel.md` exists and a new service or organ system has entered the case, add: "The case conference panel may need a new seat. Run `design-panel` to review it."

## 8. Verify before reporting

- For each source folder, the number of PDFs on disk must equal the manifest row count and the text file count. If they differ, find out why.
- Check every number you wrote in a summary or change note against the text file of the PDF it came from, never against the trend table or an index.
- Every number in the change note and summaries carries a citation, every `[n]` has a source entry, and every entry is cited.

Report in a few lines: the counts, what arrived, the headline of the change note, and whether a conference is recommended.

## Rules

- Never edit the PDFs, the family's narrative, or `notes/` entries. Log corrections in the discrepancy file.
- If the same order appears twice with different collection times, both are real. Numbered suffixes on result files mean download order, not time.
- A parse failure must never become a missing result. Read the file by hand and say so in the change note.
- Before claiming a test is absent, search generic clinical terms plus brand and assay names, and name the terms you searched.
