from __future__ import annotations

import sys
import traceback
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


class FileGuard:
    def __init__(self, path: Path):
        self.path = path
        self._original: str | None = None
        self._existed = path.exists()

    def ensure_json(self, fallback_payload: dict) -> None:
        if self._existed:
            self._original = self.path.read_text(encoding="utf-8")
            try:
                json.loads(self._original)
                return
            except json.JSONDecodeError:
                pass
        self.path.write_text(json.dumps(fallback_payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def restore(self) -> None:
        if self._original is not None:
            self.path.write_text(self._original, encoding="utf-8")
            return
        if not self._existed and self.path.exists():
            self.path.unlink()


def main() -> int:
    db_guard = FileGuard(ROOT / "products_db.json")
    settings_guard = FileGuard(ROOT / "app_settings.json")
    try:
        db_guard.ensure_json({"categories": [], "products": []})
        settings_guard.ensure_json(
            {
                "admin_password": "1",
                "factory_password": "8",
                "custom_logo_path": "",
            }
        )
        try:
            from PySide6.QtCore import QTimer
            from PySide6.QtWidgets import QApplication

            from loop_calculator.main_window import CIEMainWindow
        except Exception:
            traceback.print_exc()
            return 2

        app = QApplication.instance() or QApplication([])
        window = CIEMainWindow()
        window.show()
        QTimer.singleShot(250, app.quit)
        app.exec()
        print("GUI_SMOKE_OK")
        return 0
    finally:
        settings_guard.restore()
        db_guard.restore()


if __name__ == "__main__":
    raise SystemExit(main())
