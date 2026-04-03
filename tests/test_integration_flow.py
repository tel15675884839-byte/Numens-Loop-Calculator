from __future__ import annotations

import json

import pytest

from loop_calculator.database import ProductDatabase
from loop_calculator.device_list_model import DeviceListModel
from loop_calculator.main_window import CIEMainWindow


def _write_json(path, payload) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_integration_legacy_migration_to_model_calculation(tmp_path) -> None:
    legacy_products = [
        {
            "name": "Legacy-A",
            "type": "Detector",
            "standby": 1.0,
            "alarm": 3.0,
            "ledCost": 1,
        }
    ]
    _write_json(tmp_path / "devices_new.json", legacy_products)

    db = ProductDatabase(tmp_path)
    row = db.resolve_row_state(
        {
            "product_id": "product-0001",
            "qty": 2,
            "lead_dist": 20.0,
            "interval_dist": 5.0,
        }
    )

    model = DeviceListModel.from_payload(
        {
            "rows": [row],
            "addr_limit": 10,
            "max_current_ma": 100.0,
            "min_voltage_v": 17.0,
            "cable_resistance_ohm_per_km": 12.1,
        }
    )
    result = model.calculate()

    assert result.total_addresses == 2
    assert result.total_current_ma == pytest.approx(6.0)
    assert result.total_distance_m == pytest.approx(25.0)
    assert result.diagnostics == ()


def test_integration_update_customer_name_persists_after_reload(tmp_path) -> None:
    _write_json(
        tmp_path / "products_db.json",
        {
            "categories": ["Detector"],
            "products": [
                {
                    "id": "product-0001",
                    "category": "Detector",
                    "type": "Detector",
                    "factory_name": "F-100",
                    "customer_name": "Old Name",
                    "product_name": "",
                    "standby": 0.5,
                    "alarm": 2.0,
                    "ledCost": 1,
                }
            ],
        },
    )

    db = ProductDatabase(tmp_path)
    updated = db.update_customer_name("product-0001", "New Customer Name")
    reloaded = ProductDatabase(tmp_path)

    assert updated is not None
    assert updated["customer_name"] == "New Customer Name"
    assert reloaded.get_product("product-0001")["customer_name"] == "New Customer Name"
    assert reloaded.get_product_option("product-0001")["display_name"] == "New Customer Name"


def test_integration_restore_defaults_with_corrupted_backup_is_fault_tolerant(tmp_path) -> None:
    _write_json(
        tmp_path / "products_db.json",
        {
            "categories": ["Detector", "Custom"],
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
                    "category": "Custom",
                    "type": "Custom",
                    "factory_name": "Custom Device",
                    "customer_name": "Custom Device",
                    "product_name": "Custom Device",
                    "standby": 0.8,
                    "alarm": 1.1,
                    "ledCost": 2,
                    "built_in": False,
                },
            ],
        },
    )

    db = ProductDatabase(tmp_path)
    (tmp_path / "products_db.defaults.json").write_text("{invalid-json", encoding="utf-8")
    db.products[0]["factory_name"] = "Tampered BuiltIn"
    db.save()

    db.restore_default_products()
    reloaded = ProductDatabase(tmp_path)

    # Current behavior: when backup is corrupted, restore rebuilds backup from
    # the current in-memory products first, so built-in tampering is preserved.
    assert reloaded.get_product("product-0001")["factory_name"] == "Tampered BuiltIn"
    assert reloaded.get_product("product-9001")["factory_name"] == "Custom Device"


def test_integration_database_rows_can_round_trip_through_model_payload(tmp_path) -> None:
    _write_json(
        tmp_path / "products_db.json",
        {
            "categories": ["Detector"],
            "products": [
                {
                    "id": "product-0001",
                    "category": "Detector",
                    "type": "Detector",
                    "factory_name": "D100",
                    "customer_name": "D100",
                    "product_name": "D100",
                    "standby": 0.7,
                    "alarm": 2.5,
                    "ledCost": 1,
                }
            ],
        },
    )
    db = ProductDatabase(tmp_path)
    row = db.resolve_row_state({"product_id": "product-0001", "qty": 3, "lead_dist": 10.0, "interval_dist": 2.0})

    model = DeviceListModel()
    model.import_state({"rows": [row], "addr_limit": 5, "max_current_ma": 100.0})
    exported = model.export_state()
    result = model.calculate()

    assert exported["rows"][0]["product_id"] == "product-0001"
    assert exported["rows"][0]["qty"] == 3
    assert result.total_addresses == 3
    assert result.total_current_ma == pytest.approx(7.5)


def test_integration_loop_device_limit_syncs_across_loops() -> None:
    class FakeCombo:
        def __init__(self, index: int) -> None:
            self._index = index

        def currentIndex(self) -> int:
            return self._index

        def setCurrentIndex(self, index: int) -> None:
            self._index = index

    class FakeLoop:
        def __init__(self, index: int) -> None:
            self.combo_addr_limit = FakeCombo(index)

    source_loop = FakeLoop(1)
    target_loop_a = FakeLoop(0)
    target_loop_b = FakeLoop(0)

    window = CIEMainWindow.__new__(CIEMainWindow)
    window._syncing_loop_device_limit = False
    window._iter_loops = lambda: [source_loop, target_loop_a, target_loop_b]

    CIEMainWindow._sync_loop_addr_limit(window, source_loop, source_loop.combo_addr_limit.currentIndex())

    assert source_loop.combo_addr_limit.currentIndex() == 1
    assert target_loop_a.combo_addr_limit.currentIndex() == 1
    assert target_loop_b.combo_addr_limit.currentIndex() == 1


def test_integration_min_voltage_syncs_across_loops() -> None:
    class FakeLineEdit:
        def __init__(self, value: str) -> None:
            self._value = value

        def text(self) -> str:
            return self._value

        def setText(self, value: str) -> None:
            self._value = value

    class FakeLoop:
        def __init__(self, value: str) -> None:
            self.edit_min_voltage = FakeLineEdit(value)

    source_loop = FakeLoop("18.5")
    target_loop_a = FakeLoop("17")
    target_loop_b = FakeLoop("19")

    window = CIEMainWindow.__new__(CIEMainWindow)
    window._syncing_loop_min_voltage = False
    window._iter_loops = lambda: [source_loop, target_loop_a, target_loop_b]

    CIEMainWindow._sync_loop_min_voltage(window, source_loop, source_loop.edit_min_voltage.text())

    assert source_loop.edit_min_voltage.text() == "18.5"
    assert target_loop_a.edit_min_voltage.text() == "18.5"
    assert target_loop_b.edit_min_voltage.text() == "18.5"
