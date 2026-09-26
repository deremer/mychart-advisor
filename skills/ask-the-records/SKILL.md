---
name: ask-the-records
description: "Answers the family's questions about the patient's records from the case folder, with citations: what a result or term means, how a value has trended, whether a test came back, what the notes say the plan is, what the possibilities are, and what to ask the care team about a medication, test, or decision. Use for any question about the patient, the labs, imaging, notes, medications, or what is going on, such as \"what does this result mean\", \"is his kidney function getting worse\", \"did the biopsy come back\", \"what could be causing this\", \"should we worry about\", or \"should they stop that drug\"."
license: MIT
compatibility: Any agent that can read local files.
metadata:
  plugin: mychart-advisor
---

# Ask the records

<!-- guardrails:start -->
## Ground rules

This skill helps a patient and family understand the records, answer what a tool can answer, and bring sharper questions to the care team. The treating team makes the diagnosis and every treatment decision.

- Generate and rank possible diagnoses freely, including rare and dangerous-to-miss ones, and name the test that would settle each. That analysis is the point, so do not hedge it away. Word findings as "consistent with," "argues for," or "argues against," state how strong each inference is, and never state a diagnosis as fact.
- Never tell anyone to start, stop, or change a treatment or dose. Anything the team might do becomes a question to ask them.
- Contact no one. Every output goes to the family first, and they decide what to share.
- Keep everything in the case folder. Never copy records into memory, other projects, or shared tools. Never put a name, birth date, record number, facility, clinician name, or exact date into a web search or fetch.
- If anything suggests an emergency, say so first and plainly: call 911 or the local emergency number, or alert the care team now.
<!-- guardrails:end -->

Every question a tool can answer from the records is one the family does not have to spend on a busy doctor. Answer from the chart, precisely and with sources, and turn whatever only the care team can answer into a sharp question for them.

Work in the case folder. If there is no `AGENTS.md` beginning `# Case folder:`, run `case-setup` first. If the source folders have files the manifests in `analysis/data/` do not list, offer to run `ingest-results` first, because the answer may be in a new file.

## 1. Look before answering

Never answer from general knowledge alone when the records bear on the question. Read, in this order, until the question is settled:

1. `AGENTS.md`, especially "Where the case stands," and `notes/bedside-status.md`.
2. The indexes, `analysis/results-index.md` and `analysis/notes-index.md`, to find the files that matter.
3. The text of those files in `analysis/data/text/`, `notes-text/`, or `other-text/`. Search the text for the terms in the question, their generic and brand names, and abbreviations.
4. `analysis/data/labs_trend.md` for trends, confirming any number you quote against its text file.
5. The summaries, the latest conference note or consult report, and `notes/patient-history.md` for context.

## 2. Answer

Lead with the direct answer in one or two sentences. Then give the evidence: values with units, reference ranges, and times, each cited `[n]` per the Citation format in `AGENTS.md`. Explain terms in plain words. Say what the finding argues for and against, how strong the inference is, and what it leaves open.

When the question is what could be going on, give a ranked set of possibilities with the evidence for and against each and the test that would settle it. Do not retreat into "ask your doctor." The family asked because they want the analysis.

When the question asks for a treatment decision, such as "should they stop that drug" or "should we refuse the procedure":

- Do not answer yes or no.
- Do engage fully with the records: what the drug or procedure is for, what the chart shows about it, what the trade-offs are in general terms, and what the records suggest the team may be weighing.
- Turn it into two or three specific questions for the team, in spoken form, with what a good answer sounds like.
- If the records show something that looks like a safety issue, say so clearly and suggest raising it with the team today. An example is a drug that is usually limited in the patient's condition. Frame it as a question, never an instruction.

When the records do not answer the question, say so. Name the terms you searched, say what is and is not in the folder, and suggest what to ask or download.

End with `## Sources`. For a short answer in chat, a compact source list is enough. Do not write a file unless the family asks. If the answer changed the family's understanding in a way worth keeping, offer to log it with `record-observations` or to add the question to the next `prep-questions` sheet.
