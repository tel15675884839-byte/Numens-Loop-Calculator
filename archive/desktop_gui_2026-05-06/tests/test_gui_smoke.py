from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from loop_calculator.loop_editor import LoopEditorWidget
from loop_calculator.main_window import CIEMainWindow


def test_gui_can_start_in_offscreen_mode() -> None:
    root = Path(__file__).resolve().parents[1]
    runner = Path(__file__).resolve().parent / "gui_smoke_runner.py"

    env = dict(os.environ)
    env["QT_QPA_PLATFORM"] = "offscreen"

    proc = subprocess.run(
        [sys.executable, str(runner)],
        cwd=str(root),
        env=env,
        capture_output=True,
        text=True,
        timeout=20,
        check=False,
    )

    assert proc.returncode == 0, f"stderr:\n{proc.stderr}\nstdout:\n{proc.stdout}"
    assert "GUI_SMOKE_OK" in proc.stdout


def test_loop_page_keeps_results_top_aligned_on_small_screen() -> None:
    app = QApplication.instance() or QApplication([])
    window = CIEMainWindow()
    try:
        window.resize(1024, 600)
        window._on_nav_clicked("loops")
        window.show()
        app.processEvents()

        loop = window.tab_widget.currentWidget()
        assert isinstance(loop, LoopEditorWidget)
        assert window.width() <= 1024
        assert loop.res_group.y() <= loop.sys_group.y() + 8
        assert loop.combo_addr_limit.width() <= 180
        assert loop.combo_cable.width() <= 220
    finally:
        window.close()
