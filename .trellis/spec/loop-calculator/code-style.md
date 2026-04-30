# Loop Calculator Code Style

## Python

- Follow existing module style and naming.
- Prefer typed dataclasses/models where the surrounding code already uses them.
- Keep modules small and focused.
- Use explicit numeric conversions and named constants instead of inline magic numbers.
- Keep comments short and only for behavior that is not obvious from the code.

## PySide6

- Use `loop_calculator/i18n.py` for user-facing text where the surrounding UI is localized.
- Keep widget styling centralized in `loop_calculator/styles.py`.
- Do not add one-off stylesheet strings unless the local component already owns that pattern.

## FastAPI

- Keep Pydantic schemas in `backend/app/schemas.py`.
- Put reusable business behavior in services, not route handlers.
- Keep persistence and seed/import behavior behind storage/service APIs.

## Vue / TypeScript

- Preserve strict typing.
- Put shared payload shapes in `frontend/src/types/`.
- Avoid duplicating backend response interfaces inside components.
- Follow existing component layout and Tailwind utilities in `frontend/src/styles.css`.
- Use existing icons and component patterns before adding dependencies.

## Verification

Use the narrowest check that proves the touched area:

- Calculation: `pytest tests/test_calculator.py`
- Product data/storage: `pytest tests/test_database.py`
- Backend API: `pytest backend/tests/`
- PySide6 smoke: `python tests/gui_smoke_runner.py`
- Frontend: `cd frontend && npm test` and `cd frontend && npm run build` when UI code changes affect routing/build behavior.
