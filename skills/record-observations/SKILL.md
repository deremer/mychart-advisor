---
name: record-observations
description: "Captures what the family saw, heard, or was told at the bedside or at home since the last entry: changes in alertness, thinking, movement, eating, sleep, pain, or mood, new symptoms, reactions after a medication or procedure, and what a doctor or nurse said. Appends a dated entry to notes/bedside-status.md in the case folder and flags anything that conflicts with the chart. Use when someone says \"record an observation\", \"bedside update\", \"he seemed confused today\", \"the doctor told us\", \"log what happened\", or \"capture what the nurse said\". Also runs as the first step of ingest-results."
license: MIT
compatibility: Any agent that can read and write local files.
metadata:
  plugin: mychart-advisor
---

# Record bedside observations

<!-- guardrails:start -->
## Ground rules

This skill helps a patient and family understand the records, answer what a tool can answer, and bring sharper questions to the care team. The treating team makes the diagnosis and every treatment decision.

- Generate and rank possible diagnoses freely, including rare and dangerous-to-miss ones, and name the test that would settle each. That analysis is the point, so do not hedge it away. Word findings as "consistent with," "argues for," or "argues against," state how strong each inference is, and never state a diagnosis as fact.
- Never tell anyone to start, stop, or change a treatment or dose. Anything the team might do becomes a question to ask them.
- Contact no one. Every output goes to the family first, and they decide what to share.
- Keep everything in the case folder. Never copy records into memory, other projects, or shared tools. Never put a name, birth date, record number, facility, clinician name, or exact date into a web search or fetch.
- If anything suggests an emergency, say so first and plainly: call 911 or the local emergency number, or alert the care team now.
<!-- guardrails:end -->

The family sees the patient for hours, and the chart sees a few minutes a day. A family noticing a change at dinner, a reaction an hour after a new drug, or a sentence a doctor said in the hallway is evidence the records do not carry. This skill captures it quickly and accurately, while memory is fresh.

Work in the case folder. If there is no `AGENTS.md` beginning `# Case folder:`, run `case-setup` first. Read `AGENTS.md` and the most recent entries in `notes/bedside-status.md`.

## 1. Check for anything urgent

If the user's first words describe something that sounds urgent now, say plainly to call the care team or 911 before anything else. Examples: new trouble breathing, chest pain, sudden weakness or confusion, a fall, heavy bleeding, or a very high fever. Continue capturing only after they say it is handled.

## 2. Capture

Start open: "What have you noticed or been told since the last entry?" Let them talk. Then fill gaps with short follow-ups, only for areas they have not covered and only those relevant to the case.

- Alertness, orientation, memory, speech, behavior
- Movement, strength, walking, balance, falls
- Eating, drinking, swallowing, nausea, bowel and bladder
- Sleep, pain, mood, breathing, skin, swelling, fever
- Anything new or different from yesterday or from their normal
- Anything that changed after a medication, meal, procedure, or position change, and how long after
- What any doctor, nurse, or therapist said, and who said it
- What was planned or promised, such as a test, a result, or a visit, and whether it happened

For each item, get when (date and approximate time), who observed or who said it, and exactly what, in their words. Use numbers when the family has them: a reading on a home device, how many steps, how much of a meal. Do not turn a description into a clinical term. "Her words came out jumbled for a minute" stays as said.

Keep observation and interpretation apart. If the family adds a theory, record it on a separate "Family's thoughts" line.

## 3. Write the entry

Insert at the top of `notes/bedside-status.md`, below the file's intro lines:

```
## <YYYY-MM-DD HH:MM>, recorded by <who is reporting>

Observed:
- <time>, <who>: <what, in their words>

Told by the care team:
- <time>, <role or name as the family gave it>: <what was said>

Planned or promised:
- <what>, <by whom>, <status>

Family's thoughts:
- <theory or worry, labeled as such>
```

Leave out empty blocks. Read the entry back and ask whether it is right.

## 4. Compare with the chart

Search the note and result text in `analysis/data/` around the same times. Look for:

- A templated exam line that says the opposite of what the family saw
- A plan the family was told about that no note records, or a note's plan the family was never told
- A statement relayed by the family that a result contradicts
- A timing conflict

Log each conflict in `analysis/recap-discrepancies.md` under "Notes versus results versus family report," in a dated block. Cite the note or result with a numbered source, and cite the observation as family report.

## 5. Decide whether the picture changed

If the entry changes the picture, write a change note in `analysis/changes/` per the format in `AGENTS.md`, lead with the observation, and say which possibilities or open questions it bears on and how. Examples: a new symptom, a change that followed a medication, a conflict with the chart on something that matters, or news of a plan or result.

Generating possibilities here is expected. "New swelling in one calf after several days in bed is consistent with a clot in the leg. Ask whether an ultrasound is planned" is the right register. If the observation plausibly bears on something time-sensitive, say so at the top and suggest raising it with the care team today.

Add a line to the Update log in `AGENTS.md`. If this skill ran as step 0 of `ingest-results`, hand back to it.
