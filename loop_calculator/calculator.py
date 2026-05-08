"""Pure loop-calculation logic extracted from the UI layer.

The functions in this module are intentionally Qt-free so they can be used by
the editor widgets, tests, or command-line tooling without importing any UI
dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Mapping, Sequence

DEFAULT_PANEL_VOLTAGE = 28.0
DEFAULT_MAX_ALARM_LEDS = 10
DEFAULT_MAX_CABLE_LENGTH_M = 1000.0


@dataclass(frozen=True, slots=True)
class CableSpec:
    size: str
    resistance_ohm_per_km: float
    unit: str = "mm²"


DEFAULT_CABLE_TYPES: tuple[CableSpec, ...] = (
    CableSpec(size="1.0", resistance_ohm_per_km=18.1),
    CableSpec(size="1.5", resistance_ohm_per_km=12.1),
    CableSpec(size="2.5", resistance_ohm_per_km=7.41),
    CableSpec(size="4.0", resistance_ohm_per_km=4.61),
)


@dataclass(frozen=True, slots=True)
class LoopDeviceInput:
    product_id: str | None = None
    display_name: str = ""
    category: str = "Other"
    standby_ma: float = 0.5
    alarm_ma: float = 0.0
    led_cost: int = 1
    device_type: str = ""
    lead_dist_m: float = 0.0
    interval_dist_m: float = 0.0
    qty: int = 1


@dataclass(frozen=True, slots=True)
class DiagnosticIssue:
    key: str
    params: Mapping[str, Any] = field(default_factory=dict)

    def render(self, translate: Callable[..., str]) -> str:
        return translate(self.key, **dict(self.params))


@dataclass(frozen=True, slots=True)
class LoopDeviceResult:
    device: LoopDeviceInput
    active_alarm_leds: int
    row_current_ma: float


@dataclass(frozen=True, slots=True)
class LoopCalculationRequest:
    devices: Sequence[LoopDeviceInput | Mapping[str, Any]]
    max_current_ma: float = 400.0
    min_voltage_v: float = 17.0
    cable_resistance_ohm_per_km: float = 12.1
    addr_limit: int = 125
    panel_voltage_v: float = DEFAULT_PANEL_VOLTAGE
    max_alarm_leds: int = DEFAULT_MAX_ALARM_LEDS
    max_cable_length_m: float = DEFAULT_MAX_CABLE_LENGTH_M
    cable_types: Sequence[CableSpec] = DEFAULT_CABLE_TYPES


@dataclass(frozen=True, slots=True)
class LoopCalculationResult:
    total_addresses: int
    total_current_ma: float
    total_distance_m: float
    voltage_drop_v: float
    end_voltage_v: float
    max_install_distance_m: float
    recommended_cable_size: str
    recommended_cable_unit: str
    standby_current_ma: float
    alarm_current_ma: float
    diagnostics: tuple[DiagnosticIssue, ...]
    devices: tuple[LoopDeviceResult, ...]
    addr_limit: int
    max_current_ma: float
    min_voltage_v: float
    cable_resistance_ohm_per_km: float
    panel_voltage_v: float
    max_cable_length_m: float

    def as_display_values(self) -> dict[str, str]:
        # Display an effective limit to avoid mixing theoretical voltage limit
        # with the fixed engineering cap in the same status panel.
        effective_max_len = min(self.max_install_distance_m, self.max_cable_length_m)
        max_len = str(int(effective_max_len)) if float(effective_max_len).is_integer() else f"{effective_max_len:.1f}"
        theoretical_max_len = (
            str(int(self.max_install_distance_m))
            if float(self.max_install_distance_m).is_integer()
            else f"{self.max_install_distance_m:.1f}"
        )
        return {
            "addr": str(self.total_addresses),
            "curr": f"{self.total_current_ma:.1f}",
            "volt": f"{self.end_voltage_v:.3f}",
            "lens": f"{self.total_distance_m:.1f}",
            "max_len": max_len,
            "theo_max_len": theoretical_max_len,
            "rec_cable": self.recommended_cable_size,
        }

    def as_unit_values(self) -> dict[str, str]:
        return {
            "addr": f"/{self.addr_limit}",
            "rec_cable": self.recommended_cable_unit,
        }

    def diagnostic_messages(self, translate: Callable[..., str]) -> list[str]:
        return [issue.render(translate) for issue in self.diagnostics]

    def to_ui_payload(self, translate: Callable[..., str] | None = None) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "values": self.as_display_values(),
            "units": self.as_unit_values(),
            "standby_current_ma": self.standby_current_ma,
            "alarm_current_ma": self.alarm_current_ma,
            "devices": self.devices,
        }
        if translate is not None:
            payload["diagnostics"] = self.diagnostic_messages(translate)
        return payload


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or value == "":
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _coerce_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def coerce_device_input(value: LoopDeviceInput | Mapping[str, Any]) -> LoopDeviceInput:
    if isinstance(value, LoopDeviceInput):
        data = {
            "product_id": value.product_id,
            "display_name": value.display_name,
            "category": value.category,
            "standby_ma": value.standby_ma,
            "alarm_ma": value.alarm_ma,
            "led_cost": value.led_cost,
            "device_type": value.device_type,
            "lead_dist_m": value.lead_dist_m,
            "interval_dist_m": value.interval_dist_m,
            "qty": value.qty,
        }
    else:
        data = dict(value)
    return LoopDeviceInput(
        product_id=_coerce_text(data.get("product_id"), "") or None,
        display_name=_coerce_text(data.get("display_name"), ""),
        category=_coerce_text(data.get("category"), "Other"),
        standby_ma=max(0.0, _coerce_float(data.get("standby", data.get("standby_ma")), 0.5)),
        alarm_ma=max(0.0, _coerce_float(data.get("alarm", data.get("alarm_ma")), 0.0)),
        led_cost=max(0, _coerce_int(data.get("ledCost", data.get("led_cost")), 1)),
        device_type=_coerce_text(data.get("type", data.get("device_type")), ""),
        lead_dist_m=max(0.0, _coerce_float(data.get("lead_dist", data.get("lead_dist_m")), 0.0)),
        interval_dist_m=max(0.0, _coerce_float(data.get("interval_dist", data.get("interval_dist_m")), 0.0)),
        qty=max(0, _coerce_int(data.get("qty"), 1)),
    )


def calculate_loop(request: LoopCalculationRequest) -> LoopCalculationResult:
    devices = [coerce_device_input(device) for device in request.devices]
    total_addresses = sum(device.qty for device in devices)
    standby_current_ma = sum(device.qty * device.standby_ma for device in devices)

    led_reserved = sum(
        device.qty * device.led_cost
        for device in devices
        if device.device_type == "LSM" or device.led_cost > 1
    )
    led_remaining = max(0, request.max_alarm_leds - led_reserved)
    led_used = 0
    processed: list[LoopDeviceResult] = []
    total_current_ma = 0.0

    for device in devices:
        led_cost = device.led_cost or 1
        if device.device_type == "LSM" or device.led_cost > 1 or device.led_cost == 0:
            active_leds = device.qty
        else:
            can_use = led_remaining - led_used
            active_leds = min(device.qty, can_use // led_cost) if can_use > 0 else 0
            led_used += active_leds * led_cost

        row_current_ma = (active_leds * device.alarm_ma) + ((device.qty - active_leds) * device.standby_ma)
        total_current_ma += row_current_ma
        processed.append(LoopDeviceResult(device=device, active_alarm_leds=active_leds, row_current_ma=row_current_ma))

    total_distance_m = 0.0
    voltage_drop_v = 0.0
    flow_ma = total_current_ma
    for result in processed:
        device = result.device
        if device.qty <= 0:
            continue

        lead_r_ohm = (request.cable_resistance_ohm_per_km * (device.lead_dist_m / 1000.0)) * 2.0
        voltage_drop_v += (flow_ma / 1000.0) * lead_r_ohm
        total_distance_m += device.lead_dist_m

        interval_r_ohm = (request.cable_resistance_ohm_per_km * (device.interval_dist_m / 1000.0)) * 2.0
        if device.qty > 1:
            avg_current_ma = result.row_current_ma / device.qty
            flow_after_first_ma = flow_ma - avg_current_ma
            intervals = device.qty - 1
            factor = intervals * flow_after_first_ma - (intervals * (intervals - 1) / 2.0) * avg_current_ma
            voltage_drop_v += (factor / 1000.0) * interval_r_ohm
            total_distance_m += intervals * device.interval_dist_m

        flow_ma -= result.row_current_ma

    end_voltage_v = request.panel_voltage_v - voltage_drop_v
    if voltage_drop_v > 0:
        max_install_distance_m = total_distance_m * ((request.panel_voltage_v - request.min_voltage_v) / voltage_drop_v)
    else:
        max_install_distance_m = request.max_cable_length_m

    recommended_cable_size = "N/A"
    recommended_cable_unit = ""
    if request.cable_resistance_ohm_per_km > 0:
        for cable in request.cable_types:
            test_drop_v = (cable.resistance_ohm_per_km / request.cable_resistance_ohm_per_km) * voltage_drop_v
            if (request.panel_voltage_v - test_drop_v) >= request.min_voltage_v:
                recommended_cable_size = cable.size
                recommended_cable_unit = cable.unit
                break

    diagnostics: list[DiagnosticIssue] = []
    if total_addresses > request.addr_limit:
        diagnostics.append(DiagnosticIssue("diag_address_over", {"value": total_addresses, "limit": request.addr_limit}))
    if total_current_ma > request.max_current_ma:
        diagnostics.append(DiagnosticIssue("diag_current_over", {"value": total_current_ma}))
    if end_voltage_v < request.min_voltage_v:
        diagnostics.append(DiagnosticIssue("diag_voltage_low", {"value": end_voltage_v}))
    if total_distance_m > request.max_cable_length_m:
        diagnostics.append(
            DiagnosticIssue("diag_length_over", {"value": total_distance_m, "limit": request.max_cable_length_m})
        )

    return LoopCalculationResult(
        total_addresses=total_addresses,
        total_current_ma=total_current_ma,
        total_distance_m=total_distance_m,
        voltage_drop_v=voltage_drop_v,
        end_voltage_v=end_voltage_v,
        max_install_distance_m=max_install_distance_m,
        recommended_cable_size=recommended_cable_size,
        recommended_cable_unit=recommended_cable_unit,
        standby_current_ma=standby_current_ma,
        alarm_current_ma=total_current_ma,
        diagnostics=tuple(diagnostics),
        devices=tuple(processed),
        addr_limit=request.addr_limit,
        max_current_ma=request.max_current_ma,
        min_voltage_v=request.min_voltage_v,
        cable_resistance_ohm_per_km=request.cable_resistance_ohm_per_km,
        panel_voltage_v=request.panel_voltage_v,
        max_cable_length_m=request.max_cable_length_m,
    )


def calculate_loop_from_rows(
    rows: Sequence[LoopDeviceInput | Mapping[str, Any]],
    *,
    max_current_ma: float = 400.0,
    min_voltage_v: float = 17.0,
    cable_resistance_ohm_per_km: float = 12.1,
    addr_limit: int = 125,
    panel_voltage_v: float = DEFAULT_PANEL_VOLTAGE,
    max_alarm_leds: int = DEFAULT_MAX_ALARM_LEDS,
    max_cable_length_m: float = DEFAULT_MAX_CABLE_LENGTH_M,
    cable_types: Sequence[CableSpec] = DEFAULT_CABLE_TYPES,
) -> LoopCalculationResult:
    request = LoopCalculationRequest(
        devices=rows,
        max_current_ma=max_current_ma,
        min_voltage_v=min_voltage_v,
        cable_resistance_ohm_per_km=cable_resistance_ohm_per_km,
        addr_limit=addr_limit,
        panel_voltage_v=panel_voltage_v,
        max_alarm_leds=max_alarm_leds,
        max_cable_length_m=max_cable_length_m,
        cable_types=cable_types,
    )
    return calculate_loop(request)


def render_diagnostic_messages(
    issues: Sequence[DiagnosticIssue],
    translate: Callable[..., str],
) -> list[str]:
    return [issue.render(translate) for issue in issues]


__all__ = [
    "CableSpec",
    "DEFAULT_CABLE_TYPES",
    "DEFAULT_MAX_ALARM_LEDS",
    "DEFAULT_MAX_CABLE_LENGTH_M",
    "DEFAULT_PANEL_VOLTAGE",
    "DiagnosticIssue",
    "LoopCalculationRequest",
    "LoopCalculationResult",
    "LoopDeviceInput",
    "LoopDeviceResult",
    "calculate_loop",
    "calculate_loop_from_rows",
    "coerce_device_input",
    "render_diagnostic_messages",
]
