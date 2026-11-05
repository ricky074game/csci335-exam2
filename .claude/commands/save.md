---
description: End the session — log a summary and push progress to GitHub
---
1. Update the learner profile from this session (CLAUDE.md "Adapt to how they learn"): add any pattern you noticed about
   how the student learns best, retire notes that no longer hold.
2. `study focus end` (if it was on; mention anything it had to close), then `study session end --summary "<topics
   covered, questions done + average score, mocks, what to do next>"`.
3. `study validate` if any bank file was edited.
4. Stage `progress bank mocks notes answers`, commit with the message `progress: <YYYY-MM-DD> <short summary>`, and push
   (git-guard `git` tool if available; if a command is denied, stop and ask; if there is no remote, commit only and say so).
5. Confirm it was saved/pushed, and tell the student what the next session should start with.
