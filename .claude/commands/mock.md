---
description: Take a full timed mock exam (70 min, 100 pts) and get it graded
argument-hint: "[mock id, e.g. mock-1]"
---
Mock exam: $ARGUMENTS (default: the first mock from `study mock list` not yet taken).

1. `study sheet <id>` with Bash `run_in_background: true` — it opens the mock window (one question at a time, a box per
   part, 70-minute countdown). Tell the student: they have 70 minutes from now (state the clock time it ends), and click
   **Submit** when finished — you'll get their answers automatically. (Or: paper like the real exam, photos into
   `answers/`.) Closing the window pauses; `--resume` continues. Note the start time.
2. Do not help, hint or grade during the exam. If they ask, reply only "exam conditions". If they ask for time, compute it.
3. When they submit, take their answers from the finished command (or Read the sheet in `answers/`, plus any photos), run
   `study mock show <id> --answers` and grade every question strictly against its rubric with partial credit in exam
   points; re-run the engines for every trace. Present a table: question · points earned/possible · what lost points.
   Then the total, a predicted grade, and the 3 highest-value fixes.
4. `study mock record <id> --scores <qid>=<pts>,... --minutes <used>`. Log real misconceptions with `study weak add`.
5. Offer to go over the lost points one by one.
