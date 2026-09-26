---
name: case-setup
description: "Sets up a new case folder for tracking a patient's portal records (Epic MyChart or another patient portal): creates the folder structure, the case instructions file, and a start-here guide, and records the handful of facts every other skill needs. Use when someone says \"set up a case\", \"start tracking my mom's results\", \"new case folder\", \"get started with mychart-advisor\", or \"first time using this\", or when another mychart-advisor skill finds no case AGENTS.md. Safe to rerun to repair a folder."
license: MIT
compatibility: Python 3.10+ (standard library only). Works in any agent that can read and write local files and run a command.
metadata:
  plugin: mychart-advisor
---

# Set up a case folder

<!-- guardrails:start -->
## Ground rules

This skill helps a patient and family understand the records, answer what a tool can answer, and bring sharper questions to the care team. The treating team makes the diagnosis and every treatment decision.

- Generate and rank possible diagnoses freely, including rare and dangerous-to-miss ones, and name the test that would settle each. That analysis is the point, so do not hedge it away. Word findings as "consistent with," "argues for," or "argues against," state how strong each inference is, and never state a diagnosis as fact.
- Never tell anyone to start, stop, or change a treatment or dose. Anything the team might do becomes a question to ask them.
- Contact no one. Every output goes to the family first, and they decide what to share.
- Keep everything in the case folder. Never copy records into memory, other projects, or shared tools. Never put a name, birth date, record number, facility, clinician name, or exact date into a web search or fetch.
- If anything suggests an emergency, say so first and plainly: call 911 or the local emergency number, or alert the care team now.
<!-- guardrails:end -->

One patient, one folder. This skill creates the folder once and repairs it later. It writes no analysis.

The script and templates live next to this file, in `scripts/` and `assets/`. In Claude Code that folder is `${CLAUDE_SKILL_DIR}`.

## 1. Find the folder

If the working directory already has an `AGENTS.md` that begins with `# Case folder:`, this is a repair. Skip to step 4 and say so.

Otherwise ask where the case folder should live. Suggest the working directory if it is empty or already holds `Test Results/` or `Care Team Notes/`. Recommend a folder that is not synced to a shared drive and is not inside a git repository. One folder per patient.

## 2. Ask for the case facts

Ask in one message, and say every item is optional except how to refer to the patient. Never guess an answer, and never fill one in from the records later without asking.

- How to refer to the patient. A first name or "Mom" is fine.
- Age.
- The user's relationship to the patient.
- Care setting: inpatient, emergency, outpatient workup, or other.
- Facility.
- When this episode started: admission date or first visit.
- The reason, in one sentence, in the family's words.
- Attending or physician of record.
- Outpatient or primary physician.
- Which patient portal they use.

Write the answers to `.advisor/facts.json` inside the case folder (create `.advisor/` first) with the keys `PATIENT_LABEL`, `AGE`, `RELATIONSHIP`, `SETTING`, `FACILITY`, `START_DATE`, `REASON`, `ATTENDING`, `OUTPATIENT`, `PORTAL`.

## 3. Ask for the private identifiers

Explain why. These are the strings that must never go into a web search. Skills check web queries against them, and in Claude Code a hook blocks any search that contains one. The list never leaves the folder and is never quoted in any output.

Ask for the patient's full legal name and nicknames, date of birth, medical record numbers, facility names, and the names of clinicians the family knows. All are optional. More entries mean stronger protection.

## 4. Build the folder

Run from anywhere:

```
python3 "${CLAUDE_SKILL_DIR}/scripts/scaffold.py" --root "<case folder>" --facts "<case folder>/.advisor/facts.json"
```

The script creates every folder and starting file listed in `assets/case-folder-layout.md`, fills the templates, and never overwrites an existing file. On a repair, leave out `--facts`. Delete `.advisor/facts.json` afterward.

Then write the identifiers to `.advisor/identifiers.txt`, one per line. On a repair, append only new entries.

If the host cannot run commands, create the same structure by hand from `assets/case-folder-layout.md`, `assets/case-AGENTS.template.md`, and `assets/START-HERE.template.md`.

## 5. Tell the user how records get in

Keep this short, and point to `START-HERE.md` in the folder for the full table.

- Save each test result from the portal as a PDF into `Test Results/`.
- Save each clinical note as a PDF into `Care Team Notes/`.
- Put medication lists, discharge papers, outside records, and photos of paperwork into `Other Records/`.
- Keep the portal's file names.
- In Epic MyChart, results are under Test Results and notes under Visits or Notes, depending on the health system. Open each item and use the print or download option to save it as a PDF.

## 6. Offer the next step

Offer `patient-intake` next. A short history interview makes every later analysis better. If PDFs are already in the folders, say that `ingest-results` is ready to run after intake.

Report what was created, in a few lines. Do not print the identifiers.
