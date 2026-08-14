from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

from loop_calculator import __version__ as core_version


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_VERSION = "1.1.1"


def test_numens_desktop_release_versions_are_synchronized() -> None:
    tauri_config = json.loads(
        (ROOT / "frontend" / "src-tauri" / "tauri.conf.json").read_text(encoding="utf-8")
    )
    cargo_manifest = tomllib.loads(
        (ROOT / "frontend" / "src-tauri" / "Cargo.toml").read_text(encoding="utf-8")
    )
    cargo_lock = tomllib.loads(
        (ROOT / "frontend" / "src-tauri" / "Cargo.lock").read_text(encoding="utf-8")
    )
    desktop_package = next(
        package
        for package in cargo_lock["package"]
        if package["name"] == "loop-calculator-desktop"
    )
    frontend_version = (ROOT / "frontend" / "src" / "config" / "version.ts").read_text(
        encoding="utf-8"
    )
    installer_config = (ROOT / "installer" / "loop-calculator.iss").read_text(
        encoding="utf-8"
    )
    update_manifest = json.loads(
        (ROOT / "frontend" / "public" / "updates" / "windows" / "latest.json").read_text(
            encoding="utf-8"
        )
    )

    assert tauri_config["version"] == EXPECTED_VERSION
    assert cargo_manifest["package"]["version"] == EXPECTED_VERSION
    assert desktop_package["version"] == EXPECTED_VERSION
    assert core_version == EXPECTED_VERSION
    escaped_version = re.escape(EXPECTED_VERSION)
    assert re.search(rf'APP_VERSION\s*=\s*"{escaped_version}"', frontend_version)
    assert re.search(rf"^AppVersion={escaped_version}$", installer_config, re.MULTILINE)
    assert update_manifest["app_version"] == EXPECTED_VERSION
    assert f"/releases/download/v{EXPECTED_VERSION}/" in update_manifest["installer_url"]
    assert re.fullmatch(r"[0-9a-f]{64}", update_manifest["sha256"])
