---
description: Start a study session — sync progress, show the dashboard, plan the session
argument-hint: "[minutes available]"
---
Start a study session following the "Session protocol" in CLAUDE.md:

1. If `study status` says the student is not set up yet, run `/setup` instead (tell them why in one line).
2. Sync progress with a pull from GitHub (git-guard `git` tool if available, else Bash; skip if there is no remote).
3. `study session start --minutes <minutes>`; if focus mode is enabled on this machine, `study focus start --minutes
   <minutes + 10>` (one line on what it blocks). Then `study status`.
4. Time available: $ARGUMENTS (if empty, ask once, briefly — and meanwhile assume 60 minutes).
5. Short briefing: time left until the exam, readiness %, weakest 2–3 topics, due reviews, open weak spots, mocks taken,
   and a concrete plan following the CLAUDE.md study plan for today's date — e.g. "15 min learn quadratic probing → 4
   hash traces → 1 design question → 3 due reviews". Follow the learner profile.
6. Begin the first activity immediately.
