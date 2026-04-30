# Product Database Naming and Data Rules

## Source Files

- `products_db.json` is the active product database.
- `products_db.defaults.json` is the default/reference product source.
- Spreadsheet imports should prefer `convert_xlsx_robust.py` when the source format is uncontrolled.

## Identity Rules

- Preserve unique `product_id` values during imports, merges, and manual edits.
- Do not infer product identity from display name alone.
- Avoid hard-coding product electrical values in UI components.

## API and Storage Naming

- Keep backend request/response field names in `backend/app/schemas.py`.
- Keep API payload names aligned with frontend shared types under `frontend/src/types/`.
- If a field is renamed, update backend schema, service/storage mapping, frontend type, store usage, and tests in the same task.

## Merge and Deduplication Changes

Before changing merge or deduplication behavior:

- Read `数据库合并去重机制.md`.
- Add or update a database test that covers duplicate detection, preserved IDs, and expected conflict behavior.
- Record the decision in `.trellis/workspace/` if the rule becomes reusable.
