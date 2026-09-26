# Report template

`consult/<date>/report.md`. Plain sentences a family can follow and a physician can check. Lead with the answer. Prose over bullets, except where a table is clearer. Values keep their unit, reference range, and date in the sentence. Only file names move to the sources.

```
# Independent consult, <date>

> Prepared to help the family understand the records and prepare questions for the care team. Not a diagnosis or medical advice. The treating team makes all decisions. If anything here suggests an emergency, call 911 or alert the care team now.

## 1. What this is and how it was done
The blind team, the preset and agent count, what it could see (counts from SNAPSHOT.md), what it could not see, the number of hypotheses considered, and the snapshot freeze time.

## 2. Bottom line
About 250 words. The leading explanations and how strong each is. The possibility most worth ruling out. The handful of questions and tests that matter most in the next 48 hours.

## 3. What the records establish
One table for the core serial measurements. A short imaging section that lists every disagreement between reads. Specimen or timing problems that change what a result means.

## 4. The leading hypothesis under attack
Both the treating team's working diagnosis and the ledger's leader. The strongest honest case that each is wrong or incomplete, and what each predicts that has not been looked for. If the records support the leader, say so plainly.

## 5. What cannot be ruled out
Four tiers, each a table with hypothesis, probability, stakes, strongest for, strongest against, and settling test. Flag high-stakes rows with **High stakes** in every tier.
### Live
### Open or untested, and cheap to test
### Unlikely but not excluded, with the specific weakness of the test that lowered it
### Excluded, with why the test was adequate

## 6. Processes that may drive the main symptom on their own

## 7. Safety items that stand whatever the diagnosis

## 8. Test plan
Parallel bundles:
- held specimens
- one blood and urine draw
- imaging
- bedside exam and history
- any planned procedure
- tissue

Rank within each bundle by uncertainty removed per unit of risk, with each test framed as a question for the treating team. Add pending results to chase.

## 9. Where this consult differs from the treating team and from prior analysis
Which way the records point on each difference, and how strongly.

## 10. History questions for the family
Each tied to the hypothesis it would move.

## 11. Limits of this consult

## 12. Appendix: the full ledger
One table.

## Sources
```

Citations are numbered brackets after the clause they support, per the case `AGENTS.md`. Record sources cite the original PDF file name with its folder and time. Literature entries carry the publisher or author, title, venue, year, and URL.

## Addenda

An addendum goes after the Sources section, as `## Addendum, <date>`, with its own `### Sources` list. It never edits the verified body. It states which new files arrived, whether any changes a tier or a claim in the body, and how.
