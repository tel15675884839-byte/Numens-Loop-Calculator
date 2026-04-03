from __future__ import annotations

import pytest

from loop_calculator.calculator import LoopDeviceInput
from loop_calculator.device_list_model import DeviceListModel
from loop_calculator.device_list_state import DeviceListRowState, DeviceListState


def test_device_row_state_from_mapping_normalizes_known_fields_and_keeps_meta() -> None:
    row = DeviceListRowState.from_mapping(
        {
            "product_id": "product-1",
            "display_name": " Demo ",
            "category": "",
            "standby": "1.25",
            "alarm": "2.5",
            "ledCost": "-3",
            "type": "Sensor",
            "lead_dist": "4.5",
            "interval_dist_m": "6.75",
            "qty": "0",
            "custom_field": "kept",
        }
    )

    assert row.product_id == "product-1"
    assert row.display_name == " Demo "
    assert row.category == "Other"
    assert row.standby == pytest.approx(1.25)
    assert row.alarm == pytest.approx(2.5)
    assert row.led_cost == 0
    assert row.device_type == "Sensor"
    assert row.lead_dist_m == pytest.approx(4.5)
    assert row.interval_dist_m == pytest.approx(6.75)
    assert row.qty == 1
    assert row.meta == {"custom_field": "kept"}
    assert row.to_mapping()["custom_field"] == "kept"


def test_device_row_state_from_payload_returns_copy_and_alias_properties_work() -> None:
    original = DeviceListRowState(
        product_id="product-2",
        display_name="Alpha",
        led_cost=2,
        device_type="Detector",
        lead_dist_m=1.0,
        interval_dist_m=2.0,
    )

    copied = DeviceListRowState.from_payload(original)
    copied.ledCost = "5"
    copied.type = "Changed"
    copied.lead_dist = "7.25"
    copied.interval_dist = "8"

    assert copied is not original
    assert original.led_cost == 2
    assert original.device_type == "Detector"
    assert original.lead_dist_m == pytest.approx(1.0)
    assert original.interval_dist_m == pytest.approx(2.0)
    assert copied.led_cost == 5
    assert copied.device_type == "Changed"
    assert copied.lead_dist_m == pytest.approx(7.25)
    assert copied.interval_dist_m == pytest.approx(8.0)


def test_device_list_state_insert_update_remove_and_selection() -> None:
    state = DeviceListState()
    state.add_row({"display_name": "A", "qty": 2})
    state.add_row({"display_name": "B", "qty": 3})
    state.add_row({"display_name": "C", "qty": 4}, index=1)

    assert [row.display_name for row in state.rows] == ["A", "C", "B"]
    assert state.total_quantity() == 9

    updated = state.update_row(1, qty=5)
    assert updated.qty == 5
    assert state.get_row(1).qty == 5

    state.set_selection([0, 1, -1, 99])
    assert state.selected_rows == {0, 1}

    removed = state.remove_rows([1, -2, 8])
    assert [row.display_name for row in removed] == ["C"]
    assert [row.display_name for row in state.rows] == ["A", "B"]
    assert state.row_count() == 2


def test_device_list_state_round_trips_to_loop_devices() -> None:
    state = DeviceListState.from_loop_devices(
        [
            LoopDeviceInput(display_name="Zone 1", standby_ma=1.5, alarm_ma=4.0, qty=2),
            {"display_name": "Zone 2", "qty": 1, "standby": 0.75, "alarm": 1.25},
        ],
        panel_type="Custom",
    )

    loop_devices = state.to_loop_devices()

    assert state.panel_type == "Custom"
    assert len(loop_devices) == 2
    assert loop_devices[0].display_name == "Zone 1"
    assert loop_devices[0].qty == 2
    assert loop_devices[1].standby_ma == pytest.approx(0.75)
    assert loop_devices[1].alarm_ma == pytest.approx(1.25)
    assert state.to_mapping()["selected_rows"] == []


def test_device_list_model_round_trip_and_calculate() -> None:
    model = DeviceListModel.from_payload(
        {
            "panel_type": "Fire",
            "addr_limit_index": "2",
            "cable_index": "3",
            "min_voltage": "18.5",
            "aux_current": "1.2",
            "rows": [
                {
                    "display_name": "Zone 1",
                    "qty": "2",
                    "standby": "1.0",
                    "alarm": "5.0",
                    "ledCost": "1",
                    "lead_dist": "10",
                    "interval_dist": "5",
                }
            ],
            "selected_rows": [1, "3", -1, "x"],
            "max_current_ma": "50.5",
            "min_voltage_v": "18.2",
            "cable_resistance_ohm_per_km": "11.0",
            "addr_limit": "3",
            "cable_types": [{"size": "2.5", "resistance": "7.41", "unit": "mm2"}],
        }
    )

    payload = model.to_payload()
    result = model.calculate()

    assert model.state.panel_type == "Fire"
    assert model.state.selected_rows == {1, 3}
    assert model.calc.max_current_ma == pytest.approx(50.5)
    assert model.calc.min_voltage_v == pytest.approx(18.2)
    assert model.calc.cable_resistance_ohm_per_km == pytest.approx(11.0)
    assert model.calc.addr_limit == 3
    assert payload["cable_types"][0].size == "2.5"
    assert payload["cable_types"][0].resistance_ohm_per_km == pytest.approx(7.41)
    assert result.total_addresses == 2
    assert result.total_current_ma == pytest.approx(10.0)
    assert model.last_result is result

