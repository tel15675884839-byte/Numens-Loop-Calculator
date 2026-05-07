"""Language and translation helpers for the loop calculator."""

from __future__ import annotations

import json
import os
from typing import Any

LANGUAGE_OPTIONS: dict[str, str] = {
    "en": "English",
}

_TRANSLATIONS: dict[str, dict[str, str]] = {}


def _load_translations() -> None:
    """Load all available translation JSON files from the translations directory."""
    base_path = os.path.dirname(__file__)
    trans_dir = os.path.join(base_path, "translations")
    if not os.path.exists(trans_dir):
        return
    for lang_code in LANGUAGE_OPTIONS:
        file_path = os.path.join(trans_dir, f"{lang_code}.json")
        if not os.path.exists(file_path):
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                _TRANSLATIONS[lang_code] = json.load(file)
        except Exception as exc:
            print(f"Error loading translation for {lang_code}: {exc}")


_TRANSLATIONS.clear()
_load_translations()


def tr_text(lang: str, key: str, **kwargs: Any) -> str:
    """Translate by key, falling back to English and finally to the key itself."""
    text = _TRANSLATIONS.get(lang, {}).get(key)
    if text is None and lang != "en":
        text = _TRANSLATIONS.get("en", {}).get(key)
    if text is None:
        text = key
    return text.format(**kwargs) if kwargs else text


def t(lang: str, key: str, **kwargs: Any) -> str:
    """Convenience alias for tr_text."""
    return tr_text(lang, key, **kwargs)


def get_theme_name(lang: str, theme_id: str) -> str:
    """Get the translated name of a theme."""
    return t(lang, f"theme_{theme_id}")
