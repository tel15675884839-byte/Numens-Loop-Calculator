from __future__ import annotations

"""Pure data structures for the Device List refactor.

These classes intentionally stay Qt-free so they can be used by the current
widget-based UI, future model/view code, tests, or command-line tools.
"""

from dataclasses import dataclass, field, replace
from typing import Any, Iterable, Mapping, Sequence

from .calculator import LoopDeviceInput, coerce_device_input


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


@dataclass(slots=True)
class DeviceListRowState:
    """Serializable row snapshot used by the Device List.

    The shape is aligned with the current product database and loop calculator
    inputs so the UI can migrate to this class without translating fields over
    and over again.
    """

    product_id: str | None = None
    display_name: str = ""
    category: str = "Other"
    standby: float = 0.5
    alarm: float = 0.0
    led_cost: int = 1
    device_type: str = ""
    customer_name: str = ""
    factory_name: str = ""
    product_name: str = ""
    lead_dist_m: float = 0.0
    interval_dist_m: float = 0.0
    qty: int = 1
    meta: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "DeviceListRowState":
        data = dict(payload or {})
        device = coerce_device_input(data)
        return cls(
            product_id=device.product_id,
            display_name=str(data.get("display_name", device.display_name) or ""),
            category=str(data.get("category", device.category) or "Other"),
            standby=_coerce_float(data.get("standby", device.standby_ma), 0.5),
            alarm=_coerce_float(data.get("alarm", device.alarm_ma), 0.0),
            led_cost=max(0, _coerce_int(data.get("ledCost", device.led_cost), 1)),
            device_type=str(data.get("type", device.device_type) or ""),
            customer_name=str(data.get("customer_name", "") or ""),
            factory_name=str(data.get("factory_name", "") or ""),
            product_name=str(data.get("product_name", device.display_name) or ""),
            lead_dist_m=_coerce_float(data.get("lead_dist", data.get("lead_dist_m", device.lead_dist_m)), 0.0),
            interval_dist_m=_coerce_float(data.get("interval_dist", data.get("interval_dist_m", device.interval_dist_m)), 0.0),
            qty=max(1, _coerce_int(data.get("qty", device.qty), 1)),
            meta={k: v for k, v in data.items() if k not in cls._known_keys()},
        )

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any] | LoopDeviceInput | "DeviceListRowState" | None) -> "DeviceListRowState":
        if isinstance(payload, cls):
            return payload.copy()
        if isinstance(payload, LoopDeviceInput):
            return cls.from_loop_device_input(payload)
        return cls.from_mapping(payload)

    @classmethod
    def from_loop_device_input(
        cls,
        device: LoopDeviceInput,
        *,
        meta: Mapping[str, Any] | None = None,
    ) -> "DeviceListRowState":
        return cls(
            product_id=device.product_id,
            display_name=device.display_name,
            category=device.category,
            standby=device.standby_ma,
            alarm=device.alarm_ma,
            led_cost=device.led_cost,
            device_type=device.device_type,
            lead_dist_m=device.lead_dist_m,
            interval_dist_m=device.interval_dist_m,
            qty=max(1, device.qty),
            meta=dict(meta or {}),
        )

    @staticmethod
    def _known_keys() -> set[str]:
        return {
            "product_id",
            "display_name",
            "category",
            "standby",
            "alarm",
            "ledCost",
            "type",
            "customer_name",
            "factory_name",
            "product_name",
            "lead_dist",
            "lead_dist_m",
            "interval_dist",
            "interval_dist_m",
            "qty",
            "meta",
        }

    def to_mapping(self) -> dict[str, Any]:
        payload = {
            "product_id": self.product_id,
            "display_name": self.display_name,
            "category": self.category,
            "standby": self.standby,
            "alarm": self.alarm,
            "ledCost": self.led_cost,
            "type": self.device_type,
            "customer_name": self.customer_name,
            "factory_name": self.factory_name,
            "product_name": self.product_name,
            "lead_dist": self.lead_dist_m,
            "interval_dist": self.interval_dist_m,
            "qty": self.qty,
        }
        payload.update(self.meta)
        return payload

    def to_payload(self) -> dict[str, Any]:
        return self.to_mapping()

    def to_loop_device_input(self) -> LoopDeviceInput:
        return LoopDeviceInput(
            product_id=self.product_id,
            display_name=self.display_name,
            category=self.category or "Other",
            standby_ma=float(self.standby),
            alarm_ma=float(self.alarm),
            led_cost=max(0, int(self.led_cost)),
            device_type=self.device_type,
            lead_dist_m=float(self.lead_dist_m),
            interval_dist_m=float(self.interval_dist_m),
            qty=max(1, int(self.qty)),
        )

    def with_updates(self, **changes: Any) -> "DeviceListRowState":
        return replace(self, **changes)

    def copy(self) -> "DeviceListRowState":
        return replace(self)

    @property
    def ledCost(self) -> int:
        return self.led_cost

    @ledCost.setter
    def ledCost(self, value: int) -> None:
        self.led_cost = max(0, _coerce_int(value, self.led_cost))

    @property
    def type(self) -> str:
        return self.device_type

    @type.setter
    def type(self, value: str) -> None:
        self.device_type = str(value or "")

    @property
    def lead_dist(self) -> float:
        return self.lead_dist_m

    @lead_dist.setter
    def lead_dist(self, value: float) -> None:
        self.lead_dist_m = _coerce_float(value, self.lead_dist_m)

    @property
    def interval_dist(self) -> float:
        return self.interval_dist_m

    @interval_dist.setter
    def interval_dist(self, value: float) -> None:
        self.interval_dist_m = _coerce_float(value, self.interval_dist_m)


@dataclass(slots=True)
class DeviceListState:
    """Container for the whole Device List screen.

    This is the future single source of truth for the list. The current UI can
    incrementally adopt it without changing the user-facing behavior.
    """

    panel_type: str = "Standard"
    addr_limit_index: int = 0
    cable_index: int = 1
    min_voltage: float = 17.0
    aux_current: float = 0.0
    rows: list[DeviceListRowState] = field(default_factory=list)
    selected_rows: set[int] = field(default_factory=set)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any] | None) -> "DeviceListState":
        data = dict(payload or {})
        rows = [
            DeviceListRowState.from_mapping(row)
            for row in data.get("rows", [])
            if isinstance(row, Mapping)
        ]
        selected_rows = {
            _coerce_int(value, -1)
            for value in data.get("selected_rows", [])
            if isinstance(value, (int, float, str))
        }
        return cls(
            panel_type=str(data.get("panel_type", "Standard") or "Standard"),
            addr_limit_index=_coerce_int(data.get("addr_limit_index", 0), 0),
            cable_index=_coerce_int(data.get("cable_index", 1), 1),
            min_voltage=_coerce_float(data.get("min_voltage", 17.0), 17.0),
            aux_current=_coerce_float(data.get("aux_current", 0.0), 0.0),
            rows=rows,
            selected_rows={index for index in selected_rows if index >= 0},
        )

    @classmethod
    def from_loop_devices(
        cls,
        devices: Sequence[LoopDeviceInput | Mapping[str, Any]],
        *,
        panel_type: str = "Standard",
    ) -> "DeviceListState":
        return cls(
            panel_type=panel_type,
            rows=[
                DeviceListRowState.from_loop_device_input(
                    coerce_device_input(device),
                    meta=device if isinstance(device, Mapping) else None,
                )
                for device in devices
            ],
        )

    def to_mapping(self) -> dict[str, Any]:
        return {
            "panel_type": self.panel_type,
            "addr_limit_index": self.addr_limit_index,
            "cable_index": self.cable_index,
            "min_voltage": self.min_voltage,
            "aux_current": self.aux_current,
            "rows": [row.to_mapping() for row in self.rows],
            "selected_rows": sorted(self.selected_rows),
        }

    def to_loop_devices(self) -> list[LoopDeviceInput]:
        return [row.to_loop_device_input() for row in self.rows]

    def add_row(self, row: DeviceListRowState | Mapping[str, Any] | None = None, index: int | None = None) -> DeviceListRowState:
        state = row if isinstance(row, DeviceListRowState) else DeviceListRowState.from_mapping(row)
        if index is None or index >= len(self.rows):
            self.rows.append(state)
        else:
            self.rows.insert(max(0, index), state)
        return state

    def get_row(self, index: int) -> DeviceListRowState:
        return self.rows[index]

    def row_count(self) -> int:
        return len(self.rows)

    def is_empty(self) -> bool:
        return not self.rows

    def update_row(self, index: int, **changes: Any) -> DeviceListRowState:
        current = self.rows[index]
        updated = current.with_updates(**changes)
        self.rows[index] = updated
        return updated

    def remove_rows(self, indices: Iterable[int]) -> list[DeviceListRowState]:
        removed: list[DeviceListRowState] = []
        for index in sorted({i for i in indices if i >= 0}, reverse=True):
            if index < len(self.rows):
                removed.append(self.rows.pop(index))
        self.selected_rows = {i for i in self.selected_rows if i < len(self.rows)}
        return list(reversed(removed))

    def clear(self) -> None:
        self.rows.clear()
        self.selected_rows.clear()

    def set_selection(self, indices: Iterable[int]) -> None:
        self.selected_rows = {i for i in indices if i >= 0 and i < len(self.rows)}

    def total_quantity(self) -> int:
        return sum(row.qty for row in self.rows)

    def copy(self) -> "DeviceListState":
        return DeviceListState.from_mapping(self.to_mapping())
