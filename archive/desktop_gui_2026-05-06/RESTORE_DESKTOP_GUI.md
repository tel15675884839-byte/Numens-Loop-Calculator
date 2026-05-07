# Desktop GUI Archive

This folder is a snapshot of the removed PySide6 desktop GUI files from 2026-05-06.

The active project is Web-first. These files are kept only so the desktop app can be restored later if needed.

## Contents

- Desktop entry points: `LoopCalculatorApp.py`, `loop_calculator/main.py`, `loop_calculator/__main__.py`, and `启动程序.bat`.
- PySide6 UI modules under `loop_calculator/`.
- Desktop-only assets under `assets/`.
- GUI smoke tests under `tests/`.
- A copy of the original `requirements.txt`, `README.md`, `AGENTS.md`, product data, and pure calculation modules needed by the desktop app.

## Restore

To restore the desktop GUI in a separate working copy, extract this archive at the repository root so the relative paths line up again.

Then install the archived desktop requirements:

```bash
pip install -r requirements.txt
```

Run the desktop app:

```bash
python LoopCalculatorApp.py
```

The current active repository intentionally does not install PySide6 by default.
