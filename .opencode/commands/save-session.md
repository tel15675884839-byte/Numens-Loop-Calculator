---
description: Save Trellis workspace memory and update task handoff notes
agent: orchestrator
---

Save the current Loop Calculator AI development session for task `$ARGUMENTS`.

Follow this workflow:

1. Inspect `git status --short` and identify only files touched in this session.
2. Summarize progress, decisions, pitfalls, verification commands, and next steps.
3. Update the active task notes under `.trellis/tasks/` if the task status, acceptance criteria, or handoff changed.
4. Write a workspace journal entry under `.trellis/workspace/<developer>/journal-N.md` using `.trellis/workspace/JOURNAL_TEMPLATE.md`.
5. If a reusable rule was discovered, propose the exact `.trellis/spec/loop-calculator/` update before editing the spec.
6. If the session made source changes, run or report the smallest meaningful verification command from `AGENTS.md`.

Keep the journal concise and operational. Do not include large command output unless it is needed to diagnose a blocker.
