"""Persisted application settings for passwords and custom branding."""

from __future__ import annotations

import json
from pathlib import Path

from .constants import ADMIN_PASSWORD, APP_SETTINGS_FILENAME, FACTORY_PASSWORD


class AppSettings:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.path = self.base_dir / APP_SETTINGS_FILENAME
        self.data = {
            "admin_password": ADMIN_PASSWORD,
            "factory_password": FACTORY_PASSWORD,
            "custom_logo_path": "",
        }
        self.load()

    def load(self) -> None:
        if self.path.exists():
            with self.path.open("r", encoding="utf-8") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                self.data.update({k: loaded[k] for k in self.data if k in loaded})
        self.save()

    def save(self) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    @property
    def admin_password(self) -> str:
        return str(self.data.get("admin_password", ADMIN_PASSWORD))

    @property
    def factory_password(self) -> str:
        return str(self.data.get("factory_password", FACTORY_PASSWORD))

    @property
    def custom_logo_path(self) -> str:
        return str(self.data.get("custom_logo_path", ""))

    def set_passwords(self, admin_password: str, factory_password: str) -> None:
        self.data["admin_password"] = admin_password
        self.data["factory_password"] = factory_password
        self.save()

    def set_custom_logo_path(self, relative_path: str) -> None:
        self.data["custom_logo_path"] = relative_path
        self.save()
