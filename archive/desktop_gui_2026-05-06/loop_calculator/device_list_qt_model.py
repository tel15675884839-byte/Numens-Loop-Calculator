from __future__ import annotations

"""Qt table model for the Device List refactor.

This module is intentionally standalone and does not require the rest of the UI
to migrate immediately. It wraps the existing Qt-free `DeviceListModel` so the
current widget-based screen can later move to `QTableView` with minimal
behavioral drift.
"""

from typing import Any, Mapping, Sequence

from PySide6.QtCore import QAbstractTableModel, QModelIndex, Qt

from .calculator import LoopDeviceInput
from .device_list_model import DeviceListModel
from .device_list_state import DeviceListRowState

SOUNDER_DEVICE_LIMIT = 32


class DeviceListQtRoles:
    """Custom roles used by the future table view."""

    RowStateRole = Qt.UserRole + 1
    LoopInputRole = Qt.UserRole + 2
    CategoryRole = Qt.UserRole + 3
    ProductIdRole = Qt.UserRole + 4
    DisplayNameRole = Qt.UserRole + 5
    RawPayloadRole = Qt.UserRole + 6


class DeviceListQtColumns:
    """Column indices for the table model."""

    Index = 0
    Device = 1
    LeadDistance = 2
    IntervalDistance = 3
    Quantity = 4

    COUNT = 5


class DeviceListQtModel(QAbstractTableModel):
    """A QAbstractTableModel facade over the existing DeviceListModel."""

    def __init__(self, backing: DeviceListModel | None = None, parent=None) -> None:
        super().__init__(parent)
        self._model = backing or DeviceListModel()
        self._pending_notice: str | None = None
        self._headers = {
            DeviceListQtColumns.Index: "#",
            DeviceListQtColumns.Device: "Device",
            DeviceListQtColumns.LeadDistance: "Lead Dist",
            DeviceListQtColumns.IntervalDistance: "Interval Dist",
            DeviceListQtColumns.Quantity: "Qty",
        }

    @property
    def backing(self) -> DeviceListModel:
        return self._model

    def set_backing(self, backing: DeviceListModel) -> None:
        self.beginResetModel()
        self._model = backing
        self.endResetModel()

    def rowCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        if parent is not None and parent.isValid():
            return 0
        return self._model.row_count()

    def columnCount(self, parent: QModelIndex | None = None) -> int:  # type: ignore[override]
        if parent is not None and parent.isValid():
            return 0
        return DeviceListQtColumns.COUNT

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if role != Qt.DisplayRole:
            return None
        if orientation == Qt.Horizontal:
            return self._headers.get(section, "")
        return section + 1

    def set_header_labels(self, labels: Mapping[int, str]) -> None:
        self._headers.update({int(section): str(text) for section, text in labels.items()})
        self.headerDataChanged.emit(Qt.Horizontal, 0, self.columnCount() - 1)

    def consume_notice(self) -> str | None:
        notice = self._pending_notice
        self._pending_notice = None
        return notice

    def flags(self, index: QModelIndex) -> Qt.ItemFlags:  # type: ignore[override]
        if not index.isValid():
            return Qt.ItemIsEnabled
        base = Qt.ItemIsEnabled | Qt.ItemIsSelectable
        if index.column() in {
            DeviceListQtColumns.Device,
            DeviceListQtColumns.LeadDistance,
            DeviceListQtColumns.IntervalDistance,
            DeviceListQtColumns.Quantity,
        }:
            base |= Qt.ItemIsEditable
        if index.column() == DeviceListQtColumns.IntervalDistance and self._model.get_device(index.row()).qty <= 1:
            base &= ~Qt.ItemIsEditable
        return base

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:  # type: ignore[override]
        if not index.isValid():
            return None

        row_index = index.row()
        row = self._model.get_device(row_index)
        if role in (Qt.DisplayRole, Qt.EditRole):
            return self._display_value(row_index, row, index.column())

        if role == DeviceListQtRoles.RowStateRole:
            return row.copy()
        if role == DeviceListQtRoles.LoopInputRole:
            return row.to_loop_device_input()
        if role == DeviceListQtRoles.CategoryRole:
            return row.category
        if role == DeviceListQtRoles.ProductIdRole:
            return row.product_id
        if role == DeviceListQtRoles.DisplayNameRole:
            return row.display_name
        if role == DeviceListQtRoles.RawPayloadRole:
            return row.to_mapping()
        if role == Qt.TextAlignmentRole:
            if index.column() == DeviceListQtColumns.Index:
                return Qt.AlignCenter
            if index.column() in {
                DeviceListQtColumns.LeadDistance,
                DeviceListQtColumns.IntervalDistance,
                DeviceListQtColumns.Quantity,
            }:
                return Qt.AlignCenter
        if role == Qt.ToolTipRole and index.column() == DeviceListQtColumns.Device:
            return self._device_tooltip(row)
        if role == Qt.UserRole:
            return self._row_index_payload(row, row_index)
        return None

    def setData(self, index: QModelIndex, value: Any, role: int = Qt.EditRole) -> bool:  # type: ignore[override]
        if not index.isValid() or role not in (Qt.EditRole, Qt.DisplayRole):
            return False

        row = self._model.get_device(index.row())
        changed = False

        if index.column() == DeviceListQtColumns.Device:
            changed = self._apply_device_change(index.row(), row, value)
        elif index.column() == DeviceListQtColumns.LeadDistance:
            changed = self._apply_float_change(index.row(), "lead_dist_m", value)
        elif index.column() == DeviceListQtColumns.IntervalDistance:
            changed = self._apply_float_change(index.row(), "interval_dist_m", value)
        elif index.column() == DeviceListQtColumns.Quantity:
            changed = self._apply_int_change(index.row(), "qty", value, minimum=1)

        if changed:
            self._emit_row_changed(index.row())
        return changed

    def insertRows(
        self,
        row: int,
        count: int = 1,
        parent: QModelIndex | None = None,
        rows: Sequence[DeviceListRowState | Mapping[str, Any] | LoopDeviceInput] | None = None,
    ) -> bool:  # type: ignore[override]
        if parent is not None and parent.isValid():
            return False
        if count <= 0:
            return False
        insert_at = max(0, min(row, self.rowCount()))
        payload_rows = list(rows or [])
        self.beginInsertRows(QModelIndex(), insert_at, insert_at + count - 1)
        for offset in range(count):
            source = payload_rows[offset] if offset < len(payload_rows) else None
            state = self._coerce_row(source)
            self._model.add_device(state, index=insert_at + offset)
        self.endInsertRows()
        return True

    def removeRows(self, row: int, count: int = 1, parent: QModelIndex | None = None) -> bool:  # type: ignore[override]
        if parent is not None and parent.isValid():
            return False
        if count <= 0 or row < 0 or row >= self.rowCount():
            return False
        last = min(row + count - 1, self.rowCount() - 1)
        self.beginRemoveRows(QModelIndex(), row, last)
        self._model.remove_devices(range(row, last + 1))
        self.endRemoveRows()
        return True

    def moveRows(
        self,
        sourceParent: QModelIndex,
        sourceRow: int,
        count: int,
        destinationParent: QModelIndex,
        destinationChild: int,
    ) -> bool:  # type: ignore[override]
        if sourceParent.isValid() or destinationParent.isValid():
            return False
        if count != 1 or sourceRow < 0 or sourceRow >= self.rowCount():
            return False
        if destinationChild == sourceRow:
            return False
        self.beginMoveRows(QModelIndex(), sourceRow, sourceRow, QModelIndex(), destinationChild)
        self._model.move_device(sourceRow, destinationChild)
        self.endMoveRows()
        return True

    def refresh_from_backing(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    def set_devices(self, devices: Sequence[DeviceListRowState | Mapping[str, Any] | LoopDeviceInput]) -> None:
        self.beginResetModel()
        self._model.set_devices([self._coerce_row(device) for device in devices])
        self.endResetModel()

    def add_device(self, row: DeviceListRowState | Mapping[str, Any] | LoopDeviceInput | None = None, index: int | None = None) -> DeviceListRowState:
        state = self._coerce_row(row)
        if self._counts_toward_sounder_limit(state) and self._sounder_available_slots() < 1:
            self._pending_notice = "Load is full."
            return state
        insert_at = self.rowCount() if index is None else max(0, min(index, self.rowCount()))
        self.beginInsertRows(QModelIndex(), insert_at, insert_at)
        inserted = self._model.add_device(state, index=insert_at)
        self.endInsertRows()
        return inserted

    def update_device(self, index: int, **changes: Any) -> DeviceListRowState:
        updated = self._model.update_device(index, **changes)
        self._emit_row_changed(index)
        return updated

    def remove_devices(self, indices: Sequence[int]) -> list[DeviceListRowState]:
        removed_indices = sorted({i for i in indices if 0 <= i < self.rowCount()})
        if not removed_indices:
            return []
        removed: list[DeviceListRowState] = []
        for index in reversed(removed_indices):
            self.beginRemoveRows(QModelIndex(), index, index)
            removed.extend(self._model.remove_devices([index]))
            self.endRemoveRows()
        return list(reversed(removed))

    def to_payload(self) -> dict[str, Any]:
        payload = self._model.to_payload()
        payload["rows"] = [self._model.get_device(i).to_mapping() for i in range(self.rowCount())]
        return payload

    def export_state(self) -> dict[str, Any]:
        return self.to_payload()

    def import_state(self, payload: Mapping[str, Any] | None) -> None:
        self.beginResetModel()
        self._model.import_state(payload)
        self.endResetModel()

    def to_loop_inputs(self) -> list[LoopDeviceInput]:
        return self._model.state.to_loop_devices()

    def get_device(self, index: int) -> DeviceListRowState:
        return self._model.get_device(index)

    def row_state(self, index: int) -> DeviceListRowState:
        return self._model.get_device(index)

    def row_payload(self, index: int) -> dict[str, Any]:
        return self._model.get_device(index).to_mapping()

    def _display_value(self, row_index: int, row: DeviceListRowState, column: int) -> Any:
        if column == DeviceListQtColumns.Index:
            return str(row_index + 1)
        if column == DeviceListQtColumns.Device:
            return row.display_name
        if column == DeviceListQtColumns.LeadDistance:
            return row.lead_dist_m
        if column == DeviceListQtColumns.IntervalDistance:
            return row.interval_dist_m
        if column == DeviceListQtColumns.Quantity:
            return row.qty
        return None

    def _coerce_row(self, value: DeviceListRowState | Mapping[str, Any] | LoopDeviceInput | None) -> DeviceListRowState:
        return DeviceListRowState.from_payload(value)

    def _apply_device_change(self, row_index: int, row: DeviceListRowState, value: Any) -> bool:
        if isinstance(value, Mapping):
            payload = dict(value)
            device_id = payload.get("product_id", row.product_id)
            display_name = payload.get("display_name", row.display_name)
            category = payload.get("category", row.category)
            standby = payload.get("standby", row.standby)
            alarm = payload.get("alarm", row.alarm)
            led_cost = payload.get("ledCost", row.led_cost)
            device_type = payload.get("type", row.device_type)
            customer_name = payload.get("customer_name", row.customer_name)
            factory_name = payload.get("factory_name", row.factory_name)
            product_name = payload.get("product_name", row.product_name)
        else:
            device_id = row.product_id
            display_name = str(value or row.display_name)
            category = row.category
            standby = row.standby
            alarm = row.alarm
            led_cost = row.led_cost
            device_type = row.device_type
            customer_name = row.customer_name
            factory_name = row.factory_name
            product_name = row.product_name

        next_row = row.with_updates(
            product_id=device_id,
            display_name=str(display_name or ""),
            category=str(category or "Other"),
            standby=float(standby),
            alarm=float(alarm),
            led_cost=max(0, int(led_cost)),
            device_type=str(device_type or ""),
            customer_name=str(customer_name or ""),
            factory_name=str(factory_name or ""),
            product_name=str(product_name or display_name or ""),
        )
        if self._counts_toward_sounder_limit(next_row) and self._sounder_available_slots(excluding_row=row_index) < 1:
            self._pending_notice = "Load is full."
            self._emit_row_changed(row_index)
            return False

        updated = self._model.update_device(
            row_index,
            product_id=next_row.product_id,
            display_name=next_row.display_name,
            category=next_row.category,
            standby=next_row.standby,
            alarm=next_row.alarm,
            led_cost=next_row.led_cost,
            device_type=next_row.device_type,
            customer_name=next_row.customer_name,
            factory_name=next_row.factory_name,
            product_name=next_row.product_name,
        )
        self._enforce_sounder_limit(row_index, notify=True)
        return updated is not None

    def _apply_float_change(self, row_index: int, field_name: str, value: Any) -> bool:
        row = self._model.get_device(row_index)
        changes = {field_name: float(value)}
        self._model.update_device(row_index, **changes)
        return row != self._model.get_device(row_index)

    def _apply_int_change(self, row_index: int, field_name: str, value: Any, *, minimum: int = 0) -> bool:
        row = self._model.get_device(row_index)
        requested = value
        sounder_clamped = False
        try:
            parsed = int(float(value))
        except (TypeError, ValueError):
            parsed = minimum
        parsed = max(minimum, parsed)
        if field_name == "qty":
            other_total = sum(device.qty for idx, device in enumerate(self._model.state.rows) if idx != row_index)
            max_allowed = max(minimum, self._model.calc.addr_limit - other_total)
            parsed = min(parsed, max_allowed)
            if self._counts_toward_sounder_limit(row):
                other_sounder_total = sum(
                    device.qty
                    for idx, device in enumerate(self._model.state.rows)
                    if idx != row_index and self._counts_toward_sounder_limit(device)
                )
                max_sounder_allowed = max(minimum, SOUNDER_DEVICE_LIMIT - other_sounder_total)
                before_sounder_limit = parsed
                parsed = min(parsed, max_sounder_allowed)
                sounder_clamped = parsed < before_sounder_limit
        if field_name == "qty":
            try:
                requested_int = int(float(requested))
            except (TypeError, ValueError):
                requested_int = parsed
            if sounder_clamped and parsed < requested_int:
                self._pending_notice = "Load is full."
        self._model.update_device(row_index, **{field_name: parsed})
        return row != self._model.get_device(row_index)

    def _counts_toward_sounder_limit(self, row: DeviceListRowState) -> bool:
        if str(row.category or "").strip().lower() == "sounder":
            return True
        haystack = " ".join(
            [
                str(row.display_name or ""),
                str(row.product_name or ""),
                str(row.customer_name or ""),
                str(row.factory_name or ""),
                str(row.device_type or ""),
            ]
        ).upper()
        return "LSM" in haystack or "620-003" in haystack

    def _sounder_available_slots(self, *, excluding_row: int | None = None) -> int:
        used = sum(
            device.qty
            for idx, device in enumerate(self._model.state.rows)
            if idx != excluding_row and self._counts_toward_sounder_limit(device)
        )
        return SOUNDER_DEVICE_LIMIT - used

    def _enforce_sounder_limit(self, row_index: int, *, notify: bool = False) -> None:
        if row_index < 0 or row_index >= self.rowCount():
            return
        row = self._model.get_device(row_index)
        if not self._counts_toward_sounder_limit(row):
            return
        other_sounder_total = sum(
            device.qty
            for idx, device in enumerate(self._model.state.rows)
            if idx != row_index and self._counts_toward_sounder_limit(device)
        )
        max_allowed = max(1, SOUNDER_DEVICE_LIMIT - other_sounder_total)
        if row.qty > max_allowed:
            if notify:
                self._pending_notice = "Load is full."
            self._model.update_device(row_index, qty=max_allowed)

    def _row_index_payload(self, row: DeviceListRowState, row_index: int) -> dict[str, Any]:
        return {
            "row": row_index,
            "state": row.copy(),
            "payload": row.to_mapping(),
            "input": row.to_loop_device_input(),
        }

    def _device_tooltip(self, row: DeviceListRowState) -> str:
        return f"Standby: {row.standby} mA\nAlarm: {row.alarm} mA"

    def _emit_row_changed(self, row_index: int) -> None:
        if row_index < 0 or row_index >= self.rowCount():
            return
        top_left = self.index(row_index, 0)
        bottom_right = self.index(row_index, self.columnCount() - 1)
        self.dataChanged.emit(top_left, bottom_right, [Qt.DisplayRole, Qt.EditRole, Qt.ToolTipRole])


__all__ = [
    "DeviceListQtColumns",
    "DeviceListQtModel",
    "DeviceListQtRoles",
]
