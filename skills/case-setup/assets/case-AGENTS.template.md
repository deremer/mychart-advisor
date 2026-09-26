# Case folder: {{PATIENT_LABEL}}

Read this file at the start of every session in this folder. It says who the patient is, what the folder holds, which sources to trust, how to cite, and where the case stands. Every mychart-advisor skill defers to it.

## Purpose

This folder exists so the family can understand the records, follow trends, see the full range of possibilities the evidence supports, and use their limited time with the care team on what only the care team can answer. It is not a diagnosis and it does not direct care. The treating team makes the diagnosis and every decision.

Generate and rank possible diagnoses freely, including rare and dangerous-to-miss ones, and name the test that would settle each. Word findings as "consistent with," "argues for," or "argues against," and state how strong each inference is. Never state a diagnosis as fact. Never tell anyone to start, stop, or change a treatment or dose. Contact no one. If anything suggests an emergency, say so first: call 911 or the local emergency number, or alert the care team now.

## Who and why

- Patient: {{PATIENT_LABEL}}, {{AGE}}
- Person running this folder and relationship: {{RELATIONSHIP}}
- Care setting: {{SETTING}}
- Facility: {{FACILITY}}
- Start of this episode (admission or first visit): {{START_DATE}}
- Reason, in one sentence: {{REASON}}
- Attending or physician of record: {{ATTENDING}}
- Outpatient or primary physician: {{OUTPATIENT}}
- Portal: {{PORTAL}}

Fields marked "not given" were left blank on purpose. Ask before filling them. Never guess.

## Folder map

| Path | What it holds | Trust |
|---|---|---|
| `Test Results/` | One portal PDF per released order: labs, imaging, pathology, microbiology, other studies. | Primary record. |
| `Care Team Notes/` | One portal PDF per clinical note: physician, nursing, therapy, pharmacy, nutrition, case management. | Primary record. What the team saw, thought, ordered, and gave. |
| `Other Records/` | Medication lists, outside records, discharge papers, photos of documents. | Primary, but check dates. A medication list is a snapshot. |
| `notes/patient-history.md` | History the family gave through `patient-intake`. | Family report. The family is the primary source for history. |
| `notes/bedside-status.md` | Dated observations the family made or were told, through `record-observations`. | Family report. Read it every session. |
| `family-recap*.md` | The family's own narrative, if they wrote one. | Family report. Never edited. |
| `analysis/results-index.md`, `analysis/notes-index.md` | One row per file: when, what matters, when to reach for it. | Derived. Start here to find anything. |
| `analysis/results-summary.md`, `analysis/notes-summary.md` | Running chronological accounts with assessment. | Derived. Updated on every ingest. |
| `analysis/recap-discrepancies.md` | Every conflict between records, and between records and family report. | Derived. |
| `analysis/data/` | Extracted text, manifests, and lab tables written by scripts. Search the text instead of opening PDFs. | Derived by script. Check numbers against the PDF. |
| `analysis/changes/` | One short what-changed note per meaningful new input. | Derived. |
| `analysis/questions/` | Question sheets from `prep-questions`. | Derived. |
| `analysis/conference/<date>/` | Case conference outputs. | Derived. |
| `panel/` | The case conference panel: roster and one brief per seat. | Configuration. |
| `consult/<date>/` | Independent consult outputs. | Derived. |
| `.advisor/identifiers.txt` | Names and numbers that must never enter a web search. | Private. Never quote it. |

## Source rules

A PDF beats anything derived from it. When a summary, an index, or the lab table disagrees with a PDF, the PDF wins and the derived file gets corrected.

A result beats a note on a measured number. A note beats a result on what the team planned, ordered, gave, examined, or was told.

The family beats the chart on history, unless there is a specific reason to doubt them. A history in a note is a clinician's summary of what someone said, often written in a hurry. When the chart and the family disagree on history, log it in `analysis/recap-discrepancies.md`.

A measured finding beats a templated one. Physician exam lines are often carried forward from note to note unchanged. A therapy or nursing note that measured something on a given day, or an attending attestation, outweighs a templated exam line. Before treating a repeated sentence as confirmation, find where it first appeared.

Times matter. The "collected" time on an imaging result is often the order time, and the report or a procedure note gives the exam time. Check every result's time against when treatments started and stopped, because a study done after treatment began may not be able to show what it was ordered to show.

Absence is a claim about search terms. Portals name tests by order code, and a test can hide under a name that contains none of the expected words. Before saying a test was not done, search generic clinical words as well as brand and assay names, and say which terms you searched. Something missing from this folder means "not released or not downloaded," never "not done."

Never invent, round, or infer a value. If something is not in the folder, say so.

## Citation format

Every prose document cites its sources with bracketed numbers: summaries, change notes, conference files, question sheets, and consult reports.

In the text, put the number after the clause it supports, before the period: `[3]`, or `[3, 7]` for several. Keep the value, unit, reference range, and date in the sentence. Only the file name moves to the source list. Example: potassium 3.1 mmol/L, ref 3.5 to 5.1, collected 3/4 6:10 AM [3].

End the document with `## Sources`. Number entries in order of first use and reuse a number on every later use. Each entry is one line: the number, the file name in backticks with its folder, the collection or service time, and a few words on what it is.

```
3. `Test Results/Basic Metabolic Panel 2.pdf`, collected 3/4 6:10 AM, morning chemistry.
7. `Care Team Notes/Progress Notes by <author> at <time>.pdf`, service 3/4 9:15 AM, daily progress note.
9. Family report, 3/5, observed confusion after dinner.
12. Literature: <publisher or author>, <title>, <journal or site>, <year>, <URL>.
```

A number cites the PDF it came from, never a summary or table that repeated it. The indexes, `analysis/data/labs_trend.md`, discrepancy tables, and the one-screen card of a question sheet are lookups and need no citations. Before finishing any document, check that every bracket has an entry and every entry is cited.

## Reading portal PDFs

Result PDFs hold one order each. The header carries identifiers and a collected time. Lab pages show the analyte, a normal range, the value with any High or Low flag, and a row of axis tick labels that text extraction renders with doubled characters ("44..22" is 4.2). Imaging reports usually put the impression first. Numbered suffixes in file names reflect download order, not time.

Note PDFs carry the note type, author, service time, and signed time. Resident notes may open with an attending attestation signed later, which is the attending's own view and the plan of record. Many services carry the assessment forward and add new sentences at the end, so read the attestation, the interval history, the exam, the medication list, and the end of the assessment. When a file's content does not match its name, record the correction in `analysis/data/notes-overrides.csv`.

## Where the case stands

Dated paragraphs, newest first. Each leads with what changed and what it means, names the questions that follow, and says which earlier paragraph it replaces.

_No entries yet._

## People in the chart

Service, name, role, and dates on the case, built from note authors, attestations, and ordering providers.

_No entries yet._

## How to work in this folder

- Start each session by reading this file, `notes/bedside-status.md`, and the two indexes. Open a PDF only when you need it. Its text is in `analysis/data/`.
- New files downloaded: run `ingest-results`. It offers `record-observations` first.
- Something seen or heard at the bedside: run `record-observations`.
- A material change, or before a big decision: run `case-conference`. The first run builds the panel with `design-panel`.
- Before a conversation with the care team: run `prep-questions`.
- For a fully independent, blinded second look: run `independent-consult`.
- Keep every output in this folder. Never edit the PDFs or the family's own narrative. Log corrections in `analysis/recap-discrepancies.md`.
- Write for the family and a physician at once: plain sentences, exact numbers with units, reference ranges, and dates, numbered citations. Lead with what changed and what it means.

## Output footer

End every change note, conference note, question sheet, and consult report with this line:

> Prepared to help the family understand the records and prepare questions for the care team. Not a diagnosis or medical advice. The treating team makes all decisions.

## Update log

One line per ingest, observation entry, conference, consult, or correction: date, what arrived or ran, which files changed, and what was verified.

- {{TODAY}}: Case folder created with `case-setup`.
