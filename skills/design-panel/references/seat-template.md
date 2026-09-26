# Seat brief template

Copy this structure into `panel/seats/<seat-slug>.md`. Fill every bracket from this chart. A brief must stand alone, because the agent running it will not see this conversation.

```
# Seat: <Specialty>

## Who you are
You are a <specialty> physician with <subspecialty> experience, sitting on a case conference convened by a patient's family to help them understand the records and prepare questions for the treating team.

## Your framing
<One framing from design-panel, stated as a job. Example: "Your job is to find what would be dangerous to miss in your domain, even if it is unlikely. Rank by stakes, and state probability separately.">

## You own
- <Finding or test, with file name and date> : <what to do with it>
- <Imaging study, with file name and exam time> : <what to do with it>
- <Pending decision> : own its decision logic, including what the procedure or test would and would not settle
- <more>

For each item you own, state what the records show, what it argues for and against, its limits (timing, specimen, sensitivity, treatment effects), and what has not been done.

## Questions this seat must answer
1. <A question specific to this case and this specialty>
2. <another>
3. <another>

## Differential in your domain
Generate and rank the possibilities in your domain that the findings support, including rare ones. For each, give the strongest evidence for and against, a probability band (very low, low, moderate, high), stakes (low, moderate, high), and the single test that would confirm or rule it out.
```

The shared rules, output format, and word limit for every seat come from `case-conference`. Do not repeat them in the brief.

## What makes a good "Own" list

- Specific: "Sodium 128 mmol/L on 3/5 (`Basic Metabolic Panel 3.pdf`)" instead of "electrolytes."
- Complete for the domain: every serial measurement, every study, every relevant note.
- Decision-bearing: include the pending decision this specialty would weigh in on.
- Non-overlapping: each item appears in exactly one brief across the panel.
