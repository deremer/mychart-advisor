# Ingest reference

Row formats, writing rules, and worked patterns for `ingest-results`. The examples use invented values.

## Contents

1. Index rows
2. Summary paragraphs
3. Medication reconstruction
4. Discrepancy entries
5. Change notes
6. Imaging times
7. Carried-forward text
8. Qualitative and odd results
9. Absence claims

## 1. Index rows

Both indexes are lookup tables, so file names appear in the row and no citations are needed.

`analysis/results-index.md`:

```
| Pri | File | Collected | Finding | Reach for it when |
|---|---|---|---|---|
| 1 | `Basic Metabolic Panel 3.pdf` | 3/5 6:05 AM | Sodium 128 mmol/L (136 to 145), down from 134 on 3/3 | Tracking the sodium trend or fluid plan |
| 2 | `Blood Culture 2.pdf` | 3/4 9:10 PM | "No growth at 5 days" | Asked whether the fever source was found |
```

Priority 1 means the result defines the case. Priority 2 means it matters to a live question. Priority 3 is background. Put priority 1 rows under "Start here" as well as in their category. For results with no number, quote the result text exactly.

`analysis/notes-index.md`:

```
| Pri | File | Service time | Finding | Reach for it when |
|---|---|---|---|---|
| 1 | `Consult Note by <author> at <time>.pdf` | 3/4 1:20 PM | Attestation: "<quoted sentence>" | Need the consultant's plan of record |
```

Quote the attestation, or the sentence newly appended to the assessment, rather than paraphrasing it. Flag in the row when a note carries forward text from an earlier note, or contradicts another note or a result.

## 2. Summary paragraphs

In `results-summary.md` section 2, each study gets two paragraphs under its date.

- **Finding.** What the study showed, with numbers, units, ranges, and times, cited.
- **Assessment.** What it argues for and against across the current differential, how strong the inference is, what its limits are (timing, specimen, sensitivity), and what it leaves open. This is where the analysis lives. Name possibilities concretely.

Section 3 separates what the results establish from what they suggest and what they leave open. Keep the three distinct. Section 4 lists pending results, results not yet in the folder, and tests the notes mention but whose results are missing. Section 5 holds questions for the care team, ranked by how much the answer would change the path. Each question cites the file that motivates it.

When a new result makes an earlier sentence wrong, rewrite the sentence. Do not append a correction below it. The summary is current truth. History lives in `analysis/changes/`.

## 3. Medication reconstruction

`notes-summary.md` section 3 is a table rebuilt from note medication lists, pharmacy notes, and plans:

```
| Drug | Dose and route | Started | Changed | Stopped | Source |
```

Record what was given where notes say so, and what was ordered, and say which is which. A drug ordered is not proof a drug was given. When the family's account of home medications differs from the admission list, log it as a discrepancy.

## 4. Discrepancy entries

```
### <YYYY-MM-DD> ingest

- <Note or result> says <X> [n]. <Other source> says <Y> [m]. <Which source the rules in AGENTS.md favor and why>. <Whether it matters, and to what>.
```

End the file's discrepancy section with sources. If a discrepancy is worth raising with the team, add it under "Corrections to raise in conversation" in plain words the family could say aloud.

## 5. Change notes

```
# What changed, <date>

**A case conference is recommended: <reason>.**   (only when triggered)

<What arrived, in one sentence.>

<What it says. Numbers with units, ranges, and times. Cited.>

<What it changes: which possibilities it strengthens or weakens, and how much.>

<The question it raises for the care team.>

## Sources
1. ...

> Prepared to help the family understand the records and prepare questions for the care team. Not a diagnosis or medical advice. The treating team makes all decisions.
```

Keep it to 300 words or fewer. No jargon without a gloss. The reader is intelligent, tired, and on a phone.

## 6. Imaging times

The collected line on an imaging result is often the order time. The exam time appears in the narrative, a technologist line, the footer, or a procedure note. Record both, and use the later one as the exam time. This matters most when a treatment started between order and exam, because the treatment can change what the study could show.

## 7. Carried-forward text

A sentence repeated across notes is one observation, not many. Find the first note it appeared in. Templated physician exam lines are carried forward until something independent agrees: a therapy measurement, a nursing observation, an attestation, or the family. When a templated line conflicts with a measured one, the measured one wins, and the conflict is logged.

## 8. Qualitative and odd results

- Quote qualitative results exactly: "Not detected," "Nonreactive," "Positive (A)."
- Read lab comments. A comment about a hemolyzed, clotted, delayed, diluted, or out-of-stability specimen changes what the result means. Say so in the assessment.
- Send-out and miscellaneous orders often hide the real test name in the body. Index them under what the test actually is, and note the portal's name.
- A released page with no result printed goes in the index as "released, no result printed," and the test stays under "Not in the folder."

## 9. Absence claims

Before writing that a test was not done, search the extracted text for the generic clinical word, the common abbreviation, and brand or assay names. Then write "not found in the released records (searched: <terms>)." Never write "not done."
