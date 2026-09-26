---
name: prep-questions
description: "Prepares a short, ranked, record-grounded question list for an upcoming conversation with the care team: a one-screen card to use in the room and a detail section with reasons, sources, and what a good answer sounds like. Tailors the list to who the conversation is with and how much time there is, and skips questions the records or the tool can already answer. Use when someone says \"prep questions\", \"what should we ask\", \"rounds tomorrow\", \"family meeting\", \"call with the doctor\", \"before we talk to the specialist\", or \"what do I ask the nurse\"."
license: MIT
compatibility: Any agent that can read and write local files.
metadata:
  plugin: mychart-advisor
---

# Prepare questions for the care team

<!-- guardrails:start -->
## Ground rules

This skill helps a patient and family understand the records, answer what a tool can answer, and bring sharper questions to the care team. The treating team makes the diagnosis and every treatment decision.

- Generate and rank possible diagnoses freely, including rare and dangerous-to-miss ones, and name the test that would settle each. That analysis is the point, so do not hedge it away. Word findings as "consistent with," "argues for," or "argues against," state how strong each inference is, and never state a diagnosis as fact.
- Never tell anyone to start, stop, or change a treatment or dose. Anything the team might do becomes a question to ask them.
- Contact no one. Every output goes to the family first, and they decide what to share.
- Keep everything in the case folder. Never copy records into memory, other projects, or shared tools. Never put a name, birth date, record number, facility, clinician name, or exact date into a web search or fetch.
- If anything suggests an emergency, say so first and plainly: call 911 or the local emergency number, or alert the care team now.
<!-- guardrails:end -->

Time with doctors and nurses is short. Spend it on what only they can answer: their interpretation, their plan, their timing, and what they have not yet considered. Anything the records already answer, answer here first so the family does not spend a question on it.

Work in the case folder. If there is no `AGENTS.md` beginning `# Case folder:`, run `case-setup` first.

## 1. Read

Read these files first:

- `AGENTS.md` and `notes/bedside-status.md`
- `notes/patient-history.md`
- `analysis/results-index.md` and sections 3 to 5 of `analysis/results-summary.md`
- `analysis/notes-index.md` and sections 1, 6, 9, and 10 of `analysis/notes-summary.md`
- `analysis/recap-discrepancies.md`
- the latest `analysis/conference/*/conference-note.md` and the latest `consult/*/report.md`, if they exist
- the latest change notes
- earlier `analysis/questions/*.md`, so you know what was already asked and answered

## 2. Ask two things, unless already stated

- **Who the conversation is with.** For example the attending, a consulting service, the hospitalist, a nurse, radiology, the outpatient physician, a case manager, a patient advocate, or a family meeting with several services. Tailor the questions to what that person controls and knows.
- **How much time there is.** A bedside check-in gets three to five questions. A scheduled meeting gets up to eight on the card and ten in the detail.

## 3. Answer what the tool can answer

Before drafting, list the family's own open questions from the bedside log, the patient history, and anything they said this session. Answer any that the records settle, briefly and with citations, in an "Already answered from the records" block in the detail section. Examples: what a result means, whether a test came back, what a term in a note means, or how a value has trended. Those questions come off the card.

## 4. Draft the questions

Every question must trace to a file in the folder or to an entry under "Not in the folder" in the results index. No questions from general curiosity.

Rank them by how much the answer would change the path. Prefer questions that unlock several others. "Which tests were sent on the fluid sample, and when do you expect each?" beats five separate pending-result questions.

Include:

- **The differential.** At least one question about the possibilities the analysis ranks highly, which the notes do not show the team addressing. Phrase it as "Has X been considered? What would rule it in or out?"
- **Timing.** One question about timing and decision points. Families lose the most ground when nobody names a date.
- **Discrepancies.** A question for any discrepancy worth correcting.

Questions ask what, when, whether, and how the team interprets. They never tell the team what to do. "Has a repeat culture been sent?" is right. "You should repeat the culture" is wrong. Skip questions the notes show were already answered, unless the answer has gone stale.

## 5. Write the sheet

Write `analysis/questions/<YYYY-MM-DD>-<audience-slug>.md` and show it in the reply.

**The card comes first and must fit on one phone screen.** No citations on the card.

```
# <Audience>, <date>

**Give them first:** <history or observations the chart lacks, as fragments>

**Ask:**
1. <one line, spoken form, no reasons, no file names>
2. ...

**Write down:** <two or three facts to capture before leaving: names, dates, decision points>

**If time:** <overflow questions as fragments separated by periods>
```

Test the card by reading it aloud. If any line takes more than one breath, cut it.

Then a horizontal rule and `# Detail`, containing:

1. **Two opening sentences** the family can say aloud, showing they have read the records and framing the conversation as collaborative. For example: "We've been following the results in the portal and want to make sure we understand them. We have a few specific questions."
2. **Already answered from the records**, from step 3.
3. **The questions, ranked.** Each has three consecutive lines:
   - the question as spoken, one plain, non-leading sentence
   - the reason, one sentence a physician would find fair, with citations
   - what a good answer sounds like, so the family knows whether they got one
4. **If there is time.** A short list.
5. **After the conversation.** A reminder to run `record-observations` to log what was said, so the next analysis starts from it.

End with `## Sources` and the output footer from `AGENTS.md`.
