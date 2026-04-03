"""Shared constants for the loop calculator package."""

from __future__ import annotations

ADDRESS_LIMIT = 125
MAX_ALARM_LEDS = 10
MAX_CABLE_LENGTH = 1000

PRODUCT_DB_FILENAME = "products_db.json"
PRODUCT_DB_BACKUP_FILENAME = "products_db.defaults.json"
APP_SETTINGS_FILENAME = "app_settings.json"
ADMIN_PASSWORD = "1"
FACTORY_PASSWORD = "8"

MODULE_CATEGORY_ALIASES = {"Input Module", "Output Module", "Input/Output Module"}
MODULE_CATEGORY_NAME = "I/O Module"

CABLE_TYPES = [
    {"size": "1.0", "resistance": 18.1, "label": "1.0 mm²"},
    {"size": "1.5", "resistance": 12.1, "label": "1.5 mm²"},
    {"size": "2.5", "resistance": 7.41, "label": "2.5 mm²"},
    {"size": "4.0", "resistance": 4.61, "label": "4.0 mm²"},
]

PANEL_SPECS = {
    "Standard": {"quiescent": 200, "aux_limit": 200, "max_loops": 6},
}
