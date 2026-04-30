# Loop Calculator Project Print Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a project-wide A4 Portrait print preview workflow that replaces the disabled `Preferences` navigation entry with `Print`.

**Architecture:** Add a project-owned `print_profile` contract that round-trips through the backend and the frontend project model. Add a dedicated frontend print route with a local draft store, print profile panel, and A4 report renderer that uses the active in-memory project.

**Tech Stack:** FastAPI, Pydantic, SQLite, Vue 3, TypeScript, Pinia, Vue Router, Tailwind CSS, Vitest, pytest.

---

## File Map

- Modify `backend/app/schemas.py`: add `ProjectPrintProfile` and include `print_profile` on project schemas.
- Modify `backend/app/storage.py`: create `project_print_profiles`, persist/load one profile per project.
- Modify `backend/tests/test_api.py`: assert project print profile save/reload round-trip.
- Modify `frontend/src/types/project.ts`: add `ProjectPrintProfile` and `print_profile`.
- Create `frontend/src/types/print.ts`: print preview type helpers.
- Modify `frontend/src/stores/workspaceStore.ts`: normalize projects with `print_profile`, include it in dirty signatures, and add `savePrintProfile`.
- Create `frontend/src/stores/printStore.ts`: manage preview draft profile, reset/save/print readiness.
- Modify `frontend/src/router/index.ts`: add `/print`.
- Modify `frontend/src/components/layout/LeftNav.vue`: replace disabled `Preferences` with `Print`.
- Modify `frontend/src/components/layout/TopBar.vue`: add print context action labels.
- Create `frontend/src/views/PrintPreviewView.vue`: preview page.
- Create `frontend/src/components/print/PrintProfilePanel.vue`: editable project report metadata.
- Create `frontend/src/components/print/PrintPageStack.vue`: A4 page stack.
- Create `frontend/src/components/print/ProjectSummaryPage.vue`: first report page.
- Create `frontend/src/components/print/LoopReportPage.vue`: loop report pages.
- Create `frontend/src/components/print/DeviceScheduleTable.vue`: print-friendly device schedule.
- Modify `frontend/src/styles.css`: add print page and `@page` styles.
- Add frontend tests under `frontend/src/stores/__tests__`, `frontend/src/router/__tests__`, and component tests where needed.

## Tasks

### Task 1: Backend Project Print Profile Contract

**Files:**
- Modify: `backend/tests/test_api.py`
- Modify: `backend/app/schemas.py`
- Modify: `backend/app/storage.py`

- [ ] **Step 1: Write the failing API round-trip test**

Add a test that posts a project with `print_profile`, reloads it, updates the profile, and confirms the saved profile is returned.

- [ ] **Step 2: Run the backend test and confirm RED**

Run: `pytest backend/tests/test_api.py::test_project_print_profile_round_trip -q`

Expected: fail because `print_profile` is not returned.

- [ ] **Step 3: Add backend schema and storage support**

Add a Pydantic model named `ProjectPrintProfile`, include it on project schemas, create the `project_print_profiles` table, and load/replace the profile in project persistence.

- [ ] **Step 4: Run the backend test and confirm GREEN**

Run: `pytest backend/tests/test_api.py::test_project_print_profile_round_trip -q`

Expected: pass.

### Task 2: Frontend Project Types and Workspace Save Support

**Files:**
- Modify: `frontend/src/types/project.ts`
- Modify: `frontend/src/stores/__tests__/workspaceStore.test.ts`
- Modify: `frontend/src/stores/workspaceStore.ts`

- [ ] **Step 1: Write the failing workspace store test**

Add a test proving `savePrintProfile` updates `activeProject.print_profile`, marks the project dirty, and saves through the existing project persistence path.

- [ ] **Step 2: Run the frontend test and confirm RED**

Run: `cd frontend && npm test -- src/stores/__tests__/workspaceStore.test.ts`

Expected: fail because `savePrintProfile` does not exist.

- [ ] **Step 3: Implement project print profile typing and workspace support**

Add `ProjectPrintProfile`, normalize missing values to `null`, include `print_profile` in the project change signature, and implement `savePrintProfile(profile)`.

- [ ] **Step 4: Run the frontend store test and confirm GREEN**

Run: `cd frontend && npm test -- src/stores/__tests__/workspaceStore.test.ts`

Expected: pass.

### Task 3: Print Store Draft Workflow

**Files:**
- Create: `frontend/src/types/print.ts`
- Create: `frontend/src/stores/printStore.ts`
- Create: `frontend/src/stores/__tests__/printStore.test.ts`

- [ ] **Step 1: Write failing print store tests**

Cover draft initialization from saved profile, current-date default for new projects, temporary edits, reset, required fields, and saving defaults through `workspaceStore.savePrintProfile`.

- [ ] **Step 2: Run print store tests and confirm RED**

Run: `cd frontend && npm test -- src/stores/__tests__/printStore.test.ts`

Expected: fail because the store does not exist.

- [ ] **Step 3: Implement print store**

Implement draft state, `initializeFromProject`, `updateDraft`, `resetDraft`, `saveDefaults`, `canPrint`, and `printNow`.

- [ ] **Step 4: Run print store tests and confirm GREEN**

Run: `cd frontend && npm test -- src/stores/__tests__/printStore.test.ts`

Expected: pass.

### Task 4: Route and Navigation

**Files:**
- Modify: `frontend/src/router/__tests__/index.test.ts`
- Modify: `frontend/src/router/index.ts`
- Modify: `frontend/src/components/layout/LeftNav.vue`
- Modify: `frontend/src/components/layout/TopBar.vue`
- Create: `frontend/src/views/PrintPreviewView.vue`

- [ ] **Step 1: Write failing route/nav tests**

Assert that `/print` resolves to route name `print` and that leaving the workspace for print follows the same unsaved-project guard.

- [ ] **Step 2: Run router tests and confirm RED**

Run: `cd frontend && npm test -- src/router/__tests__/index.test.ts`

Expected: fail because route `print` does not exist.

- [ ] **Step 3: Implement route and navigation**

Add `PrintPreviewView`, route `/print`, replace `Preferences` with a real `Print` router link, and show print context labels in the top bar.

- [ ] **Step 4: Run router tests and confirm GREEN**

Run: `cd frontend && npm test -- src/router/__tests__/index.test.ts`

Expected: pass.

### Task 5: Print Preview Components and A4 Report

**Files:**
- Create: `frontend/src/components/print/PrintProfilePanel.vue`
- Create: `frontend/src/components/print/PrintPageStack.vue`
- Create: `frontend/src/components/print/ProjectSummaryPage.vue`
- Create: `frontend/src/components/print/LoopReportPage.vue`
- Create: `frontend/src/components/print/DeviceScheduleTable.vue`
- Modify: `frontend/src/views/PrintPreviewView.vue`
- Modify: `frontend/src/styles.css`

- [ ] **Step 1: Write failing component tests**

Assert that the preview renders profile fields, project summary, loop pages, diagnostics, and device schedule columns.

- [ ] **Step 2: Run component tests and confirm RED**

Run: `cd frontend && npm test -- src/components/print`

Expected: fail because components do not exist.

- [ ] **Step 3: Implement preview components**

Render the metadata panel, page stack, project summary, loop pages, and schedule table using the active project and print draft profile.

- [ ] **Step 4: Add A4 print CSS**

Add `@page { size: A4 portrait; }`, screen preview dimensions, page breaks, table header repeat rules, and print-only cleanup.

- [ ] **Step 5: Run component tests and confirm GREEN**

Run: `cd frontend && npm test -- src/components/print`

Expected: pass.

### Task 6: Full Verification

**Files:**
- All touched files.

- [ ] **Step 1: Run backend verification**

Run: `pytest backend/tests/`

Expected: pass.

- [ ] **Step 2: Run frontend tests**

Run: `cd frontend && npm test`

Expected: pass.

- [ ] **Step 3: Run frontend build**

Run: `cd frontend && npm run build`

Expected: pass.

- [ ] **Step 4: Inspect git status**

Run: `git status --short`

Expected: only intentional implementation files are modified.
