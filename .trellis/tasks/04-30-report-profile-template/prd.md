# PRD: Report Profile Template Gallery (Local Storage)

## Overview
Enable users to save their frequently used "Report Profile" configurations (Project No, Customer, Site, etc.) into a local "Template Gallery". Users can then directly select a template from a list to auto-fill the form, eliminating repetitive manual input.

## Goals
1. Allow saving the current form state as a named template.
2. Provide a UI list to browse and select previously saved templates.
3. Persistent storage using LocalStorage (cross-project accessibility).

## Functional Requirements
- **Save Template**:
    - A "Save as New Template" button.
    - Prompt the user for a template name (e.g., "Main Contractor A", "Default Site B").
    - Save the 8 fields (`project_no`, `customer`, `site`, `panel`, `revision`, `prepared_by`, `issue_date`, `notes`) into a local list.
- **Apply Template**:
    - An "Import Profile" or "Templates" menu/dropdown.
    - Display a list of saved templates.
    - Upon selection, update the current `draftProfile` in `printStore`.
- **Manage Templates**:
    - Option to delete unwanted templates.

## UI Design
- **Top Section**: Replace "IMPORT PROFILE" text with a "TEMPLATES" dropdown or a button that opens a selection menu.
- **Action Section**: Add a "Save as Template" button near the bottom.
- **Interaction**: Selecting a template immediately populates the form fields.

## Technical Notes
- Data should be stored in LocalStorage under a key like `loop-calculator.report-templates`.
- Use `usePrintStore` to manage the list of templates and the application logic.
- Ensure the `Issue Date` can either be preserved from the template or auto-updated to "today" (provide option or clear logic).
