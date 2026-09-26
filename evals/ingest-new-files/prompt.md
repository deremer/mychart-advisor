---
description: New PDFs are in the folders. ingest-results should extract, update the analysis, and write a cited, phone-length change note.
tags: [trigger, ingest]
max_turns: 120
timeout_seconds: 1800
# Eval sessions do not load the workspace CLAUDE.md, so this line replays what a real session in a case folder loads.
append_system_prompt: "The working directory is a mychart-advisor case folder. Its project instructions are in ./AGENTS.md. Read that file before responding and follow it."
allowed_tools: [Read, Glob, Grep, Skill]
---

I just downloaded a bunch of new results and notes from MyChart into the folders. Can you go through them and update everything? Nothing new to report from the bedside.
