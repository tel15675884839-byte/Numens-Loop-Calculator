# First-Use Guided Tour Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a first-use guided spotlight tutorial that helps new users understand the Loop Calculator workspace.

**Architecture:** The feature is frontend-only. A Pinia onboarding store owns tutorial state and localStorage persistence, while a global Vue component renders the overlay and reads `data-tour` markers from existing layout/workspace components.

**Tech Stack:** Vue 3, Pinia, TypeScript, Tailwind CSS, Vitest.

---

## File Structure

- Create: `frontend/src/stores/onboardingStore.ts` for steps, current index, first-run initialization, completion, skip, and replay.
- Create: `frontend/src/stores/__tests__/onboardingStore.test.ts` for localStorage and state transitions.
- Create: `frontend/src/components/layout/OnboardingTour.vue` for the overlay, highlight, tooltip, and keyboard/accessibility labels.
- Create: `frontend/src/components/layout/__tests__/OnboardingTour.test.ts` for source-level coverage of important behavior and selectors.
- Modify: `frontend/src/components/layout/AppShell.vue` to initialize and render the tour globally.
- Modify: `frontend/src/components/layout/TopBar.vue` to add a replay button and tour marker for project actions.
- Modify: `frontend/src/components/layout/LeftNav.vue` to mark the project list.
- Modify: `frontend/src/views/WorkspaceView.vue` to mark loop tabs, system parameters, device table, and result panel.
- Modify: workspace child components only if wrappers in `WorkspaceView.vue` are not enough for stable highlighting.

## Tasks

### Task 1: Onboarding Store

- [ ] Write failing tests in `frontend/src/stores/__tests__/onboardingStore.test.ts` for first-run auto-open, complete persistence, skip persistence, and replay.
- [ ] Run `cd frontend && npm test -- onboardingStore.test.ts` and verify the test fails because the store does not exist.
- [ ] Implement `frontend/src/stores/onboardingStore.ts` with a `loop-calculator.onboarding.v1` storage key and 6 fixed steps.
- [ ] Run `cd frontend && npm test -- onboardingStore.test.ts` and verify the test passes.

### Task 2: Global Tour UI

- [ ] Write failing source-level tests in `frontend/src/components/layout/__tests__/OnboardingTour.test.ts` covering use of `data-tour`, overlay controls, and focus/resize positioning hooks.
- [ ] Run `cd frontend && npm test -- OnboardingTour.test.ts` and verify the test fails because the component does not exist.
- [ ] Implement `frontend/src/components/layout/OnboardingTour.vue` with Teleport, overlay, highlighted rectangle, tooltip, Back/Next/Skip/Done controls, and scroll-to-step positioning.
- [ ] Run `cd frontend && npm test -- OnboardingTour.test.ts` and verify the test passes.

### Task 3: Wire Into Existing UI

- [ ] Add `OnboardingTour` to `AppShell.vue` and call `onboarding.initialize()` on mount.
- [ ] Add a `Help` button to `TopBar.vue` that calls `onboarding.startReplay()`.
- [ ] Add stable `data-tour` markers to `TopBar.vue`, `LeftNav.vue`, and `WorkspaceView.vue`.
- [ ] Update layout/source tests to assert the markers and replay button exist.
- [ ] Run `cd frontend && npm test` and verify all frontend tests pass.

### Task 4: Build Verification

- [ ] Run `cd frontend && npm run build`.
- [ ] Manually inspect the generated UI if needed by running `cd frontend && npm run dev` and opening the app.
