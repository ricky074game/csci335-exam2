---
description: Learn a topic interactively from its study guide, with check questions
argument-hint: "<topic: hashing|coding|heaps|heapsort|sortbasics|quicksort|analysis> [subtopic]"
---
Teach topic: $ARGUMENTS (if empty, pick the weakest unstudied topic from `study status`).

- Open the topic's notes file (see `study topics`) and the related official material in `material/text/` and the
  textbook chapter in `material/textbook/` (if present). Follow the learner profile.
- Teach in small chunks (one concept at a time, ≤ ~25 lines, starting from a concrete example). For anything that is a
  trace (hash table, heap, partition, heapsort), run the engine with `--show` so they see it step by step in the study
  browser. After each chunk ask 1–2 quick check questions and wait for the answer. Correct misconceptions immediately
  and log real ones with `study weak add`.
- Emphasise what the exam asks: the exact textbook algorithm (the professor marks other variants wrong), the trace
  format, complexities of each operation with the reason, and the traps listed in the notes. Let the student skip what
  they already know if they prove it with a correct answer.
- Finish with 2–3 bank questions (`study next --topic <topic> --n 3 --mode new`), graded and recorded per CLAUDE.md, then
  `study studied <topic>`.
