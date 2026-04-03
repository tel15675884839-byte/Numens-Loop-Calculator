from __future__ import annotations

"""A small controller-style model for the Device List refactor.

The current UI is still table-widget based, but this model gives us a stable
data layer that can later back a QAbstractTableModel or be used directly by
tests and import/export code.
"""

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .calculator import CableSpec, LoopCalculationResult, calculate_loop_from_rows
from .device_list_state import DeviceListRowState, DeviceListState


def _coerce_cable_types(values: Sequence[Any] | None) -> list[CableSpec] | None:
    if values is None:
        return None
    items: list[CableSpec] = []
    for value in values:
        if isinstance(value, CableSpec):
            items.append(value)
            continue
        if isinstance(value, Mapping):
            size = str(value.get("size", "") or "")
            resistance = float(value.get("resistance", 0.0) or 0.0)
            unit = str(value.get("unit", "mm²") or "mm²")
            items.append(CableSpec(size=size, resistance_ohm_per_km=resistance, unit=unit))
    return items


@dataclass(slots=True)
class DeviceListCalculationContext:
    """Parameters needed to run the loop calculation."""

    max_current_ma: float = 400.0
    min_voltage_v: float = 17.0
    cable_resistance_ohm_per_km: float = 12.1
    addr_limit: int = 125
    cable_types: Sequence[Any] | None = None


@dataclass(slots=True)
class DeviceListModel:
    """Qt-free model facade for the Device List.

    It stores the editable list state and exposes a few focused operations that
    the current widget UI or a future table model can call.
    """

    state: DeviceListState = field(default_factory=DeviceListState)
    calc: DeviceListCalculationContext = field(default_factory=DeviceListCalculationContext)
    last_result: LoopCalculationResult | None = None

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | None) -> "DeviceListModel":
        state = DeviceListState.from_mapping(payload)
        calc = DeviceListCalculationContext(
            max_current_ma=float(payload.get("max_current_ma", 400.0)) if payload else 400.0,
            min_voltage_v=float(payload.get("min_voltage_v", state.min_voltage)) if payload else state.min_voltage,
            cable_resistance_ohm_per_km=float(payload.get("cable_resistance_ohm_per_km", 12.1)) if payload else 12.1,
            addr_limit=int(payload.get("addr_limit", 125)) if payload else 125,
            cable_types=_coerce_cable_types(payload.get("cable_types")) if payload else None,
        )
        return cls(state=state, calc=calc)

    def to_payload(self) -> dict[str, Any]:
        payload = self.state.to_mapping()
        payload.update(
            {
                "max_current_ma": self.calc.max_current_ma,
                "min_voltage_v": self.calc.min_voltage_v,
                "cable_resistance_ohm_per_km": self.calc.cable_resistance_ohm_per_km,
                "addr_limit": self.calc.addr_limit,
                "cable_types": list(self.calc.cable_types or []),
            }
        )
        return payload

    def update_calculation_context(
        self,
        *,
        max_current_ma: float | None = None,
        min_voltage_v: float | None = None,
        cable_resistance_ohm_per_km: float | None = None,
        addr_limit: int | None = None,
        cable_types: Sequence[Any] | None = None,
    ) -> None:
        if max_current_ma is not None:
            self.calc.max_current_ma = float(max_current_ma)
        if min_voltage_v is not None:
            self.calc.min_voltage_v = float(min_voltage_v)
        if cable_resistance_ohm_per_km is not None:
            self.calc.cable_resistance_ohm_per_km = float(cable_resistance_ohm_per_km)
        if addr_limit is not None:
            self.calc.addr_limit = int(addr_limit)
        if cable_types is not None:
            self.calc.cable_types = _coerce_cable_types(cable_types)

    def set_devices(self, devices: Sequence[DeviceListRowState | Mapping[str, Any] | Any]) -> None:
        self.state.rows = [
            row if isinstance(row, DeviceListRowState) else DeviceListRowState.from_mapping(row)
            for row in devices
        ]

    def row_count(self) -> int:
        return self.state.row_count()

    def get_device(self, index: int) -> DeviceListRowState:
        return self.state.get_row(index)

    def add_device(self, row: DeviceListRowState | Mapping[str, Any] | None = None, index: int | None = None) -> DeviceListRowState:
        return self.state.add_row(row=row, index=index)

    def update_device(self, index: int, **changes: Any) -> DeviceListRowState:
        return self.state.update_row(index, **changes)

    def remove_devices(self, indices: Sequence[int]) -> list[DeviceListRowState]:
        return self.state.remove_rows(indices)

    def move_device(self, source_index: int, target_index: int) -> None:
        if source_index == target_index:
            return
        if source_index < 0 or source_index >= len(self.state.rows):
            return
        row = self.state.rows.pop(source_index)
        if target_index > source_index:
            target_index -= 1
        if target_index < 0:
            target_index = 0
        if target_index > len(self.state.rows):
            target_index = len(self.state.rows)
        self.state.rows.insert(target_index, row)

    def calculate(self) -> LoopCalculationResult:
        kwargs: dict[str, Any] = {
            "max_current_ma": self.calc.max_current_ma,
            "min_voltage_v": self.calc.min_voltage_v,
            "cable_resistance_ohm_per_km": self.calc.cable_resistance_ohm_per_km,
            "addr_limit": self.calc.addr_limit,
        }
        if self.calc.cable_types is not None:
            kwargs["cable_types"] = self.calc.cable_types
        self.last_result = calculate_loop_from_rows(self.state.to_loop_devices(), **kwargs)
        return self.last_result

    def total_quantity(self) -> int:
        return self.state.total_quantity()

    def export_state(self) -> dict[str, Any]:
        return self.to_payload()

    def import_state(self, payload: Mapping[str, Any] | None) -> None:
        other = self.from_payload(payload)
        self.state = other.state
        self.calc = other.calc
        self.last_result = other.last_result
