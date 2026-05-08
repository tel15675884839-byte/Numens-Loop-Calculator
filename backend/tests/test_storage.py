from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from backend.app.storage import SQLiteStore


def _write_seed(path: Path, *, product_name: str = "Smoke/Heat Detector", alarm: float = 2) -> None:
    path.write_text(
        json.dumps(
            {
                "categories": ["Detector"],
                "products": [
                    {
                        "id": "product-0019",
                        "factory_name": "SNA-360-C2",
                        "customer_name": "SNA-360-C2",
                        "category": "Detector",
                        "standby": 0.46,
                        "alarm": alarm,
                        "ledCost": 1,
                        "type": "Detector",
                        "product_name": product_name,
                        "built_in": True,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_initialize_removes_retired_builtin_600_detectors_from_existing_database(tmp_path: Path) -> None:
    db_path = tmp_path / "loop_calculator.sqlite3"
    seed_path = tmp_path / "products_db.json"
    _write_seed(seed_path)

    store = SQLiteStore(db_path, seed_path)
    store.initialize()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO products (
                id, category, factory_name, customer_name, product_name,
                standby_ma, alarm_ma, led_cost, device_type, built_in
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("product-0013", "Detector", "600-001", "600-001", "Smoke/Heat Detector", 0.26, 2, 1, "Detector", 1),
        )
        conn.execute(
            """
            INSERT INTO products (
                id, category, factory_name, customer_name, product_name,
                standby_ma, alarm_ma, led_cost, device_type, built_in
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("custom-600", "Detector", "600-CUSTOM", "600-CUSTOM", "Custom Detector", 0.5, 2, 1, "Detector", 0),
        )

    store.initialize()

    product_ids = {product["id"] for product in store.list_products(deleted="all")}
    assert "product-0013" not in product_ids
    assert "custom-600" in product_ids


def test_initialize_syncs_seeded_builtin_products_without_overwriting_custom_products(tmp_path: Path) -> None:
    db_path = tmp_path / "loop_calculator.sqlite3"
    seed_path = tmp_path / "products_db.json"
    _write_seed(seed_path, product_name="Original Detector", alarm=2)

    store = SQLiteStore(db_path, seed_path)
    store.initialize()
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO products (
                id, category, factory_name, customer_name, product_name,
                standby_ma, alarm_ma, led_cost, device_type, built_in
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("custom-product", "Detector", "CUSTOM", "CUSTOM", "Custom Detector", 1.1, 3.3, 1, "Detector", 0),
        )

    _write_seed(seed_path, product_name="Updated Detector", alarm=5)
    store.initialize()

    products = {product["id"]: product for product in store.list_products(deleted="all")}
    assert products["product-0019"]["product_name"] == "Updated Detector"
    assert products["product-0019"]["alarm_ma"] == 5
    assert products["custom-product"]["product_name"] == "Custom Detector"
    assert products["custom-product"]["alarm_ma"] == 3.3
