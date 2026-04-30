# OpenCode Context Priority

Load this file at the start of AI-assisted development sessions.

## Highest Priority

1. `AGENTS.md`
2. `.trellis/spec/loop-calculator/index.md`
3. `.trellis/spec/loop-calculator/*.md`
4. `.trellis/spec/backend/index.md`
5. `.trellis/spec/backend/*.md`
6. `.trellis/spec/guides/index.md`
7. `.trellis/tasks/*/prd.md`
8. `.trellis/workspace/index.md`
9. `.trellis/workspace/*/index.md`
10. Latest `.trellis/workspace/*/journal-*.md`
11. `magic-context.jsonc`
12. `.opencode/commands/*.md`

## Normal Priority

- Source files directly related to the active task.
- Tests covering the changed behavior.
- `opencode.jsonc` and `.opencode/oh-my-opencode-slim.jsonc` when changing agent orchestration.
- Existing docs under `docs/` only when the task references them.

## Excluded or Low Priority

Follow `.contextignore` for generated folders, build output, logs, spreadsheet binaries, caches, and Trellis runtime internals.

## Session Rule

When a task starts, first load the active task PRD, the relevant Trellis specs, and the latest workspace journal. When a task ends, write a journal entry that captures progress, pitfalls, verification, and next plan.
