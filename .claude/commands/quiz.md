---
description: Practice questions chosen by spaced repetition and weakest topics
argument-hint: "[topic] [type: coding|trace|analysis|knowledge|proof] [n]"
---
Run a quiz. Arguments: $ARGUMENTS (any of: a topic id, a question type, a number of questions; default 5 mixed).

1. `study next` with matching `--topic/--type/--n` flags.
2. For each question, one at a time: `study show ID`, paste the full prompt, state type/points/time budget; for coding,
   design/analysis or long answers run `study answer ID` in the background (Bash `run_in_background: true`) — it opens the
   exam editor and returns their answer when they click Submit. Grade with `study show ID --answer` (re-run the engine
   for traces), give feedback, and `study record` it immediately (rules in CLAUDE.md).
3. After the set: a 3-line summary (score, what's solid, what to fix) and suggest the next activity.
