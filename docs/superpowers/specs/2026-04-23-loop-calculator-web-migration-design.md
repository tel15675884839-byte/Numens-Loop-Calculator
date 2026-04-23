# Loop Calculator Web Migration Design

Date: 2026-04-23
Status: Approved for implementation planning

## Goal

Migrate the existing Python/PySide6 Loop Calculator into a modern Web application while preserving the proven calculation logic and redesigning the interface as a professional engineering workstation.

The first implementation phase will be a vertical product slice, not a full rewrite. It must deliver a usable Web workflow for creating projects, editing multiple loops, selecting products, running real loop calculations, saving work, and making basic product-library edits.

## Current Project Findings

The current application already has useful separation points:

- `loop_calculator/calculator.py` is Qt-free and contains the core loop calculation logic.
- `loop_calculator/device_list_state.py` and `loop_calculator/device_list_model.py` provide Qt-free row/state structures that can inform the Web data model.
- `products_db.json` is the current product database source.
- The current UI embeds permission behavior through `auth_level`, with view, admin, and factory-style capabilities.
- The current desktop workflow includes system parameters, device rows, multi-loop tabs, calculation results, diagnostics, and product database management.

The migration should reuse the domain logic rather than rewrite it.

## Design Direction

The selected visual direction is a professional engineering workstation.

Primary traits:

- Light and neutral surfaces.
- Dense but readable tables.
- Clear parameter grouping.
- Thin dividers and restrained state colors.
- Numeric values right-aligned.
- Units visible and consistent.
- Minimal decoration.
- No marketing-style landing page for the app surface.
- No dark industrial control-console theme for the first Web version.

The interface should feel closer to an engineering calculation platform, CAD/BOM workspace, or technical configuration tool than to a generic SaaS dashboard.

## Phase 1 Scope

Phase 1 will implement a vertical slice:

- Vue3 frontend application.
- FastAPI backend application.
- Reuse `loop_calculator/calculator.py`.
- Initialize products from `products_db.json`.
- Project list.
- Create, open, save, and delete projects.
- Multi-loop tabs inside each project.
- System parameter editing.
- Device table editing.
- Real calculation API calls.
- Right-side calculation results and diagnostics.
- Basic product-library editing:
  - Search.
  - Category filter.
  - Add product.
  - Edit product.
  - Delete non-protected product.

Phase 1 will not include:

- Login.
- JWT.
- User/Admin/Factory enforcement.
- Excel import.
- Product deduplication workflow.
- Factory mode.
- User administration.
- Production server deployment.
- PDF or Excel report export.
- Full multilingual migration.
- Custom logo replacement.
- Desktop packaging replacement.

Permission and role concepts should still be reserved in route/module structure so that Phase 2 can add them without reshaping the application.

## Application Layout

The main application is a three-zone engineering workspace.

```text
Top Bar
  Current project name
  Save status
  New project
  Save
  Future export entry

Left Panel: Project-Level Navigation
  Project List
  Product Library
  Settings placeholder

Center Workspace: Loop Editing
  Loop tabs
    Loop 1
    Loop 2
    + Add Loop

  System Parameters
    Address Limit
    Max Current
    Min Voltage
    Cable Spec

  Device Table
    #
    Category
    Device
    Lead Distance
    Interval Distance
    Qty
    Standby
    Alarm
    Actions

Right Inspector: Calculation Results
  Status
  Circuit Metrics
  Safety Suggestions
  Diagnostics
```

Important layout decision:

- Loop navigation belongs in the center workspace, not the left panel.
- The left panel is only for project-level navigation.
- The right inspector remains visible while editing device rows.

## Frontend Architecture

Recommended stack:

- Vue3.
- TypeScript.
- Vite.
- Pinia.
- Vue Router.
- Tailwind CSS.
- A table component can be custom-built first; add a grid library only if row editing becomes complex.

Suggested frontend structure:

```text
frontend/
  src/
    api/
      client.ts
      projects.ts
      products.ts
      calculations.ts
    router/
      index.ts
    stores/
      projectStore.ts
      productStore.ts
      workspaceStore.ts
    views/
      WorkspaceView.vue
      ProductLibraryView.vue
    components/
      layout/
        AppShell.vue
        TopBar.vue
        LeftNav.vue
      workspace/
        LoopTabs.vue
        SystemParameters.vue
        DeviceTable.vue
        CalculationInspector.vue
      products/
        ProductFilters.vue
        ProductTable.vue
        ProductEditorDrawer.vue
    types/
      project.ts
      product.ts
      calculation.ts
```

Frontend state shape:

```text
Workspace
  projects[]
  activeProjectId
  activeLoopId
  dirtyState

Project
  id
  name
  activeLoopId
  loops[]

Loop
  id
  name
  sortOrder
  systemParameters
  deviceRows[]
  calculationResult
```

Calculation interaction:

- Edits to system parameters or device rows update local state immediately.
- Frontend calls calculation API with debounce.
- Calculation API is stateless and does not save the project.
- Save action persists the whole project state.

## Backend Architecture

Recommended stack:

- FastAPI.
- Pydantic.
- SQLAlchemy or SQLModel.
- SQLite for early development.
- PostgreSQL later for server deployment.
- Alembic once the schema stabilizes.

Suggested backend structure:

```text
backend/
  app/
    main.py
    core/
      config.py
      security.py
      permissions.py
    api/
      routes/
        projects.py
        products.py
        calculations.py
        categories.py
    domain/
      calculator_adapter.py
    models/
      project.py
      product.py
    schemas/
      project.py
      product.py
      calculation.py
    services/
      project_service.py
      product_service.py
      calculation_service.py
      product_import_seed.py
    repositories/
      project_repository.py
      product_repository.py
    db/
      session.py
      base.py
      migrations/
  tests/
```

The backend must not move business calculation into route handlers. Route handlers should validate HTTP input and call services. Services should call the domain adapter, and the adapter should call the existing calculator module.

## Data Model

Phase 1 database entities:

```text
projects
  id
  name
  active_loop_id
  created_at
  updated_at

project_loops
  id
  project_id
  name
  sort_order
  address_limit
  max_current_ma
  min_voltage_v
  cable_size
  cable_resistance_ohm_per_km
  aux_current_ma

loop_device_rows
  id
  loop_id
  sort_order
  product_id nullable
  category
  display_name
  customer_name
  factory_name
  product_name
  standby_ma
  alarm_ma
  led_cost
  device_type
  lead_dist_m
  interval_dist_m
  qty

products
  id
  category
  factory_name
  customer_name
  product_name
  standby_ma
  alarm_ma
  led_cost
  device_type
  built_in
  created_at
  updated_at

categories
  id
  name
  sort_order
```

Device rows intentionally store product snapshots.

Reasons:

- Historical projects must remain reproducible.
- A later product-library edit should not silently change old project calculations.
- A future "sync from product library" action can update rows explicitly.

## API Design

Project API:

```text
GET    /api/projects
POST   /api/projects
GET    /api/projects/{project_id}
PUT    /api/projects/{project_id}
DELETE /api/projects/{project_id}
```

Loop API:

```text
POST   /api/projects/{project_id}/loops
PUT    /api/projects/{project_id}/loops/{loop_id}
DELETE /api/projects/{project_id}/loops/{loop_id}
```

Calculation API:

```text
POST   /api/calculations/loop
```

Product API:

```text
GET    /api/products
POST   /api/products
PUT    /api/products/{product_id}
DELETE /api/products/{product_id}
```

Category API:

```text
GET    /api/categories
POST   /api/categories
```

Calculation request example:

```json
{
  "devices": [
    {
      "product_id": "product-0001",
      "display_name": "Optical Smoke Detector",
      "category": "Detector",
      "standby": 0.5,
      "alarm": 2.0,
      "ledCost": 1,
      "type": "Detector",
      "lead_dist": 10,
      "interval_dist": 10,
      "qty": 15
    }
  ],
  "max_current_ma": 400,
  "min_voltage_v": 17,
  "cable_resistance_ohm_per_km": 12.1,
  "addr_limit": 125
}
```

Calculation response example:

```json
{
  "total_addresses": 45,
  "total_current_ma": 120.5,
  "total_distance_m": 320,
  "voltage_drop_v": 1.42,
  "end_voltage_v": 26.58,
  "max_install_distance_m": 1000,
  "recommended_cable_size": "1.5",
  "recommended_cable_unit": "mm²",
  "diagnostics": []
}
```

## Product Library Behavior

Phase 1 product-library behavior:

- Seed products from `products_db.json`.
- Preserve current product identifiers where possible.
- Allow category filtering.
- Allow text search across category, customer name, factory name, and product name.
- Allow adding products.
- Allow editing basic fields.
- Allow deleting products that are not protected built-in records, or require explicit confirmation if built-in deletion is allowed.

Excel import and deduplication remain out of Phase 1.

## Permission Strategy

Phase 1 will not implement login or role enforcement.

However, backend modules should be named and shaped so Phase 2 can add:

- `User`.
- `Admin`.
- `Factory`.
- JWT authentication.
- Route-level role dependencies.
- Product-library operation permissions.
- Audit logs.

The calculation API should remain available to authenticated users in the future, but should not need role-specific logic.

## Migration Phases

### Phase 1: Web Workstation Vertical Slice

Build the usable calculation workspace:

1. Create backend skeleton.
2. Connect backend to existing `loop_calculator/calculator.py`.
3. Define database schema.
4. Seed products from `products_db.json`.
5. Add calculation API.
6. Add project persistence API.
7. Add product CRUD API.
8. Create Vue application shell.
9. Build project-level left navigation.
10. Build center loop tabs and editor.
11. Build right calculation inspector.
12. Connect real products and real calculation API.
13. Connect save/open project flow.
14. Add basic product-library page.
15. Polish professional engineering workstation styling.

### Phase 2: Product Library and Permissions

Add:

- Login.
- JWT.
- `User/Admin/Factory` roles.
- Product-library operation permissions.
- Excel import.
- Product deduplication.
- Restore default product database.
- Audit logs.

### Phase 3: Engineering Enhancements

Add:

- Project import/export.
- PDF or Excel reports.
- Version history.
- User settings.
- Multilingual UI.
- Expanded automated tests.

### Phase 4: Server Deployment

Add:

- Self-owned server deployment.
- HTTPS.
- Database backup.
- Upload archive.
- Production logging.
- Environment-specific configuration.

## Testing Strategy

Backend tests:

- Keep existing `tests/test_calculator.py` as the source of calculation truth.
- Add API tests for `/api/calculations/loop`.
- Add repository/service tests for project save and reload.
- Add product seed tests from `products_db.json`.

Frontend tests:

- Smoke test the main workspace loads.
- Verify loop tab add/switch/remove.
- Verify device row edits call calculation and update inspector.
- Verify project save and reload round-trip.
- Verify product-library search/filter/edit.

Manual UX checks:

- Long device names do not break table layout.
- Numeric columns remain readable.
- Right inspector remains visible during table editing.
- Warning and error states are distinguishable without overwhelming the screen.

## Open Implementation Notes

- Use SQLite during local development unless PostgreSQL is needed earlier.
- Keep product snapshots in device rows.
- Do not make a dashboard landing page before the working surface.
- Do not couple permissions to calculation logic.
- Do not migrate Excel import until the core Web workflow is stable.
