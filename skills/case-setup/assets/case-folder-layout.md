# Case folder layout

`case-setup` creates every path below. Other skills refer to these files and to their numbered sections, so keep the headings exactly as written. Create each derived file with its headings and no content.

```
<case>/
  AGENTS.md                       from case-AGENTS.template.md
  CLAUDE.md                       one line: @AGENTS.md
  START-HERE.md                   from START-HERE.template.md
  Test Results/                   result PDFs
  Care Team Notes/                note PDFs
  Other Records/                  anything else
  notes/
    patient-history.md
    bedside-status.md
  panel/
    seats/
  analysis/
    results-index.md
    results-summary.md
    notes-index.md
    notes-summary.md
    recap-discrepancies.md
    data/
      notes-overrides.csv         header row only
    changes/
    questions/
    conference/
  consult/
  .advisor/
    identifiers.txt
```

The extract scripts write the rest of `analysis/data/`: `text/`, `notes-text/`, `other-text/`, `manifest.csv`, `notes-manifest.csv`, `other-manifest.csv`, `labs_long.csv`, `labs_wide.csv`, and `labs_trend.md`.

## notes/patient-history.md

```
# Patient history
Family report, gathered with patient-intake. The family is the primary source for history.

## Current situation and timeline
## Past medical history
## Surgeries and procedures
## Medications and supplements
## Allergies and reactions
## Family history
## Social history and exposures
## Baseline function before this episode
## Earlier workups and outside records
## The care team as the family knows it
## What the family most wants to understand, and what worries them
## Amendments
```

## notes/bedside-status.md

```
# Bedside status
Dated entries, newest first, from record-observations. Every entry is family report.
```

## analysis/results-index.md

One row per result file, grouped by category. Columns: priority (1 defines the case, 2 matters, 3 background), file, collected, finding with value, unit, and range, when to reach for it.

```
# Test results index
## Start here
## Not in the folder
```

Add one `##` section per category as results arrive, for example chemistry, blood counts, coagulation, microbiology, body fluids, imaging by region, pathology, endocrine, urine, other studies. "Not in the folder" lists tests the notes say were planned or sent whose results are not here, each with the note that names it.

## analysis/results-summary.md

```
# Results summary
## 1. The picture in one paragraph
## 2. Chronology
## 3. What the results establish, suggest, and leave open
## 4. Pending and missing
## 5. Questions for the care team, ranked
## 6. Method note
## Sources
```

Section 2 has one `###` heading per date, with a finding paragraph and an assessment paragraph for each study.

## analysis/notes-index.md

One row per note, grouped by service. Columns: priority, file, service time, finding, when to reach for it.

```
# Care team notes index
## What the notes carry that the results do not
## Start here
## Reading the notes
```

Add one `##` section per service in the order services joined the case, above "Reading the notes." "Reading the notes" records local quirks: misnamed files, clipped PDFs, carried-forward text.

## analysis/notes-summary.md

```
# Notes summary
## 1. What changed, by ingest
## 2. Timeline from the notes
## 3. Medications, reconstructed
## 4. History found only in the notes
## 5. The team's reasoning, as written
## 6. Plans written and not yet closed
## 7. Function and cognition, by measurement
## 8. Discharge and disposition
## 9. Where the notes leave the differential
## 10. Questions the notes raise
## Sources
```

Section 1 has one dated `###` block per ingest, newest first. Question numbers in section 10 continue from the highest number in `results-summary.md` section 5.

## analysis/recap-discrepancies.md

```
# Discrepancies
## Chart findings the family account does not contain
## Family statements the chart contradicts
## Family statements the chart neither confirms nor contradicts
## Notes versus results versus family report
## Corrections to raise in conversation
```

"Notes versus results versus family report" has one dated `###` block per ingest or observation entry.

## analysis/data/notes-overrides.csv

```
file,service_time,note_type,author,credential
```

Rows record the true metadata for any note whose file name does not match its content. `service_time` is `YYYY-MM-DD HH:MM`.

## analysis/changes/<YYYY-MM-DD>.md

One note per meaningful new input: an ingest, an observation entry that changes the picture, an intake amendment, a finished conference, or a consult. If one already exists for today, add a suffix: `-2`, `-3`, or a short slug such as `-conference`. Each note runs 300 words or fewer, is cited, and reads on a phone. The first line names what triggered it.

## .advisor/identifiers.txt

One identifier per line: the patient's full name and common variants, date of birth, record numbers, facility names, and clinician names as they appear. Skills check web queries against it and never quote it in any output.
