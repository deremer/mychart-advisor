# Consult roles

Prompts for every role, and which roles each preset runs. Every blind prompt begins with: "Read `<snapshot>/AGENTS.md` first and follow it exactly. Your snapshot directory is `<snapshot>`." Every prompt ends with the output format, including the JSON block from `schemas.md` where one is named.

## Contents

1. Presets
2. Blind stage: fact base, generators, triage, investigators, red team, second round, test planner
3. Synthesis stage: reconciler, synthesizer, verifiers, fixer, directive scan

## 1. Presets

| Phase | Standard, about 10 agents | Deep, about 28 | Max, 35 or more |
|---|---|---|---|
| Fact base | 2 extractors: results and imaging; notes and course | 4 extractors by domain | 4 |
| Generators | 2: core outward; periphery and exposures | 3 | 5, adding two with fresh framings |
| Triage | orchestrator | 1 agent | 1 |
| Investigators | 3, families grouped | one per family, about 9 | one per family with infectious split, about 12 |
| Red team | 1 combined | 4 | 4 |
| Second round | orchestrator folds into the synthesizer | 1 | 2 |
| Test planner | folded into the synthesizer | 1 | 1 |
| Reconciler | 1 | 1 | 1 |
| Synthesizer | 1 | 1 | 1 |
| Verifiers | 1 | 2 | 3 |
| Fixer | orchestrator | 1 | 1 |
| Directive scan | script only | script only | 1 agent |

Rough benchmark from real use of the deep preset: about 6 to 7 million subagent tokens, and two to three hours of wall time when only two agents can run at once. More concurrency is proportionally faster. Scale standard and max from that, and tell the user the estimate before launching.

## 2. Blind stage

Every blind unit runs as a blind-reader agent, with description prefix `consult-blind:`.

### Fact base

Split the records by domain. The default split for a general medical case has four domains:

1. specimen-based diagnostics: fluid studies, pathology, microbiology
2. imaging
3. blood, urine, and systemic labs
4. clinical course: history, exposures, exam by instrument, medications with dates given, and function scores

Standard mode merges these into two extractors, results and imaging, and notes and course. Choose a different split when the case calls for it.

> Extract every fact in your domain from the snapshot. Tag each item as measurement, observation, or clinician interpretation. Cite the file and time. Keep serial values as tables with units and ranges. Note specimen-quality comments and exam-versus-order times. End with two lists: never tested or not in the records, with the search terms you used, and internal contradictions between records. Stay under 6,000 words.

### Generators

Each generator gets a different entry point and never sees another's list. All of them read the fact-base outputs, which the orchestrator places in the snapshot's `work/` directory, plus the snapshot itself.

- **Core outward.** Start from the defining combination of findings and their tempo, and list every published cause, including rare ones.
- **Periphery inward.** Start from findings outside the primary organ system. Look for one disease that explains several of them, and list findings nothing explains.
- **Exposures and host.** Start from exposures, geography, travel, occupation, host factors, supplements, medications, and procedures, including ways drugs or procedures could distort the picture or the tests.
- **Max adds:** "dangerous if missed," which ranks by stakes, and "two diseases at once."

> Produce at least 20 hypotheses. For each, give its fit, its conflicts, and the tests already bearing on it. Include hypotheses about the mechanism of the main symptom that may be separate from the underlying cause. Return the generator JSON block.

### Triage

> Merge true duplicates only, and record each merge. Assign every hypothesis to a family from `family-taxonomy.md`, adapted to this case. Drop nothing for being unlikely. Top up any family with fewer than four members. Return the family list with members.

### Investigators

One per family, or grouped in standard mode.

> For each hypothesis in your family, weigh the evidence for and against, with citations. Give the literature sensitivity and specificity of each test already run, adjusted for timing, specimen, repetition, and drug exposure. Say whether tests share a failure mode. Assign a status, your confidence in that status, a probability band, and stakes, as separate fields. List the next discriminating tests, with what a positive and a negative would each mean, and the burden of each. Stay under 4,000 words and return one ledger JSON row per hypothesis.

### Red team

Four roles in deep and max. Standard mode combines them into one prompt that does all four, briefly.

- **Attack the leader.** Make the strongest honest case that the leading hypothesis is wrong or incomplete, both the treating team's (from the notes) and the ledger's. Say what it predicts that nobody has looked for. If the records support it, say so. Do not manufacture doubt.
- **Attack the exclusions.** For every excluded or unlikely row, ask four things: was the negative test the right test, on the right specimen, at the right time, and repeated enough? Flag any exclusion that rests on a clinician statement rather than a result.
- **Attack the framing.** Is there really one disease? Is the category right? Is the timeline right? List every internal contradiction between records.
- **Completeness critic.** Build the union of published differentials for the defining presentation from the literature and compare it with the ledger. List missing diagnoses and diagnostic methods nobody used.

> Return challenges with a severity and a proposed change, plus new hypotheses, in the red-team JSON block.

### Second round

> Investigate each new hypothesis from the red team, in the same ledger format. Mark duplicates of existing rows.

### Test planner

> Consolidate every discriminating test from the ledger into parallel bundles: held specimens, one blood and urine draw, imaging, bedside exam and history, any planned procedure, and tissue. Rank within each bundle by uncertainty removed per unit of risk. Frame each test as a question for the treating team. Also list pending results to chase, safety items to check before any procedure, history questions for the family with the hypothesis each would move, and the hypotheses that will stay open after every reasonable test.

## 3. Synthesis stage

### Reconciler

Not blind. Use a general agent. It reads the blind outputs in `work/`, then the treating team's trajectory in the notes, then `prior/`.

> Report five things. First, where the blind team and the treating team agree. Second, where they diverge, which side the records favor, and how strongly. Third, what the prior analysis asserted that the records do not support. Fourth, what the prior analysis had that the blind team missed. Fifth, findings in the newest records nobody has absorbed. Close with the divergences that matter most in the next 48 hours. Neither side is right by default. Write `reconciliation.md` content as your final message.

### Synthesizer

Blind. It reads the blind outputs in `work/` and `reconciliation.md`, which the orchestrator copies into the snapshot's `work/`. It never reads `prior/` directly.

> Write the report from `report-template.md`. Tier by probability and flag high stakes in every tier. Keep every citation traceable to a snapshot text file, which maps to the original PDF by file name. Stay under 7,000 words, not counting the appendix.

### Verifiers

Deep mode runs two in parallel. Standard mode runs one that does both jobs.

- **Numbers and quotes.** Check every number, unit, range, date, time, and quotation against the snapshot text, and confirm that each cited file contains the fact.
- **Absences, literature, citations, and style.** Re-run every absence claim with specific and generic terms. Check every literature figure against its source. Check citation integrity. Check for directive language, and for over-hedging that buries a possibility the evidence supports.

> Return the verifier JSON block and a count of assertions checked.

### Fixer

> Apply each correction after confirming it against the source. Return the corrected report in full.

### Directive scan

Max only. The script `style_check.py` always runs as well.

> Find any sentence that tells anyone to start, stop, or change a treatment, or that states a diagnosis as fact. Rewrite each as a question for the treating team or as "consistent with." Leave differentials that are properly worded untouched.
