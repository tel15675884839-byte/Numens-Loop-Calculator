# Journal - Developer (Part 1)

> AI development session journal
> Started: 2026-04-30

---

## Session 1: Initialize AI Workflow Harness

**Date**: 2026-04-30
**Task**: AI workflow bootstrap
**Branch**: `codex/web-migration-phase1-original`

### Progress

- Verified the repository already has Trellis, Magic Context, OpenCode, and Oh-My-OpenCode-Slim bootstrap files.
- Strengthened `.contextignore` to exclude local OpenCode dependencies and Python virtual environments while documenting high-signal context files.
- Expanded `.opencode/context-priority.md` so backend specs, guides, Magic Context config, and command docs are loaded for AI sessions.
- Updated `opencode.jsonc` instructions to include backend spec and Magic Context configuration.
- Updated `/start-task` command workflow to explicitly load Magic Context and backend specs when relevant.
- Expanded Trellis task and journal templates with context-loaded, memory-link, status-update, and task-state fields.
- Updated `AI_WORKFLOW_GUIDE.md` with daily usage guidance and available workflow actions.

### Context Loaded

- Task PRD: direct user request in current session
- Specs: `AGENTS.md`, `.trellis/spec/loop-calculator/*.md`, `.trellis/spec/backend/index.md`, `.trellis/spec/guides/index.md`
- Prior journals or memories: `.trellis/workspace/Developer/journal-1.md`

### Files Touched

- `.contextignore`
- `.opencode/context-priority.md`
- `.opencode/commands/start-task.md`
- `.trellis/tasks/TEMPLATE.md`
- `.trellis/workspace/JOURNAL_TEMPLATE.md`
- `opencode.jsonc`
- `AI_WORKFLOW_GUIDE.md`
- `.trellis/workspace/Developer/journal-1.md`

### Decisions

- Kept existing Trellis and OpenCode files instead of recreating them.
- Treated `.trellis/spec/`, `.trellis/workspace/`, `.opencode/context-priority.md`, and `magic-context.jsonc` as the high-signal memory path.
- Left unrelated dirty frontend/backend worktree changes untouched.

### Pitfalls

- `git diff` does not show changes inside untracked directories, so `git status --short` is the useful check until workflow files are added to git.
- `.opencode/node_modules/` was present locally and must remain ignored by context indexing.

### Verification

- [x] Command: `python ./.trellis/scripts/get_context.py --mode packages`
      Result: succeeded; reported `backend` and `loop-calculator` spec layers.
- [x] Command: `git status --short`
      Result: confirmed workflow files are untracked or modified alongside unrelated existing app changes.

### Next Plan

- When the next feature task starts, create or select `.trellis/tasks/<task-slug>/prd.md` and run `/start-task <task-slug>`.
- Before pausing future work, run `/save-session <task-slug>` to append a focused journal entry and update PRD handoff notes.

### Memory Candidates

- Promote to spec: no new product engineering rule discovered.
- Keep as journal-only: workflow bootstrap file list and verification result.

### Task Status Update

- PRD updated: not needed
- Current task state: done

---

## Session 2: Isolate Desktop GUI Archive

**Date**: 2026-05-06
**Task**: Web-only active tree cleanup
**Branch**: `codex/web-migration-phase1-original`

### Summary

Moved the retired PySide6 desktop GUI out of the active project and preserved it as a restorable archive.

### Main Changes

- Created `archive/desktop_gui_2026-05-06/` and `archive/desktop_gui_2026-05-06.zip`.
- Moved desktop entrypoints, PySide6 UI modules, GUI tests, desktop-only assets, app settings, and the legacy standalone HTML UI into the archive.
- Kept active `loop_calculator/` limited to Qt-free calculation, product database helpers, and pure device state/model modules.
- Removed active tracked Python caches and `output.log` generated artifacts.
- Removed `PySide6` from active `requirements.txt`.
- Rewrote active `AGENTS.md`, `README.md`, and loop-calculator Trellis specs as Web-first guidance.
- Removed two desktop-window sync tests from active `tests/test_integration_flow.py`; the original full test file remains in the archive.

### Git Commits

| Hash | Message |
|------|---------|
| N/A | No commit created in this session |

### Testing

- [OK] `pytest tests/`: 25 passed.
- [OK] `pytest backend/tests/`: 5 passed.
- [OK] `cd frontend && npm test`: 16 files and 60 tests passed.
- [OK] `cd frontend && npm run build`: Vite production build succeeded.

### Status

[OK] **Completed**

### Next Steps

- Review the archive contents before committing, especially whether the binary zip should be versioned or kept as a local handoff artifact.
- Keep unrelated pre-existing backend/frontend dirty changes separate from this cleanup if creating a commit.

---

## Session 3: Remove 600 Detector Products and Rename Result Label

**Date**: 2026-05-08
**Task**: Web product-data and results UI adjustment
**Branch**: `codex/web-migration-phase1-original`

### Summary

Removed the retired Detector 600 series from active Web data sources and changed the right-side result card label from `Loop Addresses` to `Devices Qty`.

### Main Changes

- Deleted built-in Detector products `product-0013` through `product-0018` (`600-001` through `600-006`) from `products_db.json`.
- Deleted the same products from `products_db.defaults.json` so restore/default flows do not reintroduce them.
- Added backend initialization cleanup for those retired built-in product IDs so existing SQLite databases also stop showing them.
- Added a storage regression test that preserves custom 600-named products while removing only retired built-in IDs.
- Updated `frontend/src/components/workspace/CalculationInspector.vue` label to `Devices Qty` without renaming calculation/API fields.

### Verification

- [OK] Command: `pytest backend/tests/test_storage.py`
      Result: 1 passed after red/green regression cycle.
- [OK] Command: `pytest backend/tests/`
      Result: 9 passed.
- [OK] Command: `pytest tests/test_database.py`
      Result: 7 passed.
- [OK] Command: `cd frontend && npm test`
      Result: 16 files and 66 tests passed.
- [OK] Command: `cd frontend && npm run build`
      Result: Vite production build succeeded.
- [OK] Command: Python JSON parse with `utf-8-sig`
      Result: `products_db.json` and `products_db.defaults.json` parse successfully.
- [OK] Command: active product-data scan for factory/customer names starting with `600-`
      Result: none found in active product data.

### Pitfalls

- `products_db.defaults.json` currently includes a UTF-8 BOM, so `python -m json.tool` rejects it unless read with `utf-8-sig`.
- Archived desktop snapshots still contain the 600 series by design; active Web data sources do not.

### Next Plan

- If packaging uses `dist/data/loop_calculator.sqlite3`, refresh that generated SQLite artifact before release so packaged builds match the cleaned product catalog.

---

## Session 4: Offline Cache and Device Library Sync

**Date**: 2026-05-08
**Task**: Web offline use and online Library update behavior
**Branch**: `codex/web-migration-phase1-original`

### Summary

Added a lightweight Service Worker for offline static frontend access and changed backend initialization so built-in device Library records synchronize from `products_db.json` whenever the backend starts.

### Main Changes

- Added `docs/superpowers/plans/2026-05-08-offline-cache-library-sync.md` as the implementation plan.
- Added `frontend/public/sw.js` with versioned static caching, navigation fallback, same-origin static runtime caching, old-cache cleanup, and `/api/` exclusion.
- Added `frontend/src/pwa.ts` and registered it from `frontend/src/main.ts` in production secure contexts.
- Updated `backend/app/storage.py` so built-in products are synced from the seed JSON on initialization instead of only seeding empty databases.
- Preserved custom products by deleting/updating only rows marked `built_in = 1`.
- Updated storage tests to cover built-in sync, retired built-in removal, and custom product preservation.

### Verification

- [OK] Command: `pytest backend/tests/test_storage.py -v`
      Result: 2 passed after red/green test cycle.
- [OK] Command: `pytest backend/tests/`
      Result: 10 passed.
- [OK] Command: `pytest tests/test_database.py`
      Result: 7 passed.
- [OK] Command: `cd frontend && npm test`
      Result: 16 files and 66 tests passed.
- [OK] Command: `cd frontend && npm run build`
      Result: Vite production build succeeded.
- [OK] Check: `frontend/dist/sw.js`
      Result: generated by Vite from `frontend/public/sw.js`.

### Pitfalls

- Service workers only work on HTTPS or localhost, so offline caching requires secure deployment.
- The service worker intentionally does not cache `/api/`; products/projects keep using existing frontend localStorage fallbacks when offline.
- Users may need one successful online visit after deployment before offline use is available.

### Next Plan

- If desired, add a small UI indicator later for “offline cache active” or “new version available”.

