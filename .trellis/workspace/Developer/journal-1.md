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

---

## Session 5: First-Use Guided Tour

**Date**: 2026-05-08
**Task**: Web first-use onboarding tutorial
**Branch**: `codex/web-migration-phase1-original`

### Summary

Added a frontend-only guided spotlight tour that auto-opens for first-time users and can be replayed from the top toolbar.

### Main Changes

- Added `docs/superpowers/plans/2026-05-08-first-use-guided-tour.md` to capture the implementation plan.
- Added `frontend/src/stores/onboardingStore.ts` with six fixed tutorial steps and localStorage completion persistence.
- Added `frontend/src/components/layout/OnboardingTour.vue` for the global overlay, highlighted target area, tooltip, and navigation controls.
- Added a `Help` button in `TopBar.vue` to replay the tutorial.
- Added stable `data-tour` markers to project actions, project list, loop tabs, system parameters, device table, and calculation results.
- Added focused Vitest coverage for store behavior, tour component structure, and layout wiring.

### Verification

- [OK] Command: `cd frontend && npm test -- onboardingStore.test.ts`
      Result: red/green cycle completed; 5 tests passed.
- [OK] Command: `cd frontend && npm test -- OnboardingTour.test.ts`
      Result: red/green cycle completed; 3 tests passed.
- [OK] Command: `cd frontend && npm test -- ResponsiveLayout.test.ts`
      Result: red/green cycle completed; 3 tests passed.
- [OK] Command: `cd frontend && npm test`
      Result: 19 files and 79 tests passed.
- [OK] Command: `cd frontend && npm run build`
      Result: Vite production build succeeded.

### Pitfalls

- The brainstorming visual companion server stopped because it treated the temporary PowerShell process as the owner process; static HTML preview was used instead.
- `.superpowers/` contains local brainstorming artifacts and should remain uncommitted unless explicitly requested.

### Next Plan

- If desired, run a browser QA pass against the live dev server to tune exact spotlight placement on desktop and mobile.

---

## Session 6: Guided Tour Positioning Fixes

**Date**: 2026-05-08
**Task**: Fix guided tour resize/positioning and add print guidance
**Branch**: `codex/web-migration-phase1-original`

### Summary

Fixed guided tour geometry so it updates on resize and scroll, stopped the overlay from blocking page scroll interactions, and added print preview guidance steps.

### Main Changes

- Changed `OnboardingTour.vue` from computed DOM measurement to a reactive measured rect updated via `requestAnimationFrame`.
- Added resize plus window/document scroll listeners so the blue spotlight and tooltip follow layout and scroll changes.
- Made the full-screen tour layer pointer-transparent while keeping the tooltip controls clickable, so scrollbars and resizing are not blocked during guidance.
- Added `print-settings` and `print-preview` onboarding steps.
- Added print page `data-tour` markers in `PrintPreviewView.vue`.
- Added regression tests for reactive geometry updates, non-blocking overlay behavior, and print tour targets.

### Verification

- [OK] Command: `cd frontend && npm test -- OnboardingTour.test.ts`
      Result: 5 tests passed after red/green regression cycle.
- [OK] Command: `cd frontend && npm test -- onboardingStore.test.ts`
      Result: 6 tests passed after red/green regression cycle.
- [OK] Command: `cd frontend && npm test -- ResponsiveLayout.test.ts`
      Result: 3 tests passed after red/green regression cycle.
- [OK] Command: `cd frontend && npm test`
      Result: 19 files and 82 tests passed.
- [OK] Command: `cd frontend && npm run build`
      Result: Vite production build succeeded.

### Pitfalls

- Vue computed properties do not re-run just because `getBoundingClientRect()` would now return different values; resize/scroll must update reactive state explicitly.
- A full-screen onboarding overlay should not own pointer events unless it intentionally blocks the underlying UI.

### Next Plan

- Browser-test the tour on narrow/mobile widths to validate tooltip placement around left/right edges.

---

## Session 7: Scoped Workspace and Print Tours

**Date**: 2026-05-08
**Task**: Split guided onboarding by Workspace and Print pages
**Branch**: `codex/web-migration-phase1-original`

### Summary

Split onboarding into separate Workspace and Print tours so first entering Print shows print-specific guidance and the Help button replays the current page's tour.

### Main Changes

- Added scoped onboarding state in `onboardingStore.ts` with separate `workspace` and `print` step sets.
- Changed persistence keys to keep Workspace and Print first-run completion independent.
- Updated `AppShell.vue` to initialize onboarding based on the current route and reinitialize when navigating between Workspace and Print.
- Updated `TopBar.vue` so Help calls `startReplay(currentTourScope)` and targets `project-actions` or `print-actions` depending on the current page.
- Replaced the old mixed Print steps with a dedicated 5-step Print tour covering print actions, saved templates, template fields, template actions, and print preview.
- Added `data-tour` markers in `PrintProfilePanel.vue` and kept `print-preview` in `PrintPreviewView.vue`.

### Verification

- [OK] Command: `cd frontend && npm test -- onboardingStore.test.ts`
      Result: 9 tests passed after red/green scope split.
- [OK] Command: `cd frontend && npm test -- ResponsiveLayout.test.ts`
      Result: 3 tests passed after updating route wiring assertions.
- [OK] Command: `cd frontend && npm test`
      Result: 19 files and 85 tests passed.
- [OK] Command: `cd frontend && npm run build`
      Result: Vite production build succeeded.

### Pitfalls

- A single global tour made Print Help replay Workspace guidance; tour scope needs to follow the current route.
- Print template markers belong inside `PrintProfilePanel.vue`, not `PrintPreviewView.vue`, because the template UI is encapsulated in that component.

### Next Plan

- Browser-test first-run behavior by clearing `loop-calculator.onboarding.workspace.v1` and `loop-calculator.onboarding.print.v1` in localStorage.

---

## Session 8: Workspace Tour Target Precision

**Date**: 2026-05-08
**Task**: Fix Workspace tour step 1 and step 2 highlight offsets
**Branch**: `codex/web-migration-phase1-original`

### Summary

Made the first Workspace tour targets more precise by moving `data-tour` markers from broad layout containers onto the specific UI regions users see.

### Main Changes

- Changed Workspace step 1 from the broad toolbar action group to `project-settings`, targeting the project title/name area.
- Added a separate `project-actions` step for New/Save/Export/Import controls.
- Moved the project list marker in `LeftNav.vue` from the whole scrollable sidebar area to a tighter wrapper around the Projects title and project rows.
- Updated focused tests to prevent future regressions where tour markers are attached to oversized containers.

### Verification

- [OK] Command: `cd frontend && npm test -- ResponsiveLayout.test.ts onboardingStore.test.ts`
      Result: 2 files and 13 tests passed after red/green cycle.
- [OK] Command: `cd frontend && npm test`
      Result: 19 files and 86 tests passed.
- [OK] Command: `cd frontend && npm run build`
      Result: Vite production build succeeded.

### Pitfalls

- The overlay measurement was working, but the target elements were too broad. Fixing geometry alone cannot make an oversized marker look precise.
- Dynamic `:data-tour` bindings are useful for route-scoped Help, but precise tour steps should prefer static markers on exact visible regions.

### Next Plan

- If more offset issues appear, inspect the target element size first before changing overlay math.

---

## Session 9: Empty Default Workspace and Git Ignore Cleanup

**Date**: 2026-05-08
**Task**: Prevent local artifacts from upload and remove default sample devices
**Branch**: `codex/web-migration-phase1-original`

### Summary

Changed fresh Web deployments to start with an empty loop instead of two sample devices and added local-only artifacts to `.gitignore`.

### Main Changes

- Updated `workspaceStore.ts` so `getLocalProjects()` returns an empty list when localStorage has no workspace cache, instead of falling back to `sampleWorkspaceProjects`.
- Added a regression test that verifies a first-run workspace with no backend/local project has an empty `device_rows` list.
- Added `.superpowers/`, `build.bat`, `loop_calculator.spec`, `requirements-build.txt`, and `run_server.py` to `.gitignore`.
- Confirmed those local artifacts show as ignored in `git status --short --ignored`.

### Verification

- [OK] Command: `cd frontend && npm test -- workspaceStore.test.ts`
      Result: 16 tests passed after red/green fallback change.
- [OK] Command: `cd frontend && npm test`
      Result: 19 files and 87 tests passed.
- [OK] Command: `cd frontend && npm run build`
      Result: Vite production build succeeded.

### Pitfalls

- Vercel/fresh environments showed two default devices because frontend fallback data used `sampleWorkspaceProjects`, which builds a sample project from default products.
- `.superpowers/` is generated by visual brainstorming and should not be committed.

### Next Plan

- If `frontend/src/data/sampleWorkspace.ts` becomes unused everywhere after this change, consider removing it in a cleanup pass.

---

## Session 10: Remove Manual Row Option

**Date**: 2026-05-08
**Task**: Remove manual device row option and clarify Vercel catalog behavior
**Branch**: `codex/web-migration-phase1-original`

### Summary

Removed the `Manual row` option from the workspace device selector and verified frontend-only catalog behavior for Vercel deployments.

### Main Changes

- Removed the empty-value `Manual row` option from `DeviceTable.vue` device selectors.
- Changed print schedule fallback text from `Manual row` to `Unassigned device` for any legacy rows without product/display names.
- Added a DeviceTable regression assertion that `Manual row` is not rendered and no empty product option exists.

### Verification

- [OK] Command: `cd frontend && npm test -- DeviceTable.test.ts`
      Result: 2 tests passed after red/green removal.
- [OK] Command: frontend source grep for `Manual row`
      Result: only the negative regression test still references the string.
- [OK] Command: `cd frontend && npm test`
      Result: 19 files and 87 tests passed.
- [OK] Command: `cd frontend && npm run build`
      Result: Vite production build succeeded.

### Pitfalls

- In Vercel without a backend, Device Catalog changes are frontend bundle changes plus localStorage cache behavior; existing users may keep cached products until cache invalidation/merge logic updates them.

### Next Plan

- Consider adding frontend seed-version synchronization so product catalog changes deployed to Vercel update existing users without requiring manual localStorage clearing.

---

## Session 11: Static Catalog Cache Refresh

**Date**: 2026-05-08
**Task**: Make Vercel/static frontend Device Catalog updates reach existing offline users
**Branch**: `codex/web-migration-phase1-original`

### Summary

Added frontend product-cache metadata so static bundled catalog updates can refresh cached built-in products while preserving user-created custom products.

### Main Changes

- Added `loop-calculator.products.meta` cache metadata with source and bundled catalog signature.
- Offline bootstrap now refreshes cached seed/bundled products when the deployed `defaultProducts` signature changes.
- Custom `built_in: false` products are preserved during bundled catalog refresh.
- API-sourced product caches are not overwritten by bundled frontend data when the backend is temporarily offline.
- Added product-store regression tests for both static refresh and API-cache preservation.

### Verification

- [OK] Command: `cd frontend && npm test -- productStore.test.ts`
      Result: 9 product-store tests passed after red/green coverage.
- [OK] Command: `cd frontend && npm test`
      Result: 19 files and 89 tests passed.
- [OK] Command: `cd frontend && npm run build`
      Result: Vite production build succeeded.

### Pitfalls

- Previous offline logic could never distinguish bundled/static cache from API-sourced cache. Metadata is required so static Vercel deployments update existing users without corrupting backend-managed catalogs.

### Next Plan

- If backend product APIs later expose their own catalog version, keep that version separate from the frontend bundled signature.

