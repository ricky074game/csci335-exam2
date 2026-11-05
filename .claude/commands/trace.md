---
description: Trace drill — unlimited auto-graded hashing / heap / sorting trace problems
argument-hint: "[hash|heap|sort|mix] [n]"
---
Trace drill. Arguments: $ARGUMENTS (default: 5 problems, `mix` = rotate hash, heap, sort; bias toward the student's
weakest of these per `study status`).

For each problem:
1. Generate it: `study hash random --method any` · `study heap random --kind any` · `study sort random --kind any`.
   Paste the problem text exactly. State the expected format (HW5-style table after each insert; heap array after each
   step with index 0; partition array after the pivot move, each swap, and the end).
2. The student answers (short ones in chat; long ones on paper with a photo dropped into `answers/`, or typed in chat).
3. Grade with the engine: `study hash grade ID --table "..."`, `study heap grade ID --array "..."`,
   `study sort grade ID --array "..." [--steps "a;b;c"] [--answer K]`. Then `... solve ID --show` and walk through the
   exact step they missed (which probe / which child / where i and j stopped and why).
4. Score 0–4 (4 = every step right; final right but a wrong intermediate step = 3; method wrong = 1) and
   `study record <ID> <score> --note "..."` (the topic is inferred from the id).
End with the drill score and the most common mistake; log a weak spot if a mistake repeated.
