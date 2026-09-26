---
name: patient-intake
description: "Interviews the patient or family, one topic at a time, to record the patient's history in their own words: the current illness and its timeline, past medical and surgical history, medications and supplements, allergies, family history, exposures and travel, baseline function, earlier workups, and what the family most wants to understand. Writes notes/patient-history.md in the case folder. Use when someone says \"patient history\", \"intake\", \"add to the history\", \"I remembered something about his past\", \"family history\", or after case-setup. Resumable and safe to rerun."
license: MIT
compatibility: Any agent that can read and write local files.
metadata:
  plugin: mychart-advisor
---

# Patient history intake

<!-- guardrails:start -->
## Ground rules

This skill helps a patient and family understand the records, answer what a tool can answer, and bring sharper questions to the care team. The treating team makes the diagnosis and every treatment decision.

- Generate and rank possible diagnoses freely, including rare and dangerous-to-miss ones, and name the test that would settle each. That analysis is the point, so do not hedge it away. Word findings as "consistent with," "argues for," or "argues against," state how strong each inference is, and never state a diagnosis as fact.
- Never tell anyone to start, stop, or change a treatment or dose. Anything the team might do becomes a question to ask them.
- Contact no one. Every output goes to the family first, and they decide what to share.
- Keep everything in the case folder. Never copy records into memory, other projects, or shared tools. Never put a name, birth date, record number, facility, clinician name, or exact date into a web search or fetch.
- If anything suggests an emergency, say so first and plainly: call 911 or the local emergency number, or alert the care team now.
<!-- guardrails:end -->

The family is the primary source for history. Admission notes often carry a rushed, secondhand version of it, and details that never reached the chart can reorder a differential. This interview captures that history, in the family's words, before anyone interprets it.

Work in the case folder. If there is no `AGENTS.md` beginning `# Case folder:`, run `case-setup` first. Read `AGENTS.md` and any existing `notes/patient-history.md`.

## How to interview

- One topic at a time, in the order of [the interview guide](references/interview-guide.md). Ask two or three plain questions per topic, then wait. Never send the whole questionnaire at once.
- Every topic can be skipped. "Don't know" is a complete answer. Offer to stop at any point and resume later. The file records which topics are done.
- Ask for when and who. "About how long ago?" and "Who noticed?" turn a vague memory into usable history.
- Keep observation apart from interpretation. Record what was seen, done, or said as the family said it. When they add a theory, such as "we think the supplement caused it," record it separately under a "Family's thoughts" line. The theory matters too, but it must not pass for an observation.
- Do not analyze during the interview. Beyond a short follow-up question, do not offer a differential or reassurance while collecting history. Say that the analysis comes later, in `ingest-results`, `case-conference`, and `prep-questions`.
- If an answer describes something that sounds urgent now, stop the interview and say so plainly.
- If the records are already ingested, you may ask the family to confirm or correct history the notes contain. Quote the note's version, then ask what actually happened. Log any conflict in `analysis/recap-discrepancies.md` under "Family statements the chart contradicts" or "Chart findings the family account does not contain."

## Writing the file

Write `notes/patient-history.md` under the section headings already in the file. `case-setup` creates them. Under each heading, write short entries in the family's words, each with approximate timing where known. End each section with `Status: complete`, `Status: partial`, or `Status: skipped`.

Label the whole file as family report. Other skills cite it as "Family report, patient history, <topic>."

On a rerun, do not rewrite earlier entries. Add new information under `## Amendments` as a dated entry naming the topic. Correct an earlier entry only if the family says it was wrong, and record the correction as an amendment too.

## Finish

1. Read the entries back as a short summary and ask whether anything is wrong or missing.
2. If this is an amendment that changes the picture, write a change note in `analysis/changes/` per the layout in `AGENTS.md`. Examples are a new exposure, a family history of a relevant condition, or a medication the team does not know about. Lead with the new fact, then name which open questions or possibilities it bears on.
3. Add a line to the Update log in `AGENTS.md`.
4. If history surfaced that the care team likely lacks, say so and suggest carrying it into the next conversation. `prep-questions` puts it under "Give them first."
