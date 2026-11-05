---
description: First-time setup — asks your name, imports the course files + textbook, installs the study browser, focus mode, your own progress repo
argument-hint: "[your name]"
---
Set this study system up for a new student, end to end. Be friendly and quick; do every step yourself and only ask
what you can't find out. Run commands from the repo root (`python` on Windows, `python3` on Linux/macOS — check once).

1. **Check the machine:** `study setup check`. Fix what you can as you go (below). If Python < 3.8, stop and say so.
2. **Ask about them** (one AskUserQuestion round, or plain questions if that tool isn't available). Name: $ARGUMENTS
   (if given, don't ask again). Ask:
   - their **name** (what to call them),
   - **hours per day** they can study until Nov 19,
   - **how Exam 1 went / what they find hardest** (hashing, heaps, sorting traces, complexity analysis, coding),
   - **how they learn best** (examples first, pictures, analogies, short chunks, lots of practice questions...),
   - whether they want **focus mode** (closes browsers/chat/social/games/streaming during sessions) — and which
     categories, and any app they need to keep open (e.g. a browser for another class).
   Then: `study setup name "<name>" --hours <h>`, and record each learning preference as a learner note
   (`study style add "..." --kind works|avoid|pace|pref`) and each self-reported weakness as a weak spot
   (`study weak add "..." --topic <topic>`). Focus: `study focus config on|off`, `study focus config categories a,b,...`,
   `study focus config allow "<App.exe>"` / `add "<App.exe>"` as they asked (`study focus config show` to confirm).
3. **Course files:** ask where their Brightspace downloads are (the Exam 2 materials zip, the slides zip, the homework
   zip, the solutions zip — any or all; also look in this repo folder for `*.zip`). Run
   `study setup material <zip> [<zip> ...]` — it keeps ONLY the Exam 2 files and converts them to text. Never search
   the whole disk; if they don't know, ask them to drop the zips into this folder.
4. **Textbook (optional but best):** ask for the path to the Weiss *Data Structures and Algorithm Analysis in C++*
   (4th ed.) PDF. `study setup textbook "<path>"` copies it to `material/textbook/` (git-ignored) and extracts Ch 5–7.
   Without it, teaching uses the notes + slides (fine, slightly less exact quoting).
5. **Study browser:** `study setup browser` (creates `.venv` and installs it; may take a few minutes — run with a
   long timeout). Linux may need `sudo apt install python3-venv python3-tk` first (ask them to run it with `! ...`).
   Then `study setup allowlist` (generates the browser's allow list from the notes/material links).
6. **Their own progress repo** (so progress syncs between computers): `study setup repo-info` explains it. If `gh` is
   installed and logged in, offer to create a **private** repo for them. If the current `origin` remote is the shared
   template, rename it to `upstream` first (so they can pull new questions later), then create their repo with
   `gh repo create <their-user>/csci335-exam2-study --private --source . --remote origin --push`.
   Use the git-guard `git` tool if available; every mutating git command needs their OK, and if one is denied, stop
   and ask. If they decline or have no gh, skip — progress still saves locally.
7. Finish: `study setup check` and `study status`, then a 5-line summary: what's set up, what's missing (and whether it
   matters), and how to use it — `/start [minutes]` to begin a session, `/save` to end one, `/learn hashing` is a good
   first lesson. Offer to start the first session now.
