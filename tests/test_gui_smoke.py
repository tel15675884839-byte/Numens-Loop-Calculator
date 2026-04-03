from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


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
