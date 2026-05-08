from __future__ import annotations

from loop_calculator.calculator import (
    LoopCalculationRequest,
    LoopDeviceInput,
    calculate_loop,
    coerce_device_input,
    render_diagnostic_messages,
)


def test_calculate_loop_empty_devices_uses_safe_defaults() -> None:
    result = calculate_loop(LoopCalculationRequest(devices=[]))
    assert result.total_addresses == 0
    assert result.total_current_ma == 0.0
    assert result.total_distance_m == 0.0
    assert result.end_voltage_v == result.panel_voltage_v
    assert result.diagnostics == ()


def test_led_allocation_respects_max_alarm_leds() -> None:
    request = LoopCalculationRequest(
        devices=[
            {"display_name": "A", "qty": 3, "standby": 1.0, "alarm": 10.0, "ledCost": 1},
            {"display_name": "B", "qty": 1, "standby": 1.0, "alarm": 20.0, "ledCost": 1},
        ],
        max_alarm_leds=2,
    )
    result = calculate_loop(request)

    assert result.devices[0].active_alarm_leds == 2
    assert result.devices[1].active_alarm_leds == 0
    assert result.total_current_ma == 22.0


def test_calculate_loop_reports_address_and_current_over_limit() -> None:
    request = LoopCalculationRequest(
        devices=[{"display_name": "Big", "qty": 5, "standby": 2.0, "alarm": 20.0, "ledCost": 1}],
        addr_limit=4,
        max_current_ma=50.0,
    )
    result = calculate_loop(request)
    keys = {issue.key for issue in result.diagnostics}

    assert "diag_address_over" in keys
    assert "diag_current_over" in keys


def test_calculate_loop_reports_voltage_and_distance_diagnostics() -> None:
    request = LoopCalculationRequest(
        devices=[
            {
                "display_name": "Far High Load",
                "qty": 1,
                "standby": 0.0,
                "alarm": 10000.0,
                "ledCost": 1,
                "lead_dist": 1001.0,
                "interval_dist": 0.0,
            }
        ],
        max_current_ma=20000.0,
    )

    result = calculate_loop(request)
    keys = {issue.key for issue in result.diagnostics}
    length_issue = next(issue for issue in result.diagnostics if issue.key == "diag_length_over")

    assert "diag_voltage_low" in keys
    assert "diag_length_over" in keys
    assert "diag_current_over" not in keys
    assert length_issue.params["limit"] == request.max_cable_length_m


def test_calculate_loop_selects_recommended_cable_size_and_scaled_max_len() -> None:
    request = LoopCalculationRequest(
        devices=[
            {
                "display_name": "Cable Check",
                "qty": 1,
                "standby": 0.0,
                "alarm": 1000.0,
                "ledCost": 1,
                "lead_dist": 400.0,
                "interval_dist": 0.0,
            }
        ],
        max_current_ma=2000.0,
    )

    result = calculate_loop(request)
    display_values = result.as_display_values()

    assert result.recommended_cable_size == "1.5"
    assert display_values["rec_cable"] == "1.5"
    assert display_values["max_len"] == "454.5"
    assert display_values["theo_max_len"] == "454.5"


def test_as_display_values_uses_integer_max_len_when_voltage_drop_is_zero() -> None:
    result = calculate_loop(LoopCalculationRequest(devices=[]))

    assert result.as_display_values()["max_len"] == "1000"


def test_as_display_values_caps_effective_max_len_by_system_limit() -> None:
    request = LoopCalculationRequest(
        devices=[
            {
                "display_name": "Long Reach",
                "qty": 1,
                "standby": 0.0,
                "alarm": 100.0,
                "ledCost": 1,
                "lead_dist": 400.0,
                "interval_dist": 0.0,
            }
        ],
    )
    result = calculate_loop(request)
    display_values = result.as_display_values()

    assert result.max_install_distance_m > result.max_cable_length_m
    assert display_values["max_len"] == "1000"
    assert display_values["theo_max_len"] == f"{result.max_install_distance_m:.1f}"


def test_to_ui_payload_renders_diagnostics_with_translate_function() -> None:
    request = LoopCalculationRequest(
        devices=[
            {
                "display_name": "Payload Check",
                "qty": 1,
                "standby": 0.0,
                "alarm": 10000.0,
                "ledCost": 1,
                "lead_dist": 1001.0,
                "interval_dist": 0.0,
            }
        ],
        max_current_ma=20000.0,
    )
    result = calculate_loop(request)

    def translate(key: str, **kwargs) -> str:
        return f"{key}:{kwargs['value']}"

    payload = result.to_ui_payload(translate)

    assert payload["values"] == result.as_display_values()
    assert payload["units"]["addr"] == "/125"
    assert payload["diagnostics"] == render_diagnostic_messages(result.diagnostics, translate)


def test_coerce_device_input_handles_invalid_values() -> None:
    device = coerce_device_input(
        {
            "product_id": "  ",
            "display_name": "  Demo  ",
            "standby": "bad",
            "alarm": None,
            "ledCost": "-2",
            "qty": "not-a-number",
        }
    )

    assert device.product_id is None
    assert device.display_name == "Demo"
    assert device.standby_ma == 0.5
    assert device.alarm_ma == 0.0
    assert device.led_cost == 0
    assert device.qty == 1


def test_loop_device_input_instances_are_sanitized_before_calculation() -> None:
    invalid_device = LoopDeviceInput(
        display_name="Invalid",
        qty=-10,
        standby_ma=-0.5,
        alarm_ma=-2.0,
        lead_dist_m=-100.0,
        interval_dist_m=-50.0,
    )
    request = LoopCalculationRequest(devices=[invalid_device])

    result = calculate_loop(request)

    assert result.total_addresses == 0
    assert result.standby_current_ma == 0.0
    assert result.total_current_ma == 0.0
    assert result.total_distance_m == 0.0
    assert result.end_voltage_v == result.panel_voltage_v
