from __future__ import annotations

from contextlib import contextmanager
from typing import Any

from PySide6.QtWidgets import QPushButton

from .device_list_model import DeviceListModel
from .device_list_qt_model import DeviceListQtModel
from .device_list_state import DeviceListRowState as DeviceRowState


def clear_layout(layout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        if item.widget():
            item.widget().deleteLater()


def build_category_buttons(editor) -> None:
    clear_layout(editor.category_toolbar)
    editor.category_buttons = []
    for category in editor.product_db.categories():
        button = QPushButton(editor.t('add_category_prefix', category=category))
        button.clicked.connect(lambda checked=False, cat=category: editor.add_device_row(cat))
        editor.category_buttons.append(button)
    layout_category_buttons(editor)


def layout_category_buttons(editor) -> None:
    layout = editor.category_toolbar
    while layout.count():
        layout.takeAt(0)
    if not editor.category_buttons:
        return

    host_width = max(1, editor.category_toolbar_host.width())
    spacing = layout.horizontalSpacing() if layout.horizontalSpacing() >= 0 else 8

    row = 0
    col = 0
    used_width = 0
    for button in editor.category_buttons:
        button_width = max(button.sizeHint().width(), button.minimumSizeHint().width())
        extra = 0 if col == 0 else spacing
        if col > 0 and (used_width + extra + button_width) > host_width:
            row += 1
            col = 0
            used_width = 0
            extra = 0
        layout.addWidget(button, row, col)
        used_width += extra + button_width
        col += 1


def reload_cables(editor, cable_types) -> None:
    current = editor.combo_cable.currentData()
    current_size = current['size'] if current else None
    editor.combo_cable.blockSignals(True)
    editor.combo_cable.clear()
    for cable in cable_types:
        editor.combo_cable.addItem(f"{cable['label']} ({cable['resistance']} \u03A9/km)", cable)
        if cable['size'] == current_size:
            editor.combo_cable.setCurrentIndex(editor.combo_cable.count() - 1)
    if editor.combo_cable.currentIndex() < 0 and editor.combo_cable.count() > 1:
        editor.combo_cable.setCurrentIndex(1)
    editor.combo_cable.blockSignals(False)


def default_row_snapshot(editor, category: str) -> dict[str, Any]:
    options = editor.product_db.product_options_by_category(category)
    lead = '10.0' if editor.device_list_controller.model.row_count() else '0.0'
    if options:
        option = dict(options[0])
        option.update({'lead_dist': lead, 'interval_dist': '10.0', 'qty': 1})
        return option
    return {'product_id': None, 'display_name': '', 'category': category, 'standby': 0.5, 'alarm': 0.0, 'ledCost': 1, 'type': category, 'lead_dist': lead, 'interval_dist': '10.0', 'qty': 1}
class DeviceListController:
    def __init__(self, editor) -> None:
        self.editor = editor
        self.model = DeviceListModel()
        self.qt_model = DeviceListQtModel(self.model)
        self._batch_depth = 0
        self._recalc_pending = False

    @property
    def rows(self) -> list[DeviceRowState]:
        return self.model.state.rows

    @rows.setter
    def rows(self, value: list[DeviceRowState]) -> None:
        self.model.set_devices([row.to_payload() for row in value])

    @contextmanager
    def batch_update(self):
        self._batch_depth += 1
        try:
            yield
        finally:
            self._batch_depth -= 1
            if self._batch_depth == 0 and self._recalc_pending:
                self._recalc_pending = False
                self.editor.run_calculation()

    def request_recalculation(self) -> None:
        if self._batch_depth > 0:
            self._recalc_pending = True
            return
        self.editor.run_calculation()

    def _row_state(self, row: int) -> DeviceRowState:
        if 0 <= row < len(self.rows):
            return DeviceRowState.from_payload(self.rows[row])
        return DeviceRowState()

    def delete_selected_rows(self) -> None:
        selection_model = self.editor.table.selectionModel()
        if selection_model is None:
            return
        selection = selection_model.selectedRows()
        if not selection:
            return
        with self.batch_update():
            removed_rows = sorted({idx.row() for idx in selection}, reverse=True)
            if removed_rows:
                self.qt_model.remove_devices(removed_rows)
            self.editor._refresh_row_selection_feedback(set())
            self.qt_model.refresh_from_backing()

    def add_row(self, category: str, row_state: dict[str, Any] | None = None) -> bool:
        limit = int(self.editor.combo_addr_limit.currentText())
        if self.editor.get_total_qty() >= limit:
            self.editor._warn('add_failed_title', 'add_failed_message', limit=limit)
            return False
        row_state = DeviceRowState.from_payload(
            self.editor.product_db.resolve_row_state(row_state or default_row_snapshot(self.editor, category))
        )
        with self.batch_update():
            self.qt_model.add_device(row_state.to_payload())
            self.qt_model.refresh_from_backing()
        notice = self.qt_model.consume_notice()
        if notice:
            self.editor._warn_text(notice)
            return False
        return True

    def collect_rows(self) -> list[dict[str, Any]]:
        return self.model.state.to_loop_devices()

    def serialize_rows(self) -> list[dict[str, Any]]:
        return [row.to_mapping() for row in self.model.state.rows]

    def export_state(self) -> dict[str, Any]:
        self.model.state.panel_type = self.editor.panel_type
        self.model.state.addr_limit_index = self.editor.combo_addr_limit.currentIndex()
        self.model.state.cable_index = self.editor.combo_cable.currentIndex()
        self.model.state.min_voltage = float(self.editor.edit_min_voltage.text() or 17)
        self.model.state.aux_current = float(self.editor.edit_aux.text() or 0)
        payload = self.model.export_state()
        payload['min_voltage'] = str(self.model.state.min_voltage)
        payload['aux_current'] = str(self.model.state.aux_current)
        payload['rows'] = self.serialize_rows()
        return payload

    def calculate(self, *, cable_resistance_ohm_per_km: float, cable_types) -> Any:
        self.model.update_calculation_context(
            max_current_ma=float(self.editor.edit_max_current.text() or 400),
            min_voltage_v=float(self.editor.edit_min_voltage.text() or 17),
            cable_resistance_ohm_per_km=cable_resistance_ohm_per_km,
            addr_limit=int(self.editor.combo_addr_limit.currentText()),
            cable_types=cable_types,
        )
        return self.model.calculate()

    def import_state(self, state: dict[str, Any]) -> None:
        self.qt_model.import_state(state)
        with self.batch_update():
            self.editor.combo_addr_limit.setCurrentIndex(self.model.state.addr_limit_index)
            self.editor.combo_cable.setCurrentIndex(self.model.state.cable_index)
            self.editor.edit_min_voltage.setText(str(self.model.state.min_voltage))
            self.editor.edit_aux.setText(str(self.model.state.aux_current))
        self.editor.apply_panel_settings()
        self.qt_model.refresh_from_backing()
        self.request_recalculation()

    def refresh_products(self) -> None:
        build_category_buttons(self.editor)
        with self.batch_update():
            updated_rows: list[dict[str, Any]] = []
            for row in range(self.model.row_count()):
                row_data = DeviceRowState.from_payload(
                    self.editor.product_db.resolve_row_state(self._row_state(row).to_payload())
                )
                updated_rows.append(row_data.to_payload())
            self.model.set_devices(updated_rows)
            self.qt_model.refresh_from_backing()
        self.editor.refresh_theme()


def add_device_row(editor, category: str, row_state: dict[str, Any] | None = None) -> None:
    editor.device_list_controller.add_row(category, row_state)


def collect_table_rows(editor) -> list[dict[str, Any]]:
    return editor.device_list_controller.collect_rows()


def export_state(editor) -> dict[str, Any]:
    return editor.device_list_controller.export_state()


def import_state(editor, state: dict[str, Any]) -> None:
    editor.device_list_controller.import_state(state)


def refresh_products(editor) -> None:
    editor.device_list_controller.refresh_products()
