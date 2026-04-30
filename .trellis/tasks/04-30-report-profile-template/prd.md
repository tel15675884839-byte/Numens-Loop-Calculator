# PRD: Report Profile Template Gallery (Refined v7 - Print Fidelity)

## Overview
Fix the browser print preview to ensure that footers (Loop Name + Page X of Y) appear on every single physical page, even when content overflows.

## Goals
1. Ensure footers are visible on every page in browser print preview.
2. Fix the "missing footer" on overflowing pages.
3. Adjust row limits to prevent browser-side accidental breaks.

## Functional Requirements
- **Footer Persistence**: Footers must be anchored to the bottom of the physical page.
- **Row Limit Calibration**:
    - Page 1 (with metrics/params): 12 rows max.
    - Subsequent pages: 28 rows max.
- **Strict Sizing**: Use fixed heights during print to force the browser to respect our virtual page boundaries.

## UI Design
- **Footer**: Position absolutely at the bottom of the `.print-page` container.
- **Page Container**: Fixed `297mm` height in print mode.

## Technical Notes
- Update `LoopReportPage.vue` pagination constants.
- Modify `styles.css` `@media print` section.
