from __future__ import annotations
import os
from typing import Any, Protocol

from PySide6.QtCore import QUrl, Qt, Signal
from PySide6.QtGui import QColor, QDesktopServices, QDoubleValidator, QIntValidator, QPalette
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .calculator import render_diagnostic_messages
from .core_widgets import ProductDatabaseDialog
from .device_list_delegates import DeviceDistanceDelegate, DeviceProductDelegate, DeviceQtyDelegate
from .device_list_qt_model import DeviceListQtColumns
from .loop_editor_support import (
    DeviceListController,
    add_device_row,
    build_category_buttons,
    layout_category_buttons,
    clear_layout,
    export_state,
    import_state,
    refresh_products,
    reload_cables,
)
from .selection_table import StableMultiSelectView
from .styles import palette, unified_table_style
from .ui_support import maybe_recalc_window, set_message_box_texts
try:
    from .constants import ADMIN_PASSWORD, ADDRESS_LIMIT, CABLE_TYPES, FACTORY_PASSWORD, MAX_ALARM_LEDS, MAX_CABLE_LENGTH, PANEL_SPECS
except ImportError:  # pragma: no cover - safe fallback while the package is being split
    from .calculator import DEFAULT_CABLE_TYPES, DEFAULT_MAX_ALARM_LEDS, DEFAULT_MAX_CABLE_LENGTH_M

    ADDRESS_LIMIT = 125
    MAX_ALARM_LEDS = DEFAULT_MAX_ALARM_LEDS
    MAX_CABLE_LENGTH = DEFAULT_MAX_CABLE_LENGTH_M
    FACTORY_PASSWORD = '8'
    ADMIN_PASSWORD = '1'
    PANEL_SPECS = {'Standard': {'quiescent': 200, 'aux_limit': 200, 'max_loops': 6}}
    CABLE_TYPES = [
        {'size': cable.size, 'resistance': cable.resistance_ohm_per_km, 'label': f'{cable.size} mm²', 'unit': cable.unit}
        for cable in DEFAULT_CABLE_TYPES
    ]


CABLE_TYPES = [{**cable, 'label': f"{cable['size']} mm²"} for cable in CABLE_TYPES]


CABLE_TYPES = [{**cable, 'label': f"{cable['size']} mm\u00B2"} for cable in CABLE_TYPES]


def _sq_mm_label() -> str:
    return "mm" + "\u00B2"

class ResultRow(QWidget):
    def __init__(self, name: str, value_dict: dict, label_dict: dict, unit_dict: dict | None, key: str, unit: str, default="0"):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        self.lbl_name = QLabel(name)
        self.lbl_name.setStyleSheet("font-size: 13px;")
        self.lbl_val = QLabel(default)
        self.lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.lbl_val.setStyleSheet("font-weight: bold; font-family: 'Space Mono', 'Consolas'; font-size: 14px;")
        self.lbl_unit = QLabel(unit)
        self.lbl_unit.setFixedWidth(50)
        self.lbl_unit.setStyleSheet("font-size: 11px; padding-left: 4px;")
        
        layout.addWidget(self.lbl_name)
        layout.addWidget(self.lbl_val, 1)
        layout.addWidget(self.lbl_unit)
        value_dict[key] = self.lbl_val
        if label_dict is not None:
            label_dict[key] = self.lbl_name
        if unit_dict is not None:
            unit_dict[key] = self.lbl_unit
        self.name_key = name

class ResultSection(QWidget):
    def __init__(self, title: str):
        super().__init__()
        self.setObjectName("resultSection")
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)
        
        self.header = QLabel(title.upper())
        self.header.setObjectName("sectionHeader")
        self.content_layout.addWidget(self.header)
        
        self.rows_container = QWidget()
        self.rows_layout = QVBoxLayout(self.rows_container)
        self.rows_layout.setContentsMargins(0, 8, 0, 12)
        self.rows_layout.setSpacing(2)
        self.content_layout.addWidget(self.rows_container)

    def add_row(self, name_key: str, value_dict: dict, label_dict: dict, key: str, unit: str, editor: LoopEditorWidget, default="0"):
        unit_dict = editor.units if editor else None
        row = ResultRow(name_key, value_dict, label_dict, unit_dict, key, unit, default)
        self.rows_layout.addWidget(row)
        if editor:
            editor.result_labels[key] = row.lbl_name
            editor.result_keys[key] = name_key
        return row


class StatusCard(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setObjectName("statusCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        self.lbl_tag = QLabel("SYSTEM STATUS")
        self.lbl_tag.setObjectName("statusCardTag")
        self.lbl_state = QLabel("Normal")
        self.lbl_state.setObjectName("statusCardState")
        self.lbl_message = QLabel("Loop configuration is valid")
        self.lbl_message.setObjectName("statusCardMessage")
        self.lbl_message.setWordWrap(True)

        layout.addWidget(self.lbl_tag)
        layout.addWidget(self.lbl_state)
        layout.addWidget(self.lbl_message)
        layout.addStretch()


class _ThemeHost(Protocol):
    p: dict[str, str]

    def t(self, key: str, **kwargs: Any) -> str: ...
    def primary_button_style(self) -> str: ...
    def secondary_button_style(self) -> str: ...
    def inline_input_style(self) -> str: ...
    def diag_panel_style(self, ok: bool = True) -> str: ...


class _ProductDb(Protocol):
    def categories(self) -> list[str]: ...
    def product_options_by_category(self, category: str) -> list[dict[str, Any]]: ...
    def resolve_row_state(self, row_state: dict[str, Any]) -> dict[str, Any]: ...


class LoopEditorWidget(QWidget):
    data_changed = Signal()

    def __init__(self, panel_type: str, product_db: _ProductDb, main_app: _ThemeHost | None = None) -> None:
        super().__init__(main_app)
        self.panel_type = panel_type
        self.product_db = product_db
        self.main_app = main_app
        self.results: dict[str, QLabel] = {}
        self.units: dict[str, QLabel] = {}
        self.result_labels: dict[str, QLabel] = {}
        self.result_keys: dict[str, str] = {}
        self.last_errors: list[str] = []
        self.category_buttons: list[QPushButton] = []
        self.device_list_controller = DeviceListController(self)
        self._init_ui()
        self._bind()
        self.apply_panel_settings()
        self.retranslate_ui()
        self.refresh_theme()

    def t(self, key: str, **kwargs: Any) -> str:
        return self.main_app.t(key, **kwargs)

    def _s(self, value: int) -> int:
        scale = getattr(self.main_app, "ui_scale", 1.0) if self.main_app else 1.0
        return max(1, int(round(value * scale)))

    def _assets_root(self) -> str:
        return os.path.dirname(os.path.dirname(__file__))

    def _init_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(12)
        self.main_content_grid = QGridLayout()
        self.main_content_grid.setHorizontalSpacing(18)
        self.main_content_grid.setVerticalSpacing(12)

        self.sys_group = QGroupBox()
        self.sys_layout = QGridLayout(self.sys_group)
        self.sys_layout.setContentsMargins(14, 18, 14, 14)
        self.sys_layout.setHorizontalSpacing(18)
        self.sys_layout.setVerticalSpacing(12)
        self.lbl_addr_limit = QLabel()
        self.combo_addr_limit = QComboBox()
        self.combo_addr_limit.addItems(['125', '250'])
        param_input_width = self._s(150)
        self.combo_addr_limit.setFixedWidth(param_input_width)
        self.combo_addr_limit.setMinimumContentsLength(3)
        self.combo_addr_limit.setSizeAdjustPolicy(QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.lbl_max_current = QLabel()
        self.edit_max_current = QLineEdit('400')
        self.edit_max_current.setFixedWidth(param_input_width)
        self.edit_max_current.setEnabled(False)
        self.lbl_min_voltage = QLabel()
        self.edit_min_voltage = QLineEdit('17')
        self.edit_min_voltage.setFixedWidth(param_input_width)
        self.edit_min_voltage.setValidator(QDoubleValidator(0.0, 30.0, 1))
        self.lbl_cable = QLabel()
        self.combo_cable = QComboBox()
        self.combo_cable.setFixedWidth(self._s(220))
        self.system_parameter_fields = []
        fields = (
            (self.lbl_addr_limit, self.combo_addr_limit),
            (self.lbl_max_current, self.edit_max_current),
            (self.lbl_min_voltage, self.edit_min_voltage),
            (self.lbl_cable, self.combo_cable),
        )
        for label, widget in fields:
            label.setStyleSheet("font-weight: bold; font-size: 11px; text-transform: uppercase;")
            field = QWidget()
            field_layout = QVBoxLayout(field)
            field_layout.setContentsMargins(0, 0, 0, 0)
            field_layout.setSpacing(6)
            field_layout.addWidget(label)
            field_layout.addWidget(widget)
            self.system_parameter_fields.append(field)
        self._layout_system_parameters()
        # Logo is displayed in the left sidebar; keep system-parameter row clean here.
        self.main_content_grid.addWidget(self.sys_group, 0, 0)
        self.dev_group = QGroupBox()
        dev_layout = QVBoxLayout(self.dev_group)
        dev_layout.setContentsMargins(14, 18, 14, 14)
        dev_layout.setSpacing(12)
        toolbar = QHBoxLayout()
        toolbar.setSpacing(10)
        self.category_toolbar_host = QWidget()
        self.category_toolbar = QGridLayout(self.category_toolbar_host)
        self.category_toolbar.setContentsMargins(0, 0, 0, 0)
        self.category_toolbar.setHorizontalSpacing(8)
        self.category_toolbar.setVerticalSpacing(8)
        toolbar.addWidget(self.category_toolbar_host, 1)
        toolbar.addStretch()
        self.btn_delete = QPushButton()
        toolbar.addWidget(self.btn_delete)
        dev_layout.addLayout(toolbar)
        self.table = StableMultiSelectView()
        self.table.setModel(self.device_list_controller.qt_model)
        self.table.setEditTriggers(QAbstractItemView.EditKeyPressed)
        self.table.set_dropdown_columns({DeviceListQtColumns.Device})
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(True)
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setCascadingSectionResizes(False)
        header.setStretchLastSection(False)
        self.table.setColumnWidth(0, self._s(45))
        self.table.setColumnWidth(2, self._s(84))
        self.table.setColumnWidth(3, self._s(84))
        self.table.setColumnWidth(4, self._s(88))
        self.table.verticalHeader().setDefaultSectionSize(self._s(42))
        self.table.setItemDelegateForColumn(DeviceListQtColumns.Device, DeviceProductDelegate(self))
        self.table.setItemDelegateForColumn(DeviceListQtColumns.LeadDistance, DeviceDistanceDelegate(self, self.table))
        self.table.setItemDelegateForColumn(DeviceListQtColumns.IntervalDistance, DeviceDistanceDelegate(self, self.table))
        self.table.setItemDelegateForColumn(DeviceListQtColumns.Quantity, DeviceQtyDelegate(self, self.table))
        self.table.verticalHeader().setVisible(False)
        dev_layout.addWidget(self.table)
        self.main_content_grid.addWidget(self.dev_group, 1, 0)
        self.res_group = QGroupBox()
        res_layout = QVBoxLayout(self.res_group)
        res_layout.setContentsMargins(14, 18, 14, 14)
        res_layout.setSpacing(10)

        self.sec_status = ResultSection("Circuit Status")
        self.sec_status.add_row("point_load", self.results, self.result_labels, 'addr', f'/{ADDRESS_LIMIT}', self, '0')
        self.sec_status.add_row("total_loop_current", self.results, self.result_labels, 'curr', 'mA', self, '0')
        self.sec_status.add_row("end_voltage", self.results, self.result_labels, 'volt', 'V', self, '0')
        self.sec_status.add_row("loop_length", self.results, self.result_labels, 'lens', 'm', self, '0')
        res_layout.addWidget(self.sec_status)

        self.sec_opt = ResultSection("Safety Optimization")
        self.sec_opt.add_row("max_install_distance", self.results, self.result_labels, 'max_len', 'm', self, '0')
        self.sec_opt.add_row("theoretical_max_distance", self.results, self.result_labels, 'theo_max_len', 'm', self, '0')
        self.sec_opt.add_row("recommended_cable", self.results, self.result_labels, 'rec_cable', 'mm²', self, '0')
        if 'rec_cable' in self.units:
            self.units['rec_cable'].setText('mm²')
        res_layout.addWidget(self.sec_opt)

        self.sec_batt = ResultSection("Battery Life")
        # Special row for Aux Input
        aux_row = QWidget()
        aux_h = QHBoxLayout(aux_row)
        aux_h.setContentsMargins(8, 4, 8, 4)
        self.aux_name = QLabel("AUX Load")
        self.aux_name.setStyleSheet("font-family: 'Space Grotesk', 'Segoe UI', sans-serif; font-size: 13px;")
        aux_h.addWidget(self.aux_name)
        self.edit_aux = QLineEdit("0")
        self.edit_aux.setFixedWidth(self._s(60))
        self.edit_aux.setAlignment(Qt.AlignCenter)
        self.edit_aux.setValidator(QIntValidator(0, 9999, self.edit_aux))
        aux_h.addStretch()
        aux_h.addWidget(self.edit_aux)
        self.lbl_aux_unit = QLabel("mA")
        self.lbl_aux_unit.setFixedWidth(self._s(50))
        self.lbl_aux_unit.setStyleSheet("font-family: 'Space Grotesk', 'Segoe UI', sans-serif; font-size: 11px; padding-left: 4px;")
        aux_h.addWidget(self.lbl_aux_unit)
        self.sec_batt.rows_layout.addWidget(aux_row)
        
        self.sec_batt.add_row("standby_runtime", self.results, self.result_labels, 'std_time', 'h', self, '---')
        self.sec_batt.add_row("alarm_runtime", self.results, self.result_labels, 'alm_time', 'h', self, '---')
        res_layout.addWidget(self.sec_batt)

        res_layout.addStretch()
        self.diag_panel = StatusCard()
        self.diag_panel.setMinimumHeight(136)
        res_layout.addWidget(self.diag_panel)

        self.website_label = QLabel('<a href="https://www.numens.com" style="text-decoration:none;">www.numens.com</a>')
        self.website_label.setAlignment(Qt.AlignCenter)
        self.website_label.setCursor(Qt.PointingHandCursor)
        self.website_label.setTextInteractionFlags(Qt.TextBrowserInteraction)
        self.website_label.setOpenExternalLinks(False)
        self.website_label.linkActivated.connect(lambda url: QDesktopServices.openUrl(QUrl(url)))
        self.website_label.setVisible(False)
        res_layout.addSpacing(10)
        res_layout.addWidget(self.website_label)
        res_layout.addSpacing(10)
        
        self.main_content_grid.addWidget(self.res_group, 0, 1, 2, 1)
        self.main_content_grid.setColumnStretch(0, 7)
        self.main_content_grid.setColumnStretch(1, 4)
        self.main_content_grid.setRowStretch(0, 0)
        self.main_content_grid.setRowStretch(1, 1)

        main_layout.addLayout(self.main_content_grid)

    def _layout_system_parameters(self) -> None:
        while self.sys_layout.count():
            self.sys_layout.takeAt(0)
        host_width = self.sys_group.width() if self.sys_group.width() > 0 else self.width()
        compact = host_width > 0 and host_width < self._s(820)
        columns = 2 if compact else 4
        for index, field in enumerate(self.system_parameter_fields):
            row = index // columns
            col = index % columns
            self.sys_layout.addWidget(field, row, col)
        for col in range(4):
            self.sys_layout.setColumnStretch(col, 1 if col < columns else 0)

    def _bind(self) -> None:
        self.btn_delete.clicked.connect(self.delete_selected)
        self.table.selected_rows_changed.connect(self._refresh_row_selection_feedback)
        model = self.device_list_controller.qt_model
        model.dataChanged.connect(self.on_table_changed)
        model.rowsInserted.connect(lambda *_args: self.on_table_changed())
        model.rowsRemoved.connect(lambda *_args: self.on_table_changed())
        self.combo_cable.currentIndexChanged.connect(self.run_calculation)
        self.edit_min_voltage.textChanged.connect(self.run_calculation)
        self.edit_aux.textChanged.connect(self._sanitize_aux_curr)
        self.edit_aux.textChanged.connect(self.run_calculation)
        self.edit_aux.editingFinished.connect(self._validate_aux_curr)
        self.combo_addr_limit.currentIndexChanged.connect(self.validate_all_quantities)
        self.combo_addr_limit.currentIndexChanged.connect(self.run_calculation)

    def _clear_layout(self, layout) -> None:
        clear_layout(layout)

    def _rebuild_category_buttons(self) -> None:
        build_category_buttons(self)

    def _layout_category_buttons(self) -> None:
        layout_category_buttons(self)

    def _reload_cables(self) -> None:
        reload_cables(self, CABLE_TYPES)

    def _refresh_row_selection_feedback(self, selected_rows: set[int]) -> None:
        self._selected_rows_cache = set(selected_rows)
        self.device_list_controller.model.state.set_selection(selected_rows)

    def retranslate_ui(self) -> None:
        self.sys_group.setTitle(self.t('system_parameters'))
        self.dev_group.setTitle(self.t('device_list'))
        self.res_group.setTitle(self.t('calculation_results'))
        self.lbl_addr_limit.setText(self.t('loop_device_count'))
        self.lbl_max_current.setText(self.t('loop_current'))
        self.lbl_min_voltage.setText(self.t('minimum_voltage'))
        self.lbl_cable.setText(self.t('cable_spec'))
        self.btn_delete.setText(self.t('delete_selected'))
        
        self.sec_status.header.setText(self.t('current_loop_status').upper())
        self.sec_opt.header.setText(self.t('safety_suggestions').upper())
        self.aux_name.setText(self.t('aux_load'))

        for key, label_key in self.result_keys.items():
            if key in self.result_labels:
                self.result_labels[key].setText(self.t(label_key))
        if 'rec_cable' in self.units:
            self.units['rec_cable'].setText('mm\u00B2')

        self.device_list_controller.qt_model.set_header_labels({
            DeviceListQtColumns.Index: self.t('table_index'),
            DeviceListQtColumns.Device: self.t('table_device_name'),
            DeviceListQtColumns.LeadDistance: self.t('table_lead_dist'),
            DeviceListQtColumns.IntervalDistance: self.t('table_interval_dist'),
            DeviceListQtColumns.Quantity: self.t('table_qty'),
        })
        
        website = self.t('website_url')
        self.website_label.setText(f'<a href="https://{website}" style="text-decoration:none;">{website}</a>')
        self._reload_cables()
        self._rebuild_category_buttons()
        self.run_calculation()

    def refresh_theme(self) -> None:
        p = self.main_app.p if self.main_app else palette()
        style_host = self.window() if hasattr(self.window(), "primary_button_style") else self.main_app
        
        self.btn_delete.setStyleSheet(style_host.secondary_button_style())
        for button in self.category_buttons:
            button.setStyleSheet(style_host.primary_button_style())
        self._layout_category_buttons()
        self.table.setStyleSheet(unified_table_style(p))
        self._selected_rows_cache = set()
        selection_model = self.table.selectionModel()
        selected_rows = {index.row() for index in selection_model.selectedRows()} if selection_model else set()
        self._refresh_row_selection_feedback(selected_rows)
        self.edit_aux.setStyleSheet(style_host.inline_input_style())
        self.edit_aux.setAlignment(Qt.AlignCenter)
        for label in (self.lbl_addr_limit, self.lbl_max_current, self.lbl_min_voltage, self.lbl_cable):
            label.setStyleSheet(f"font-weight: bold; color: {p['text']}; font-size: 11px; text-transform: uppercase;")
        self.aux_name.setStyleSheet(f"color: {p['text']}; font-family: 'Space Grotesk', 'Segoe UI', sans-serif; font-size: 13px;")
        self.lbl_aux_unit.setStyleSheet(f"color: {p['text']}; font-family: 'Space Grotesk', 'Segoe UI', sans-serif; font-size: 11px; padding-left: 4px;")
        for key, value in self.result_labels.items():
            value.setStyleSheet(f"color: {p['text']}; font-size: 13px;")
        for key, value in self.results.items():
            value.setStyleSheet(f"font-weight: bold; font-family: 'Space Mono', 'Consolas'; font-size: 14px; color: {p['text']};")
        for key, value in self.units.items():
            value.setStyleSheet(f"color: {p['text']}; font-size: 11px; padding-left: 4px;")
        self.website_label.setStyleSheet(f"QLabel {{ color: {p['danger']}; font-weight: bold; font-size: 13px; padding-top: 8px; }} QLabel:hover {{ color: {p['accent']}; }}")
        self.diag_panel.setStyleSheet(self.main_app.diag_panel_style(ok=not self.last_errors))
        self.update_diag_panel(self.last_errors)

    def apply_panel_settings(self) -> None:
        self.edit_max_current.setText('400')
        self.combo_addr_limit.setEnabled(True)
        self.validate_all_quantities()
        self.run_calculation()

    def _warn(self, title_key: str, msg_key: str, **kwargs: Any) -> None:
        box = QMessageBox(QMessageBox.Warning, self.t(title_key), self.t(msg_key, **kwargs), parent=self)
        self._theme_message_box(box)
        box.setStandardButtons(QMessageBox.Ok)
        set_message_box_texts(box, self)
        box.exec()

    def _warn_text(self, message: str, title: str | None = None) -> None:
        box = QMessageBox(QMessageBox.Warning, title or self.t('notice_title'), message, parent=self)
        self._theme_message_box(box)
        box.setStandardButtons(QMessageBox.Ok)
        set_message_box_texts(box, self)
        box.exec()

    def _theme_message_box(self, box: QMessageBox) -> None:
        box.setWindowFlag(Qt.WindowMinimizeButtonHint, False)
        box.setWindowFlag(Qt.WindowMaximizeButtonHint, False)
        box.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        box.setWindowFlag(Qt.MSWindowsFixedSizeDialogHint, True)
        box.ensurePolished()
        box.adjustSize()
        box.setFixedWidth(max(box.sizeHint().width(), self._s(420)))
        host_window = self.window()
        if host_window is not None and hasattr(host_window, "_set_native_dark_title_bar") and hasattr(host_window, "theme"):
            host_window._set_native_dark_title_bar(host_window.theme in ["dark", "industrial"], box)

    def _validate_aux_curr(self) -> None:
        try:
            self._sanitize_aux_curr()
            limit = PANEL_SPECS[self.panel_type]['aux_limit']
            if int(self.edit_aux.text() or 0) > limit:
                self._warn('aux_over_title', 'aux_over_message')
                self.edit_aux.setText(str(limit))
                self.run_calculation()
        except Exception:
            pass

    def _sanitize_aux_curr(self, _text: str | None = None) -> None:
        raw = (self.edit_aux.text() or "").strip()
        if raw == "":
            return
        try:
            value = float(raw)
        except Exception:
            value = 0.0
        value = max(0, min(9999, int(value)))
        normalized = str(value)
        if normalized != raw:
            self.edit_aux.blockSignals(True)
            self.edit_aux.setText(normalized)
            self.edit_aux.blockSignals(False)

    def validate_all_quantities(self) -> None:
        limit = int(self.combo_addr_limit.currentText())
        total = self.get_total_qty()
        if total > limit:
            self._warn('total_devices_over_title', 'total_devices_over_message', total=total, limit=limit)

    def get_total_qty(self) -> int:
        return self.device_list_controller.model.total_quantity()

    def add_device_row(self, category: str, row_state: dict[str, Any] | None = None) -> None:
        add_device_row(self, category, row_state)

    def delete_selected(self) -> None:
        self.device_list_controller.delete_selected_rows()

    def on_table_changed(self, *_args) -> None:
        notice = self.device_list_controller.qt_model.consume_notice()
        if notice:
            self._warn_text(notice)
        self.validate_all_quantities()
        self.device_list_controller.request_recalculation()

    def get_aux_current(self) -> float:
        try:
            return float(self.edit_aux.text() or 0)
        except Exception:
            return 0

    def get_loop_standby_current(self) -> float:
        return getattr(self, '_loop_standby_i', 0)

    def get_loop_alarm_current(self) -> float:
        return getattr(self, '_loop_alarm_i', 0)

    def update_battery_display(self, h_std: float, h_alm: float) -> None:
        self.results['std_time'].setText(f'{h_std:.1f}')
        self.results['alm_time'].setText(f'{h_alm:.2f}')

    def export_state(self) -> dict[str, Any]:
        return export_state(self)

    def import_state(self, state: dict[str, Any]) -> None:
        import_state(self, state)

    def refresh_products(self) -> None:
        refresh_products(self)

    def update_diag_panel(self, errors: list[str] | None = None) -> None:
        self.last_errors = list(errors or [])
        if not self.last_errors:
            self.diag_panel.lbl_tag.setText("SYSTEM STATUS")
            self.diag_panel.lbl_state.setText("Normal")
            self.diag_panel.lbl_message.setText("Loop configuration is valid")
            self.diag_panel.setStyleSheet(self.main_app.diag_panel_style(ok=True))
        else:
            self.diag_panel.lbl_tag.setText("SYSTEM STATUS")
            self.diag_panel.lbl_state.setText("Attention")
            self.diag_panel.lbl_message.setText("\n".join(self.last_errors))
            self.diag_panel.setStyleSheet(self.main_app.diag_panel_style(ok=False))

    def run_calculation(self) -> None:
        if self.device_list_controller.model.row_count() == 0:
            self._loop_standby_i = 0
            self._loop_alarm_i = 0
            for key, value in self.results.items():
                value.setText('---' if key in {'std_time', 'alm_time'} else '0')
            self.update_diag_panel([])
            maybe_recalc_window(self)
            return
        try:
            cable = self.combo_cable.currentData()
            if not cable:
                return
            result = self.device_list_controller.calculate(
                cable_resistance_ohm_per_km=float(cable['resistance']),
                cable_types=CABLE_TYPES,
            )
            for key, value in result.as_display_values().items():
                self.results[key].setText(value)
            for key, value in result.as_unit_values().items():
                if key in self.units:
                    self.units[key].setText(value)
            if 'rec_cable' in self.units:
                self.units['rec_cable'].setText('mm\u00B2')
            self._loop_standby_i = result.standby_current_ma
            self._loop_alarm_i = result.alarm_current_ma
            self.update_diag_panel(render_diagnostic_messages(result.diagnostics, self.t))
            maybe_recalc_window(self)
            self.data_changed.emit()
        except Exception as exc:
            print(f'Calculation Error: {exc}')

    def resizeEvent(self, event) -> None:
        super().resizeEvent(event)
        self._layout_system_parameters()
        self._layout_category_buttons()
