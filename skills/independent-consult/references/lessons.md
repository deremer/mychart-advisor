# Design principles

Why the consult is built the way it is. Read this before changing the pipeline.

1. **Blinding is the product.** A team that has read the treating team's conclusions, or the family's prior summaries, reproduces them. The blind half starts without the case instructions in context and reads only a frozen snapshot.
2. **Clinician interpretation is a hypothesis.** Notes are records, so they are in the snapshot, but assessments and plans rank below measurements and observations.
3. **Probability and stakes are separate fields.** A possibility can rank high because it is dangerous to miss, not because it is likely. The ledger records both, and the report tiers by probability while flagging high stakes in every tier.
4. **Negative tests are rarely independent.** Several negatives that share a failure mode cannot be multiplied.
5. **Exact report wording matters.** Certainty categories in pathology and imaging are fixed. Quote them.
6. **Check confirmations for independence.** A read made after the reader knew the first result is not independent. Compare timestamps.
7. **Carried-forward documentation is weak.** A measured therapy or nursing finding beats a templated exam line.
8. **Specimen quality is part of the result.** Contamination, dilution, deviations, delays, and drug timing change what a negative means.
9. **Absence claims are claims about search terms.** Tests hide under unexpected names.
10. **Time-critical findings go out now.** Safety items and anything that changes a planned procedure go to the user mid-run, marked preliminary.
11. **Verification is mandatory.** Independent verifiers routinely find errors in about one of every ten checked assertions, some serious. No report ships unverified.
12. **Diversity beats headcount.** Agents given the same framing converge. Each generator and red-team role gets a different entry point, and none sees another's work until it has written its own.
13. **Do not manufacture doubt.** When the records support the treating team, the report says so plainly. The red team argues honestly, not reflexively.
