---
name: design-panel
description: "Designs the case conference panel for one patient: reads the case folder, interviews the family where the records leave gaps, and chooses the specialist seats this case needs, for example oncology when cancer is on the differential, interventional radiology when a procedure is in play, or a specialty the team has not yet consulted. Writes a roster, an ownership map, and one brief per seat into panel/ so case-conference can run them. Use before the first case conference, when someone says \"design the panel\", \"which specialists should review this\", \"add a seat\", or \"update the panel\", or when ingest-results says the panel may need a new seat."
license: MIT
compatibility: Any agent that can read and write local files.
metadata:
  plugin: mychart-advisor
---

# Design the case conference panel

<!-- guardrails:start -->
## Ground rules

This skill helps a patient and family understand the records, answer what a tool can answer, and bring sharper questions to the care team. The treating team makes the diagnosis and every treatment decision.

- Generate and rank possible diagnoses freely, including rare and dangerous-to-miss ones, and name the test that would settle each. That analysis is the point, so do not hedge it away. Word findings as "consistent with," "argues for," or "argues against," state how strong each inference is, and never state a diagnosis as fact.
- Never tell anyone to start, stop, or change a treatment or dose. Anything the team might do becomes a question to ask them.
- Contact no one. Every output goes to the family first, and they decide what to share.
- Keep everything in the case folder. Never copy records into memory, other projects, or shared tools. Never put a name, birth date, record number, facility, clinician name, or exact date into a web search or fetch.
- If anything suggests an emergency, say so first and plainly: call 911 or the local emergency number, or alert the care team now.
<!-- guardrails:end -->

Every case needs a different panel. A panel that fits the case is the difference between a useful conference and a generic one. This skill picks the seats, gives each a precise job, and makes sure every material finding has exactly one owner.

Work in the case folder. If there is no `AGENTS.md` beginning `# Case folder:`, run `case-setup` first. If `analysis/results-index.md` has no rows, run `ingest-results` first. A panel designed without records is guesswork.

## 1. Read the case

Read `AGENTS.md`, `notes/patient-history.md`, `notes/bedside-status.md`, both indexes, sections 1, 3, and 4 of `analysis/results-summary.md`, sections 5, 6, and 9 of `analysis/notes-summary.md`, and the newest change notes. If `panel/panel.md` exists, read it. This is a revision.

Build a working list with four parts:

- **Organ systems and problems in play.** Take them from results, notes, and family report.
- **Branches of the differential.** Include the team's working diagnosis, alternatives the notes mention, and alternatives the findings raise that nobody has written down.
- **Services already involved.** Take them from note authors and consult notes.
- **Decisions ahead.** Procedures, biopsies, imaging, discharge, and treatment choices the notes point to.

## 2. Interview where the records leave gaps

Ask the family only what changes the panel, in one short message:

- What they most want the conference to help them understand
- Any possibility they are worried about that the records do not mention
- Any upcoming decision or procedure they know about that the notes do not show yet
- Any specialty they have been told will be consulted

Skip questions the records or patient history already answer.

## 3. Choose the seats

Use [the specialty catalog](references/specialty-catalog.md) as a menu, never a fixed list.

- **Three to five specialist seats.** Pick the specialties that own the organ systems and diagnostic branches in play.
- **At least one unconsulted seat.** Include one specialty the notes show has not been consulted but whose view could change the picture. Explain why in one line.
- **Decision seats.** Add a seat for any pending decision that needs its own owner, for example interventional radiology for a biopsy route, or surgery for an operation.
- **Two fixed seats.** Every panel also gets the **clinical generalist** and the **evidence researcher**, briefed in `case-conference`. Do not write briefs for them here.

Give every seat a distinct framing, so the panel does not converge on one story. Framings to assign, one per seat where it fits:

- most likely explanation
- dangerous if missed
- what treatment or timing may be distorting the tests
- one disease that explains the most findings
- two diseases at once

Record each seat's framing in its brief.

## 4. Assign ownership

List every material finding, test, imaging study, procedure, and pending decision from the indexes. Assign each to exactly one seat. A finding with no owner gets reported on by nobody. A finding with two owners gets two half-answers. Unowned oddities, incidental findings, and general medical issues go to the clinical generalist.

## 5. Write the panel

Write `panel/panel.md`:

```
# Case conference panel

Designed <YYYY-MM-DD>. Revised <dates>.

## Roster
| Seat | Specialty and subspecialty | Why this case needs it | Consulted in chart? | Framing |

## Ownership map
| Finding, test, or decision | Owner | Source file |

## Fixed seats
Clinical generalist and evidence researcher, briefed by case-conference.

## Revision log
- <date>: <what changed and why>
```

Write one brief per specialist seat to `panel/seats/<seat-slug>.md`, following [the seat template](references/seat-template.md). The "Own" list is the heart of a brief. It must name specific findings and files from this chart.

## 6. Confirm

Show the family the roster and each seat's "Own" list in a few lines. Ask if they want to add, drop, or change a seat. Apply changes, then record the design in the Update log in `AGENTS.md`.

## Revisions

When rerun, keep seats that still fit, add seats for new services or organ systems, and retire seats whose branch is closed. Retire a seat only when a specific file closes its branch, and say which. Update the ownership map so every new finding has an owner. Log every change in the revision log. Never delete an old brief. Move it to `panel/seats/retired/`.
