# Loop Calculator

Loop Calculator is a Web-first industrial loop load and voltage-drop calculator for engineering workflows such as fire alarm and safety system design.

The active application is split into:

- `frontend/`: Vue 3, Vite, TypeScript, and Tailwind UI.
- `backend/`: FastAPI API with SQLite persistence.
- `loop_calculator/`: Qt-free Python calculation and product-data helpers reused by backend/tests.
- `products_db.json`: active product seed data.

The old PySide6 desktop GUI has been isolated in:

- `archive/desktop_gui_2026-05-06/`
- `archive/desktop_gui_2026-05-06.zip`

## Setup

Install backend dependencies:

```bash
pip install -r requirements.txt
```

Install frontend dependencies:

```bash
cd frontend
npm install
```

## Run

Start the backend:

```bash
uvicorn backend.app.main:app --reload
```

Start the frontend:

```bash
cd frontend
npm run dev
```

## Test

Run active Python tests:

```bash
pytest tests/
pytest backend/tests/
```

Run frontend tests and build:

```bash
cd frontend
npm test
npm run build
```

## Data Notes

- Keep electrical calculation logic in `loop_calculator/calculator.py`.
- Keep backend API schemas in `backend/app/schemas.py`.
- Keep product identity and seed data aligned with `products_db.json`.
- Review `数据库合并去重机制.md` before changing merge or deduplication behavior.
