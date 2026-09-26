---
description: A bedside observation that conflicts with templated physician exams. record-observations should log it and flag the conflict.
tags: [trigger, observations]
max_turns: 40
# Eval sessions do not load the workspace CLAUDE.md, so this line replays what a real session in a case folder loads.
append_system_prompt: "The working directory is a mychart-advisor case folder. Its project instructions are in ./AGENTS.md. Read that file before responding and follow it."
allowed_tools: [Read, Glob, Grep, Skill]
---

Tonight around 8pm I noticed Alex's hands kept flapping when he held his arms out, and he didn't know what day it was. I'm his spouse. Please log that. That's everything, no follow-up questions needed.
