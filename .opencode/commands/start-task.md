---
description: Load a Trellis task and prepare Loop Calculator development context
agent: orchestrator
---

Start the Loop Calculator task identified by `$ARGUMENTS`.

Follow this workflow:

1. Read `AGENTS.md`.
2. Read `.opencode/context-priority.md`.
3. Read `magic-context.jsonc` so memory and high-signal context behavior is explicit.
4. Run `python .trellis/scripts/get_context.py --mode packages` to inspect available Trellis packages/spec layers.
5. If `$ARGUMENTS` is present, find the matching directory under `.trellis/tasks/`. If it is omitted, list `.trellis/tasks/` and ask for the task slug only if there is no clear active task.
6. Read the task `prd.md`, `task.json`, `implement.jsonl`, and `check.jsonl` when they exist.
7. Read `.trellis/spec/loop-calculator/index.md`, `.trellis/spec/backend/index.md`, and the specific spec files relevant to the task scope.
8. Use Magic Context search or memory tools for prior related sessions, prioritizing `.trellis/workspace/`.
9. Restate the task scope, affected modules, verification plan, and any missing requirement before editing.

Do not change unrelated dirty worktree files.
