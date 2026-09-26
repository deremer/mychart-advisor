# Sanitizing family notes for the blind team

Family observations are valuable evidence and often carry interpretation. The blind team should see what the family saw and when, not what the family concluded.

## Inputs

`notes/bedside-status.md`, `notes/patient-history.md`, and any `family-recap*.md` in the case folder.

## Task

Run this as one unit. Any agent type works, because this step is not blind. Rewrite the inputs into `consult/<date>/family-observations.md`:

- **Keep** what was seen, heard, measured, or done, when, and by whom. Keep stated history such as medications, exposures, family history, and baseline function, in the family's words where possible. Keep what staff said, attributed as "family reports being told by <role>."
- **Remove** every theory, "because," "which means," "we think," "ruled out," "caused by," judgment of a clinician, and "why this matters" passage. Remove any statement about what a test showed unless the family is quoting a number they were told. The blind team reads the records for results.
- **Keep dates and times.** Replace names with roles, such as "spouse" or "morning physician."
- **Structure it** as dated entries, oldest first, then a history section by topic.

## Review

Show the user the sanitized file before the run. Ask whether it is accurate and whether anything they consider important was removed. Record their approval in `inputs.md`. Pass the approved file to `build_snapshot.py` with `--family-observations`.
