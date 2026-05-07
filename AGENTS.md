# AGENTS.md

## Project Overview

Loop Calculator is now maintained as a Web-first industrial loop load and voltage-drop calculator. The active repository contains:

- `frontend/`: Vue 3 + Vite + TypeScript frontend.
- `backend/`: FastAPI backend backed by SQLite and seeded from `products_db.json`.
- `loop_calculator/`: Qt-free Python core logic kept for calculation, product data helpers, and legacy-compatible tests.
- `tests/`: Python tests for calculation, database, integration, and pure state-model coverage.
- Root data files such as `products_db.json` and `products_db.defaults.json`.
- Archived desktop GUI artifacts under `archive/desktop_gui_2026-05-06/` and `archive/desktop_gui_2026-05-06.zip`.

Use this file as the primary agent guidance. Keep agent-facing instructions here rather than maintaining parallel `AGENT.md` or tool-specific files.

## Setup Commands

- Install Python backend dependencies from the repository root:
  ```bash
  pip install -r requirements.txt
  ```
- Install frontend dependencies:
  ```bash
  cd frontend
  npm install
  ```

## Run Commands

- Run the FastAPI backend:
  ```bash
  uvicorn backend.app.main:app --reload
  ```
- Run the Vite frontend:
  ```bash
  cd frontend
  npm run dev
  ```
- Build the frontend:
  ```bash
  cd frontend
  npm run build
  ```

## Test Commands

- Run all active root Python tests:
  ```bash
  pytest tests/
  ```
- Run core calculation tests after changing calculation logic:
  ```bash
  pytest tests/test_calculator.py
  ```
- Run database tests after changing product data, import logic, or persistence behavior:
  ```bash
  pytest tests/test_database.py
  ```
- Run backend API tests after changing `backend/`:
  ```bash
  pytest backend/tests/
  ```
- Run frontend tests after changing `frontend/src/`:
  ```bash
  cd frontend
  npm test
  ```

## Architecture Guidelines

- Keep `loop_calculator/calculator.py` Qt-free. Do not import PySide6, Qt widgets, or GUI-specific code into active core modules.
- Keep electrical calculation logic in pure Python modules so it remains unit-testable and reusable by the backend.
- Treat `products_db.json` and `products_db.defaults.json` as data sources. Do not hard-code product electrical values in UI components.
- Use backend storage/service APIs for Web product data changes instead of duplicating data access rules in Vue components.
- Keep FastAPI request/response contracts in `backend/app/schemas.py`; put backend business behavior in `backend/app/services.py`.
- In the Vue app, keep API calls under `frontend/src/api/`, shared state under `frontend/src/stores/`, shared types under `frontend/src/types/`, and calculation helpers under `frontend/src/utils/`.
- Do not reintroduce desktop GUI code into the active tree unless the user explicitly asks to restore the archived desktop app.

## Calculation Rules

- Preserve unit conventions:
  - Voltage: `V`
  - Current: `mA`
  - Resistance: `Ohm/km`
  - Cable length: `m`
- Any behavior change in voltage-drop, standby current, alarm current, cable recommendation, or device load aggregation must include or update tests.
- Prefer explicit numeric conversions and named constants over inline magic numbers.

## UI and Localization

- For the Vue frontend, follow the existing component structure and Tailwind-based styling in `frontend/src/styles.css`.
- Keep shared UI behavior inside existing components, stores, and utilities before introducing new dependencies.
- Use existing icons and component patterns before introducing new UI dependencies.
- Keep user-facing Web text consistent with the current product terminology and data model.

## Data Maintenance

- When importing or merging Excel/device data, preserve unique `product_id` values.
- Review `数据库合并去重机制.md` before changing data merge or deduplication behavior.
- Prefer the robust converter (`convert_xlsx_robust.py`) for uncontrolled source spreadsheets.
- Do not commit generated caches such as `__pycache__/`, `.pytest_cache/`, or build output unless explicitly requested.

## Code Style

- Python: follow the local style, keep modules small, and prefer typed dataclasses/models where already used.
- TypeScript/Vue: preserve strict typing, keep shared interfaces in `frontend/src/types/`, and avoid duplicating API payload shapes inside components.
- Keep comments concise and focused on non-obvious behavior.
- Do not perform unrelated formatting churn.

## Verification Before Finishing

Run the smallest meaningful checks for the files you changed. For broad changes, prefer:

```bash
pytest tests/
pytest backend/tests/
cd frontend && npm test && npm run build
```

If a check cannot run in the current environment, report the exact command and failure reason.
