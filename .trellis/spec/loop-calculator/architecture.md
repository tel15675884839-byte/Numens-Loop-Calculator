# Loop Calculator Architecture

## Runtime Surfaces

Loop Calculator has four active surfaces:

- `loop_calculator/`: PySide6 desktop application plus reusable calculation and product-management modules.
- `backend/`: FastAPI app, SQLite-backed storage, API schemas, and service behavior.
- `frontend/`: Vue 3, Vite, TypeScript, Tailwind-based web UI.
- Root data/config files: `products_db.json`, `products_db.defaults.json`, `app_settings.json`, and spreadsheet conversion helpers.

## Boundaries

- Keep `loop_calculator/calculator.py` Qt-free and directly unit-testable.
- Keep electrical calculation rules out of UI components.
- Keep FastAPI request/response contracts in `backend/app/schemas.py`.
- Keep backend business behavior in `backend/app/services.py`.
- Keep backend persistence rules in `backend/app/storage.py` and related storage modules.
- Keep Vue API calls under `frontend/src/api/`, state under `frontend/src/stores/`, shared interfaces under `frontend/src/types/`, and calculation helpers under `frontend/src/utils/`.

## Data Flow

Product data should flow from source files or backend storage through product-manager/service APIs into UI layers. Do not duplicate electrical values or product identity rules inside PySide6 widgets or Vue components.

## Calculation Rules

Preserve unit conventions:

- Voltage: `V`
- Current: `mA`
- Resistance: `Ohm/km`
- Cable length: `m`

Any change in voltage drop, standby current, alarm current, cable recommendation, or device load aggregation must include a matching test.

## Task Scope Rule

When the user asks for UI-only work, do not change calculation or persistence behavior. When the user asks for backend/data behavior, do not redesign frontend layout unless required to expose the behavior.
