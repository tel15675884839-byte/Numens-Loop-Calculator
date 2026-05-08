# Offline Cache and Library Sync Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the deployed Web app usable offline after first load while keeping the device Library refreshed from the backend whenever the user is online.

**Architecture:** Add a small hand-written service worker for static frontend assets and keep existing localStorage business-data fallbacks. Update backend startup storage so built-in products from `products_db.json` are synchronized into SQLite on every initialization, while custom user products remain untouched.

**Tech Stack:** Vue 3, Vite, TypeScript, Pinia, FastAPI, SQLite, browser Service Worker Cache API.

---

### Task 1: Backend Built-In Library Synchronization

**Files:**
- Modify: `backend/app/storage.py`
- Modify: `backend/tests/test_storage.py`

- [ ] Write failing tests that prove `SQLiteStore.initialize()` updates existing built-in products from the seed JSON and removes retired built-in products, but keeps custom products.

- [ ] Run: `pytest backend/tests/test_storage.py -v`
Expected: new sync test fails before implementation.

- [ ] Implement minimal storage behavior:
  - Load seed product IDs from `products_db.json` during initialization.
  - Delete existing `built_in = 1` products that are not present in the seed.
  - Upsert all seed products with `built_in = 1` using existing `seed_from_json()` behavior.
  - Do not delete or overwrite `built_in = 0` custom products.

- [ ] Run: `pytest backend/tests/test_storage.py -v`
Expected: storage tests pass.

- [ ] Run: `pytest backend/tests/`
Expected: backend tests pass.

### Task 2: Frontend Static Offline Cache

**Files:**
- Create: `frontend/public/sw.js`
- Create: `frontend/src/pwa.ts`
- Modify: `frontend/src/main.ts`

- [ ] Add `frontend/public/sw.js` with a versioned cache name, install pre-cache for `/`, `/index.html`, `/favicon.ico`, `/icon.png`, `/logo-long.png`, `/logo-long-black.png`, and runtime cache for same-origin `GET` requests excluding `/api/`.

- [ ] Add navigation fallback so route refreshes work offline by returning cached `/index.html`.

- [ ] Add activate cleanup for old caches and `clients.claim()` so new deployments update automatically when online.

- [ ] Add `frontend/src/pwa.ts` exporting `registerServiceWorker()` with guards for unsupported browsers, development mode, and non-secure origins.

- [ ] Call `registerServiceWorker()` from `frontend/src/main.ts` after app mount.

- [ ] Run: `cd frontend && npm run build`
Expected: Vite copies `public/sw.js` into `dist/sw.js` and TypeScript build succeeds.

### Task 3: Verification

**Files:**
- No production changes expected unless checks fail.

- [ ] Run: `pytest backend/tests/`
Expected: all backend tests pass.

- [ ] Run: `pytest tests/test_database.py`
Expected: product database tests pass.

- [ ] Run: `cd frontend && npm test`
Expected: frontend tests pass.

- [ ] Run: `cd frontend && npm run build`
Expected: build succeeds and `frontend/dist/sw.js` exists.

- [ ] Record results and any caveats in `.trellis/workspace/Developer/journal-1.md`.

## Self-Review

- Spec coverage: covers offline static frontend caching, online Library refresh via backend product sync, local user data preserved through existing localStorage paths, and update behavior through versioned service worker caches.
- Placeholder scan: no placeholders or TBD items.
- Type consistency: backend storage APIs remain unchanged; frontend adds a single `registerServiceWorker()` function called from `main.ts`.
