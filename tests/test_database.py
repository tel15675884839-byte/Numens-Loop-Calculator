from __future__ import annotations

import json

from loop_calculator.database import ProductDatabase


def _write_products_db(base_dir, payload: dict) -> None:
    path = base_dir / "products_db.json"
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def test_product_database_normalizes_module_aliases(tmp_path) -> None:
    _write_products_db(
        tmp_path,
        {
            "categories": ["Input Module"],
            "products": [
                {
                    "id": "product-0001",
                    "category": "Input Module",
                    "type": "Output Module",
                    "factory_name": "M100",
                    "customer_name": "M100",
                    "standby": 0.5,
                    "alarm": 2.0,
                    "ledCost": 1,
                }
            ],
        },
    )
    db = ProductDatabase(tmp_path)
    product = db.get_product("product-0001")

    assert product is not None
    assert product["category"] == "I/O Module"
    assert product["type"] == "I/O Module"
    assert "I/O Module" in db.categories()


def test_product_database_next_product_id_increments() -> None:
    class Dummy:
        pass

    dummy = Dummy()
    dummy.products = [{"id": "product-0002"}, {"id": "product-0010"}, {"id": "legacy-1"}]

    assert ProductDatabase.next_product_id(dummy) == "product-0011"


def test_merged_options_compact_display_name(tmp_path) -> None:
    _write_products_db(
        tmp_path,
        {
            "categories": ["Detector"],
            "products": [
                {
                    "id": "product-0001",
                    "category": "Detector",
                    "type": "Detector",
                    "factory_name": "ABC100",
                    "customer_name": "ABC100",
                    "standby": 0.5,
                    "alarm": 2.0,
                    "ledCost": 1,
                },
                {
                    "id": "product-0002",
                    "category": "Detector",
                    "type": "Detector",
                    "factory_name": "ABC101",
                    "customer_name": "ABC101",
                    "standby": 0.5,
                    "alarm": 2.0,
                    "ledCost": 1,
                },
            ],
        },
    )

    db = ProductDatabase(tmp_path)
    merged = db.merged_options_by_category("Detector")

    assert len(merged) == 1
    assert merged[0]["display_name"] == "ABC100/101"


def test_product_database_migrates_legacy_products(tmp_path) -> None:
    legacy_payload = [
        {
            "name": "Legacy Smoke Detector",
            "type": "Detector",
            "standby": "0.75",
            "alarm": "3.25",
            "ledCost": "2",
        },
        {
            "type": "Input Module",
            "standby": 0.6,
            "alarm": 1.5,
            "ledCost": 3,
        },
    ]
    (tmp_path / "devices_new.json").write_text(json.dumps(legacy_payload), encoding="utf-8")

    db = ProductDatabase(tmp_path)

    first = db.get_product("product-0001")
    second = db.get_product("product-0002")

    assert first is not None
    assert first["factory_name"] == "Legacy Smoke Detector"
    assert first["customer_name"] == "Legacy Smoke Detector"
    assert first["standby"] == 0.75
    assert first["alarm"] == 3.25
    assert first["ledCost"] == 2
    assert first["built_in"] is True
    assert second is not None
    assert second["factory_name"] == "Product 2"
    assert second["category"] == "I/O Module"
    assert second["type"] == "I/O Module"
    assert second["built_in"] is True
    assert (tmp_path / "products_db.json").exists()


def test_resolve_row_state_prefers_product_id_and_overlays_state(tmp_path) -> None:
    _write_products_db(
        tmp_path,
        {
            "categories": ["Detector"],
            "products": [
                {
                    "id": "product-0001",
                    "category": "Detector",
                    "type": "Detector",
                    "factory_name": "ABC100",
                    "customer_name": "ABC100",
                    "product_name": "ABC100",
                    "standby": 0.5,
                    "alarm": 2.0,
                    "ledCost": 1,
                }
            ],
        },
    )

    db = ProductDatabase(tmp_path)

    resolved = db.resolve_row_state({"product_id": "product-0001", "qty": 3, "customer_name": "Override"})

    assert resolved["product_id"] == "product-0001"
    assert resolved["display_name"] == "ABC100"
    assert resolved["standby"] == 0.5
    assert resolved["alarm"] == 2.0
    assert resolved["qty"] == 3
    assert resolved["customer_name"] == "Override"


def test_resolve_row_state_uses_legacy_merge_fallback(monkeypatch, tmp_path) -> None:
    _write_products_db(
        tmp_path,
        {
            "categories": ["Detector"],
            "products": [
                {
                    "id": "member-1",
                    "category": "Detector",
                    "type": "Detector",
                    "factory_name": "Legacy 100",
                    "customer_name": "Legacy 100",
                    "product_name": "Legacy 100",
                    "standby": 0.4,
                    "alarm": 1.2,
                    "ledCost": 1,
                },
                {
                    "id": "member-2",
                    "category": "Detector",
                    "type": "Detector",
                    "factory_name": "Legacy 101",
                    "customer_name": "Legacy 101",
                    "product_name": "Legacy 101",
                    "standby": 0.4,
                    "alarm": 1.2,
                    "ledCost": 1,
                },
            ],
        },
    )

    db = ProductDatabase(tmp_path)
    merged_option = {
        "member_product_ids": ["member-1", "member-2"],
        "display_name": "Legacy 100/101",
        "category": "Detector",
        "type": "Detector",
        "standby": 0.4,
        "alarm": 1.2,
        "ledCost": 1,
    }
    monkeypatch.setattr(db, "get_product_option", lambda product_id: {"product_id": product_id, "display_name": "Legacy 100", "category": "Detector"} if product_id == "member-1" else None)
    monkeypatch.setattr(db, "get_merged_option", lambda merge_key: None)
    monkeypatch.setattr(db, "get_merged_option_for_product", lambda product_id: merged_option if product_id == "legacy-0001" else None)

    resolved = db.resolve_row_state({"product_id": "legacy-0001", "qty": 2, "merge_key": "stale-key"})

    assert resolved["product_id"] == "legacy-0001"
    assert resolved["display_name"] == "Legacy 100"
    assert resolved["qty"] == 2
    assert "merge_key" not in resolved
    assert "member_product_ids" not in resolved


def test_restore_default_products_keeps_custom_products_and_categories(tmp_path) -> None:
    _write_products_db(
        tmp_path,
        {
            "categories": ["Custom Category"],
            "products": [
                {
                    "id": "product-0001",
                    "category": "Detector",
                    "type": "Detector",
                    "factory_name": "Default Detector",
                    "customer_name": "Default Detector",
                    "product_name": "Default Detector",
                    "standby": 0.5,
                    "alarm": 2.0,
                    "ledCost": 1,
                    "built_in": True,
                },
                {
                    "id": "product-9001",
                    "category": "Custom Category",
                    "type": "Custom Category",
                    "factory_name": "Custom Sensor",
                    "customer_name": "Custom Sensor",
                    "product_name": "Custom Sensor",
                    "standby": 1.1,
                    "alarm": 2.2,
                    "ledCost": 4,
                    "built_in": False,
                },
            ],
        },
    )

    db = ProductDatabase(tmp_path)
    db.products[0]["factory_name"] = "Tampered Default"
    db.products[0]["product_name"] = "Tampered Default"
    db.save()

    db.restore_default_products()

    restored_default = db.get_product("product-0001")
    custom = db.get_product("product-9001")

    assert restored_default is not None
    assert restored_default["factory_name"] == "Default Detector"
    assert restored_default["product_name"] == "Default Detector"
    assert custom is not None
    assert custom["factory_name"] == "Custom Sensor"
    assert custom["built_in"] is False
    assert "Custom Category" in db.categories()
