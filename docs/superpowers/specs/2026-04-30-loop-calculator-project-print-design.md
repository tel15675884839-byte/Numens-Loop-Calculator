# Loop Calculator Project Print Design

Date: 2026-04-30
Status: Approved for implementation planning

## Goal

Replace the disabled `Preferences` entry in the Web app with a real `Print` workflow that generates an engineering-style project report for the current project.

The report must:

- default to the current project, not the current loop
- support print preview and browser printing
- use `A4 Portrait`
- organize all loops into one formal report
- save project-specific print information after the first entry
- allow temporary edits in preview without silently changing saved project defaults

This is not a screenshot-print feature. It is a dedicated report-rendering feature.

## Approved Product Decisions

The user-approved decisions for this feature are:

- `Print` replaces the current disabled `Preferences` entry in the left navigation
- the default print scope is the entire active project
- the report is an engineering review document, not a temporary internal-only dump
- users fill report metadata once per project, then reuse it
- preview can temporarily override saved metadata
- only an explicit save action updates the project's saved print metadata

## Current Project Findings

The current Web application already has the right base pieces for a print module:

- `frontend/src/components/layout/LeftNav.vue` contains the disabled `Preferences` entry that can be replaced with `Print`
- `frontend/src/views/WorkspaceView.vue` provides the working project/loop editing context
- `frontend/src/stores/workspaceStore.ts` already holds the full active project in client state
- `frontend/src/types/project.ts` already models project, loop, row, and calculation snapshot data
- `frontend/src/components/workspace/CalculationInspector.vue` shows the important engineering result fields already available in the UI
- project persistence currently happens through full-project read/write calls in `frontend/src/api/projects.ts`
- backend project storage is structured and explicit, so print metadata should be designed intentionally rather than hidden in ad hoc frontend-only state

One important constraint is that the current project model does not include formal report metadata such as `Project No`, `Customer`, `Site`, `Panel`, `Revision`, or `Prepared By`. That metadata must be added as part of this feature.

## Approaches Considered

### 1. Print the existing workspace layout

Use browser print styles on the current workspace and try to hide controls.

Pros:

- smallest implementation

Cons:

- poor pagination control
- right-side inspector and editable table do not map cleanly to paper
- produces a UI printout, not an engineering report
- weak readability once a project contains multiple loops

Rejected because it does not meet the report-quality goal.

### 2. Dedicated project print preview with saved project print profile

Add a dedicated `Print Preview` view that renders a report from the active project using `A4 Portrait` pages and a project-level saved print profile.

Pros:

- correct document structure for engineers
- deterministic pagination
- supports first-time entry plus reuse
- clean separation between editing UI and print UI

Cons:

- requires new route/view/store logic
- requires explicit project metadata support

Selected because it satisfies the user-approved workflow with controlled scope.

### 3. Full document-template system

Create a broader reporting/template engine with signatures, approval history, branding packs, and export variants.

Pros:

- highest long-term flexibility

Cons:

- too large for this request
- shifts the feature from printing into document management

Rejected for now as over-scoped.

## Recommended Design

Implement a dedicated `Print Preview` route for the active project. The route renders a formal multi-page report using the current in-memory project state, not a screenshot of the workspace.

The preview uses a draft print profile:

- initial value comes from the project's saved print profile
- user edits in preview affect only the current preview session
- `Save as Project Defaults` persists the draft into the project
- `Reset` restores the last saved project print profile
- `Print` uses the current preview draft, even if the draft has not been saved

This feature should behave like a project-aware reporting tool, not like a global settings page.

## Scope

### In Scope

- replace the left-nav `Preferences` entry with `Print`
- add a dedicated print preview view/route
- render an `A4 Portrait` project report
- include all loops from the active project in one report
- add project-level print metadata storage
- allow temporary preview edits without immediate persistence
- support browser print preview and browser print
- re-calculate all loops before the report becomes printable
- show clear warning or blocking states if calculations are incomplete

### Out of Scope

- PDF export as a separate file-generation pipeline
- approval workflow or signature capture
- company-wide print templates
- formal issue history tables
- stamping or watermark rules
- backend-generated report PDFs
- desktop-app print implementation
- multilingual print localization changes

## Information Model

### Project-Level Print Profile

Add a new nested project field:

```ts
interface ProjectPrintProfile {
  project_no: string;
  customer: string;
  site: string;
  panel: string;
  revision: string;
  prepared_by: string;
  issue_date: string;
  notes: string;
}
```

Add it to the Web/shared project contract:

```ts
interface ProjectRecord {
  ...
  print_profile: ProjectPrintProfile | null;
}
```

The backend API should expose the same nested structure in `ProjectCreate`, `ProjectUpdate`, and `ProjectRead`.

### Persistence Direction

Conceptually, the print profile belongs to the project.

Storage recommendation:

- expose `print_profile` as part of the project API contract
- store it server-side as a dedicated one-to-one record tied to `project_id`

Reason:

- keeps project-level ownership clear
- avoids turning the main `projects` table into a wide document-header table
- preserves room for future print/report metadata growth without polluting the core project identity columns

The first implementation does not need app-wide reusable company defaults. The approved behavior is satisfied by project-level reuse.

## Routing and Navigation

Add a new route:

```text
/print
```

Recommended route name:

```text
print
```

Navigation behavior:

- left nav item label becomes `Print`
- clicking `Print` navigates to the dedicated preview view
- if there is no active project, `Print` stays disabled
- navigating away from `Print` should not auto-save preview metadata edits

The preview should use the same shell as the rest of the app, but with print-specific center content and toolbar actions.

## Print Preview Workflow

### Entry

When the user enters `Print Preview`:

1. snapshot the current active project from `workspaceStore`
2. copy `project.print_profile` into a local draft profile
3. trigger recalculation for every loop in the snapped project
4. disable the `Print` action until calculations finish

### Draft Behavior

Draft edits are local to the preview session.

- changing `Revision` in preview updates the rendered report immediately
- leaving preview without saving discards the temporary override
- `Save as Project Defaults` writes the draft into the project's saved `print_profile`

### Actions

The preview toolbar should provide exactly these high-value actions:

- `Print`
- `Save as Project Defaults`
- `Reset`
- `Back to Workspace`

Optional extra controls such as paper size, orientation, or theme switching should not be part of the first version. The first version is fixed to `A4 Portrait`.

## Calculation Freshness Rules

This feature prints the current working state of the project, not only the last saved backend state.

That is the correct engineering behavior because users expect the printed report to match the latest edits they are looking at.

To keep the report trustworthy:

- the preview must re-run calculation for every loop in the project before enabling `Print`
- if a loop is still calculating, the preview shows a `Calculating` state
- if a loop cannot calculate, that loop shows a clear failure state and `Print` remains disabled until the issue is resolved or explicitly acknowledged by the chosen implementation policy

Recommended first-version policy:

- disable `Print` while any loop calculation is incomplete or failed

This is stricter, but it avoids engineers printing a report with stale or partial numbers.

## Preview Layout

The print UI should be a full-page working surface, not a modal.

Recommended structure:

```text
Print Preview View
  Top action bar
    Back to Workspace
    Save as Project Defaults
    Reset
    Print

  Main body
    Left metadata panel
      editable print profile fields

    Right preview surface
      A4 page stack
```

The left panel is for editing metadata. The right side is the true paper preview.

## Report Layout

The report should use a fixed engineering-document structure.

### Page 1: Project Summary

Top section:

- `Project Name`
- `Project No`
- `Customer`
- `Site`
- `Panel`
- `Revision`
- `Prepared By`
- `Issue Date`

Middle summary metrics:

- `Total Loops`
- `Total Devices`
- `Worst Address Utilization`
- `Worst Current Utilization`
- `Lowest End Voltage`
- `Global Battery Standby Runtime`
- `Global Battery Alarm Runtime`

Bottom summary table:

- `Loop`
- `Devices`
- `Addr Used / Limit`
- `Current Used / Limit`
- `Distance`
- `End Voltage`
- `Cable`
- `Status`

### Loop Pages

Each loop starts on a new page.

Loop page structure:

1. `Loop Header`
2. `Loop Result Summary`
3. `Loop Parameters`
4. `Diagnostics`
5. `Device Schedule`

#### Loop Header

- `Project Name`
- `Project No`
- `Loop Name`
- `Revision`
- `Issue Date`

#### Loop Result Summary

- `Addresses`
- `Current`
- `Distance`
- `Voltage Drop`
- `End Voltage`
- `Recommended Cable`

This block should visually answer the question: "Is this loop valid, and what cable/result should I trust?"

#### Loop Parameters

- `Address Limit`
- `Max Current`
- `Min Voltage`
- `Cable Size`
- `Cable Resistance`
- `AUX Current`

#### Diagnostics

Diagnostics are high priority on paper and must never be buried at the bottom of the report.

- if a loop has diagnostics, place them directly under the result summary
- use a strong but controlled warning style
- preserve the message order from calculation output

#### Device Schedule

Recommended columns:

- `#`
- `Category`
- `Device / Model`
- `Qty`
- `Addr/ea`
- `SBY mA/ea`
- `ALM mA/ea`
- `Lead m`
- `Interval m`

Field mapping notes:

- `Addr/ea` comes from the row address cost field already represented in the data as `led_cost`
- `SBY mA/ea` comes from `standby_ma`
- `ALM mA/ea` comes from `alarm_ma`

This is intentionally an engineering schedule, not the exact same column set as the editable workspace table.

## Pagination Rules

Use explicit print CSS.

Required rules:

- `@page { size: A4 portrait; }`
- fixed document margins suitable for engineering tables
- each loop page starts with `page-break-before: always`
- device table header repeats on continuation pages
- individual device rows should avoid splitting across pages
- page footers repeat document context

Recommended footer content:

- `Project Name`
- `Loop Name` or `Project Summary`
- `Revision`
- `Page x of y`

Recommended first-version page margins:

- top: `14mm`
- right: `12mm`
- bottom: `12mm`
- left: `12mm`

Exact numbers can be tuned during implementation, but the design assumes real A4 pagination, not responsive-screen layout.

## Key Engineering Information Priority

The report must reflect how engineers actually review loop calculations:

1. determine whether the project is within limits
2. identify which loop is worst or invalid
3. review the key electrical metrics for that loop
4. inspect the device schedule that produced those metrics

That leads to this priority order:

- project/loop validity
- addresses, current, voltage, distance, cable
- diagnostics
- device schedule detail
- freeform notes

The report should not prioritize decorative branding over calculation clarity.

## UI States and Validation

### First-Time Project Without Print Profile

If the project has no saved `print_profile`:

- open preview with empty editable fields
- prefill `Issue Date` with the current local date
- allow preview editing immediately
- require the minimum fields needed for a credible report before enabling `Print`

Recommended minimum required fields:

- `Project No`
- `Customer`
- `Revision`
- `Prepared By`
- `Issue Date`

`Site`, `Panel`, and `Notes` may be optional.

### Unsaved Workspace Edits

If the active project has unsaved workspace changes:

- preview still uses the current in-memory state
- show a subtle banner such as `Printing current unsaved working state`
- do not force a project save before previewing or printing

### No Loops or Empty Data

If the project contains zero loops:

- render the project summary header
- show a clear empty-state message instead of a broken report
- keep `Print` disabled if the report would be structurally empty

## Frontend Design Changes

Recommended new frontend pieces:

```text
frontend/src/
  views/
    PrintPreviewView.vue
  components/print/
    PrintProfilePanel.vue
    PrintPageStack.vue
    ProjectSummaryPage.vue
    LoopReportPage.vue
    DeviceScheduleTable.vue
  stores/
    printStore.ts
  types/
    print.ts
```

Store responsibilities:

- `workspaceStore` remains source of truth for active project editing
- `printStore` owns preview draft state, recalculation readiness, and save/reset actions

This keeps print-specific behavior out of the main editing store.

## Backend Design Changes

Recommended API direction:

- extend project schemas with nested `print_profile`
- persist print profile server-side
- return print profile with normal project reads

Recommended storage direction:

- add a new table for project print profiles keyed by `project_id`
- join/load it when reading a project
- replace it when saving a project

This keeps the API simple while containing the storage impact.

## Error Handling

The print feature should fail clearly.

Expected error cases:

- project metadata save fails
- one or more loops fail recalculation
- print profile load is missing or malformed
- project becomes unavailable while preview is open

Expected behavior:

- keep the user in preview
- show an actionable error message
- do not silently drop the preview draft
- do not print partially refreshed engineering data

## Testing Strategy

### Frontend Tests

- route test for the new `print` route
- left-nav test confirming `Preferences` is replaced by `Print`
- `printStore` tests for:
  - draft initialization from saved profile
  - temporary edits not persisting automatically
  - `Save as Project Defaults`
  - `Reset`
- preview tests confirming:
  - project summary page renders expected fields
  - each loop produces a page section
  - diagnostic blocks appear when present
  - print button is disabled while recalculations are pending

### Data Contract Tests

- TypeScript and backend schema coverage for nested `print_profile`
- serialization/deserialization tests for optional and empty profile states

### Manual Verification

- open a project with multiple loops
- enter `Print`
- fill metadata once
- save defaults
- leave and re-enter to confirm reuse
- temporarily modify `Revision` without saving and confirm reset behavior
- print preview in browser and verify `A4 Portrait`
- confirm multi-page layout with loop page breaks

## Implementation Boundaries

The first implementation should stay disciplined:

- no new branding system
- no export-format matrix
- no document-approval workflow
- no desktop print work
- no attempt to make screen layout and paper layout share the same component tree everywhere

The print components should be optimized for print readability first.

## Final Recommendation

Build a dedicated project print module centered on a project-level saved print profile and a true `A4 Portrait` preview route.

This gives the user:

- the requested `Preferences` to `Print` replacement
- first-time metadata entry with reuse
- temporary preview edits without accidental persistence
- an engineering-readable whole-project report
- controlled pagination and trustworthy loop calculations

This is the smallest design that still behaves like a real engineering print feature instead of a dressed-up browser print shortcut.
