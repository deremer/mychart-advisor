# mychart-advisor

Agent skills that help patients and families make sense of hospital and clinic records exported from a patient portal such as Epic MyChart. You download results and notes as PDFs into a folder. The skills turn that folder into organized, cited, dated understanding, surface the possibilities the evidence supports, and prepare sharp questions for the care team.

> **This tool does not diagnose and does not direct care.** The treating team makes the diagnosis and every decision. mychart-advisor helps you understand what the results and notes mean, follow trends, see the full range of possibilities and the tests that would settle them, and spend your limited time with doctors and nurses on what only they can answer.
>
> **If you think the patient is having an emergency, call 911 or your local emergency number, or alert the care team now.**
>
> Read [DISCLAIMER.md](DISCLAIMER.md). Not affiliated with Epic Systems.

It runs in Claude Code and Claude Cowork, and the skills follow the open [Agent Skills](https://agentskills.io) format, so they also work in Codex, Gemini CLI, Cursor, GitHub Copilot, and other agents.

## Contents

1. [What it does](#what-it-does)
2. [Install](#install)
3. [Requirements](#requirements)
4. [Getting records out of MyChart](#getting-records-out-of-mychart)
5. [First run](#first-run)
6. [Ongoing use](#ongoing-use)
7. [Case conferences and independent consults](#case-conferences-and-independent-consults)
8. [Privacy](#privacy)
9. [Other portals and other AI tools](#other-portals-and-other-ai-tools)
10. [Contributing](#contributing)

## What it does

| Skill | What it does | When to use it |
|---|---|---|
| `case-setup` | Creates the case folder and records the basic facts. | Once, at the start. |
| `patient-intake` | Interviews you, one topic at a time, about the patient's history: the current illness, past conditions, medications and supplements, family history, exposures, and baseline function. | Right after setup, and whenever you remember more. |
| `record-observations` | Captures what you saw, heard, or were told at the bedside, and checks it against the chart. | Any time, and automatically at the start of each ingest. |
| `ask-the-records` | Answers your questions from the chart, with citations: what a result means, how a value is trending, whether a test came back, what the possibilities are. Turns what only the team can answer into sharp questions. | Any time you have a question. |
| `ingest-results` | Extracts new PDFs, builds lab trend tables, updates indexes and summaries, flags conflicts, and writes a short what-changed note you can read on a phone. | Every time you download new files. |
| `design-panel` | Chooses the specialists this case needs for a case conference, such as oncology, radiology, or a service the team has not consulted yet. | Once before the first conference, and when the case shifts. |
| `case-conference` | A panel of specialist agents reviews the chart in parallel, a contrarian attacks the consensus, and a synthesizer writes a ranked differential with open disagreements and questions. A second reader verifies every claim. | After a big new result or before a big decision. |
| `prep-questions` | A one-screen question card for the room, plus a detail sheet with reasons and sources. Answers first whatever the records already settle. | Before rounds, a call, or a family meeting. |
| `independent-consult` | A blinded team that has not seen anyone's conclusions generates every hypothesis the records cannot rule out, investigates each, red-teams itself, and delivers one verified report with a test plan. | When you want a fresh, unanchored second look. |

Every output cites the exact file behind each number, keeps family report separate from the chart, and ends at a human gate. Nothing goes to anyone until you have read it.

## Install

**Claude Code**

```
/plugin marketplace add deremer/mychart-advisor
/plugin install mychart-advisor@mychart-advisor
```

**Claude Cowork.** Add the marketplace `deremer/mychart-advisor` in the plugin settings, install `mychart-advisor`, and give Cowork access to the folder where you will keep the case.

**Codex**

```
codex plugin marketplace add deremer/mychart-advisor
```

**Any other agent.** Install just the skills with the cross-agent installer:

```
npx skills add deremer/mychart-advisor
```

Add `-a <agent>` to target a specific agent and `-g` to install for your user account. The Claude-only extras need the plugin install: the web-search privacy hook, the blind-reader agent, and the optional workflows.

## Requirements

- Python 3.10 or later.
- One of these for reading PDFs:
  - **poppler**: `brew install poppler` on macOS, or `apt install poppler-utils` on Linux. Recommended.
  - **pdfplumber**: installed automatically if you have [uv](https://docs.astral.sh/uv/), or `pip install pdfplumber`.
- Optional: [OCRmyPDF](https://ocrmypdf.readthedocs.io) for scanned pages. Without it, the agent reads scanned pages directly.
- Optional: Chrome, Chromium, or Edge to render the consult report as a PDF.

## Getting records out of MyChart

v1 works from PDFs, one per result and one per note.

1. **Sign in to MyChart** on a computer. The web version makes downloading easier than the phone app. If you manage a relative's records, use proxy access, which the health system grants on request.
2. **Test results.** Open Test Results, then open each result. Use the print or download option and save it as PDF into the case folder's `Test Results/` folder. Keep the file name MyChart suggests.
3. **Care team notes.** Notes live under Visits, Notes, or a hospital stay's details, depending on the health system. Open each note, save it as PDF, and put it in `Care Team Notes/`.
4. **Everything else.** Medication lists, discharge papers, letters, outside records, and phone photos of paperwork go in `Other Records/`.
5. **How often.** During a hospital stay, once or twice a day works well. Results are often released to the portal as soon as they are final, sometimes before the doctor has discussed them. Download new items and run `ingest-results`. Duplicates are harmless. The scripts track what they have already seen.

Other routes exist and are worth knowing about:

- **Download or Export in MyChart.** Some health systems offer a "Download My Record" or "Lucy" option under the Health or Sharing menus. It produces a ZIP with a summary and structured files in C-CDA format.
- **A request to Health Information Management.** The hospital's records office can send the complete record. This takes days, and imaging and some notes may come separately.
- **FHIR patient-access apps.** Federal rules require patient-facing APIs. Apps that use them need their own registration.
- **Browser export tools.** Open-source tools such as [mychart-takeout](https://github.com/jmandel/mychart-takeout) export your records from inside your own logged-in browser session.

Structured-data adapters for C-CDA and takeout exports are planned for v1.1. For now, put any PDFs from these routes in `Other Records/`.

## First run

1. Open Claude Code or Cowork in an empty folder where the case will live. Use one folder per patient. Keep it out of shared drives and out of git repositories.
2. Say **"Set up a case."** `case-setup` asks a few questions, all optional except how to refer to the patient. It also asks for names and numbers that must never go into a web search, and creates the folder.
3. Say **"Start the patient history."** `patient-intake` interviews you, one topic at a time. Skip anything, and stop and resume whenever you like.
4. Download records into the folders as described above.
5. Say **"Ingest the new results."** `ingest-results` asks whether you've noticed anything new, then reads every file. It builds the indexes, summaries, and lab tables, and writes a change note.

Open `START-HERE.md` in the case folder any time for a reminder of what to say.

## Ongoing use

| When | Say | What happens |
|---|---|---|
| Any question about the case | "What does the CT mean?" "Is his kidney function getting worse?" | `ask-the-records` answers from the chart with sources. |
| New files downloaded | "Ingest the new results." | Observations first, then extraction, updates, cross-checks, and a change note in `analysis/changes/`. It tells you when a conference is worth running. |
| You noticed something, or a doctor told you something | "Record an observation." | A dated entry in `notes/bedside-status.md`, checked against the chart. |
| You remembered more history | "Add to the patient history." | A dated amendment in `notes/patient-history.md`. |
| A conversation with the team is coming up | "Prep questions for rounds tomorrow with the cardiology team, about ten minutes." | A card and a detail sheet in `analysis/questions/`. |
| After the conversation | "Record what the doctor said." | Logged, so the next analysis starts from it. |

Everything lives in the case folder:

```
<case>/
  AGENTS.md          the case instructions every skill reads, and where the case stands
  START-HERE.md      what to say, where files go
  Test Results/  Care Team Notes/  Other Records/      your downloads
  notes/             patient history and bedside observations, family report
  panel/             the case conference panel
  analysis/          indexes, summaries, discrepancies, change notes, question sheets, conferences
    data/            extracted text, manifests, lab tables in CSV and markdown
  consult/           independent consult reports
```

## Case conferences and independent consults

**Case conference.** Say "Run a case conference." The first time, `design-panel` reads the case, asks you a few questions, and proposes specialist seats chosen for this patient. At least one seat is a specialty the team has not consulted yet. You approve the panel, then the seats review the chart in parallel. A contrarian investigator attacks the consensus, and a synthesizer writes a conference note. A second reader checks every claim against the records. Expect 10 to 20 minutes and a substantial number of tokens. Run one after a material change, not every day. Choose **fresh look** mode when you worry the analysis has anchored on one story.

**Independent consult.** Say "/mychart-advisor:independent-consult start." It is manual-only because it is expensive. It freezes a snapshot of the primary records with identifiers replaced by tokens. A blind team then works only from that snapshot. The team has not seen the treating team's conclusions summarized, nor your earlier analysis, nor the conference notes. It builds a fact base, generates hypotheses from several independent angles, investigates each family, and red-teams its conclusions. Only then does a reconciler compare its findings with the treating team's thinking and your prior analysis. Two verifiers check the report before you see it.

| Preset | Agents | Rough cost |
|---|---|---|
| standard | about 10 | Roughly a third of deep |
| deep | about 28 | Two to three hours at low concurrency, about 6 to 7 million tokens |
| max | 35 or more | Longer and more |

The skill states the estimate and asks before launching. Urgent findings, such as a safety issue or something that should change a planned procedure, reach you mid-run, marked preliminary. When new records arrive after a consult, `independent-consult addendum` appends a dated section and never rewrites the verified report.

## Privacy

- **Local files.** Records stay in the case folder on your computer. The skills never copy them to memory, other projects, or shared tools.
- **What your AI provider sees.** The model you use receives what it reads while it works, under your provider's terms. Health information you give a consumer AI tool is generally not covered by HIPAA. Decide what you are comfortable with before you start.
- **Web searches.** The skills search the web only for general medical literature. `.advisor/identifiers.txt` lists names and numbers that must never appear in a search. In Claude Code and Cowork, a hook blocks any web search or fetch that contains one. The independent consult also replaces identifiers in its snapshot and audits its own tool calls afterward.
- **Sharing.** Before you share any output, remember it contains health information. The consult report's HTML and PDF carry a confidentiality line and include the patient's name only if you ask.

## Other portals and other AI tools

**Other portals.** Text extraction works on any PDF. Lab-value parsing and note-name parsing are tuned to MyChart layouts. For other portals, the scripts fall back to a generic adapter, which extracts text, reads common collection-date labels, and leaves lab values for the agent to read. Adding a portal means adding one adapter module under `skills/ingest-results/scripts/portals/`.

**Other AI tools.** Skills written for parallel subagents run their units one at a time where the host has no subagents, and say so. The independent consult needs an agent type that starts without the case instructions. In Claude Code and Cowork, that is the plugin's `blind-reader` agent, and the skill verifies the blinding with a probe on every run. In other hosts, the skill builds the snapshot outside the case folder and asks you to open a new session there for the blind stage.

## Contributing

Read [AGENTS.md](AGENTS.md) first. The rule that outranks everything: **no real patient data, ever.** All fixtures are synthetic and all examples are fictional. A pre-commit guard enforces this.

```
python3 -m venv .venv && .venv/bin/pip install -r requirements-dev.txt
git config core.hooksPath .githooks
.venv/bin/python tests/fixtures/generate.py
.venv/bin/pytest
claude plugin eval . --threshold 0.8      # model-graded evals, costs tokens
```

## License

MIT. See [LICENSE](LICENSE) and [DISCLAIMER.md](DISCLAIMER.md).
