from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QFrame,
    QHeaderView,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .selection_table import NoHoverDelegate
from .styles import unified_table_style
from .ui_support import NumericDelegate, PlainTextDelegate

if TYPE_CHECKING:
    from .database import ProductDatabase


class ProductManagerWidget(QWidget):
    data_changed = Signal()

    def __init__(self, db: ProductDatabase, main_app: Any, parent: QWidget | None = None):
        super().__init__(parent)
        self.db = db
        self.main_app = main_app
        self.p: dict[str, str] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        self.toolbar_frame = QFrame()
        self.toolbar_frame.setObjectName("productToolbar")
        toolbar_layout = QVBoxLayout(self.toolbar_frame)
        toolbar_layout.setContentsMargins(16, 16, 16, 16)
        toolbar_layout.setSpacing(12)
        self.toolbar_title = QLabel()
        self.toolbar_title.setObjectName("productToolbarTitle")
        toolbar_layout.addWidget(self.toolbar_title)

        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)
        self.search_input = QLineEdit()
        self.search_input.setFixedWidth(self._s(360))
        self.search_input.textChanged.connect(self._filter_products)
        top_bar.addWidget(self.search_input)
        top_bar.addStretch()

        self.btn_add_product = QPushButton()
        self.btn_add_product.clicked.connect(self._add_product)
        top_bar.addWidget(self.btn_add_product)

        self.btn_add_category = QPushButton()
        self.btn_add_category.clicked.connect(self._add_category)
        top_bar.addWidget(self.btn_add_category)

        self.btn_delete_selected = QPushButton()
        self.btn_delete_selected.clicked.connect(self._delete_selected_products)
        top_bar.addWidget(self.btn_delete_selected)

        self.btn_restore_defaults = QPushButton()
        self.btn_restore_defaults.clicked.connect(self._restore_defaults)
        top_bar.addWidget(self.btn_restore_defaults)

        self.btn_save = QPushButton()
        self.btn_save.clicked.connect(self._save_changes)
        top_bar.addWidget(self.btn_save)
        toolbar_layout.addLayout(top_bar)
        layout.addWidget(self.toolbar_frame)

        content_layout = QHBoxLayout()
        content_layout.setSpacing(16)

        self.left_panel = QFrame()
        self.left_panel.setObjectName("productCategoryPanel")
        self.left_panel.setFixedWidth(self._s(230))
        left_layout = QVBoxLayout(self.left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        self.category_label = QLabel()
        self.category_label.setStyleSheet("font-weight: 700; font-size: 11px;")
        self.category_label.setObjectName("categoryHeader")
        left_layout.addWidget(self.category_label)

        self.category_list = QListWidget()
        self.category_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.category_list.currentRowChanged.connect(self._filter_products)
        left_layout.addWidget(self.category_list)
        content_layout.addWidget(self.left_panel)

        self.table = QTableWidget()
        # Source, Category, Product Name, Factory Name, Customer Name, Standby, Alarm, ID(hidden)
        self.table.setColumnCount(8)
        self.table.setColumnHidden(7, True)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(False)
        self.table.setShowGrid(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setItemDelegateForColumn(1, PlainTextDelegate())
        self.table.setItemDelegateForColumn(2, PlainTextDelegate())
        self.table.setItemDelegateForColumn(3, PlainTextDelegate())
        self.table.setItemDelegateForColumn(4, PlainTextDelegate())
        self.table.setItemDelegateForColumn(5, NumericDelegate())
        self.table.setItemDelegateForColumn(6, NumericDelegate())
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.Fixed)
        header.setSectionResizeMode(2, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Interactive)
        header.setSectionResizeMode(4, QHeaderView.Interactive)
        header.setCascadingSectionResizes(True)
        header.setMinimumSectionSize(60)
        header.setStretchLastSection(False)
        self.table.setItemDelegate(NoHoverDelegate(self))
        self._apply_auto_column_widths()
        content_layout.addWidget(self.table)
        layout.addLayout(content_layout)

        self.retranslate_ui()
        self.refresh_data()
        self.refresh_permissions()

    def retranslate_ui(self) -> None:
        self.search_input.setPlaceholderText(self.main_app.t("admin_search_placeholder"))
        self.btn_add_product.setText(self.main_app.t("admin_add_product"))
        self.btn_add_category.setText(self.main_app.t("admin_add_category"))
        self.btn_delete_selected.setText(self.main_app.t("delete_selected"))
        self.btn_restore_defaults.setText(self.main_app.t("restore_default_data"))
        self.btn_save.setText(self.main_app.t("admin_save"))
        self.category_label.setText(self.main_app.t("product_category").upper())
        self.toolbar_title.setText(self.main_app.t("database_manage").upper())
        self.table.setHorizontalHeaderLabels(
            [
                self.main_app.t("product_source").upper(),
                self.main_app.t("product_category").upper(),
                self.main_app.t("product_name").upper(),
                self.main_app.t("product_factory_name").upper(),
                self.main_app.t("product_customer_name").upper(),
                self.main_app.t("product_standby").upper() + " (uA)",
                self.main_app.t("product_alarm").upper() + " (mA)",
                "ID",
            ]
        )
        self.refresh_data()

    def _s(self, value: int) -> int:
        scale = getattr(self.main_app, "ui_scale", 1.0)
        return max(1, int(round(value * scale)))

    def _all_categories(self) -> list[str]:
        return self.db.categories()

    def refresh_data(self) -> None:
        current_cat = self._current_category()
        self.category_list.blockSignals(True)
        self.category_list.clear()
        for category in self._all_categories():
            self.category_list.addItem(QListWidgetItem(category))
        if self.category_list.count():
            target = 0
            if current_cat:
                for i in range(self.category_list.count()):
                    if self.category_list.item(i).text() == current_cat:
                        target = i
                        break
            self.category_list.setCurrentRow(target)
        self.category_list.blockSignals(False)
        self._filter_products()

    def _current_category(self) -> str | None:
        item = self.category_list.currentItem()
        return item.text() if item else None

    def _filter_products(self) -> None:
        search_text = self.search_input.text().strip().lower()
        selected_category = self._current_category()
        filtered: list[dict[str, Any]] = []
        for product in self.db.products:
            if selected_category and product.get("category") != selected_category:
                continue
            searchable = " ".join(
                [
                    str(product.get("category", "")),
                    str(product.get("product_name", "")),
                    str(product.get("factory_name", "")),
                    str(product.get("customer_name", "")),
                ]
            ).lower()
            if search_text and search_text not in searchable:
                continue
            filtered.append(product)
        filtered.sort(
            key=lambda product: (
                str(product.get("product_name", "")),
                str(product.get("factory_name", "")),
            )
        )
        self._display_products(filtered)

    def _display_products(self, products: list[dict[str, Any]]) -> None:
        self.table.setRowCount(len(products))
        for row, product in enumerate(products):
            self.table.setRowHeight(row, self._s(38))
            built_in = bool(product.get("built_in", True))
            product_id = str(product.get("id", ""))
            cells = [
                self.main_app.t("product_source_default") if built_in else self.main_app.t("product_source_added"),
                str(product.get("category", "")),
                str(product.get("product_name", "")),
                str(product.get("factory_name", "")),
                str(product.get("customer_name", "")),
                str(product.get("standby", 0.5)),
                str(product.get("alarm", 2.0)),
            ]
            for col, value in enumerate(cells):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, product_id)
                item.setToolTip(value)
                if col in (5, 6):
                    item.setTextAlignment(Qt.AlignCenter)
                item.setFlags(self._editable_flags(col, built_in))
                self.table.setItem(row, col, item)
            self.table.setItem(row, 7, QTableWidgetItem(product_id))
        self._apply_auto_column_widths()

    def _apply_auto_column_widths(self) -> None:
        """Keep compact columns fixed and distribute remaining width across name columns."""
        fixed_specs = {
            0: (90, 130),   # SOURCE
            1: (90, 140),   # CATEGORY
            5: (110, 150),  # STANDBY
            6: (100, 140),  # ALARM
        }
        for col, (min_w, max_w) in fixed_specs.items():
            self.table.resizeColumnToContents(col)
            target = self.table.columnWidth(col) + 12
            self.table.setColumnWidth(col, max(min_w, min(target, max_w)))

        visible_width = self.table.viewport().width() or self.table.width()
        fixed_width = sum(self.table.columnWidth(col) for col in fixed_specs)
        available = max(240, visible_width - fixed_width - 8)

        # Preferred distribution: Product gets more room; factory/customer share the rest.
        widths = [int(available * 0.52), int(available * 0.24), 0]
        widths[2] = available - widths[0] - widths[1]
        mins = [160, 110, 110]

        if available >= sum(mins):
            deficit = 0
            for i, min_w in enumerate(mins):
                if widths[i] < min_w:
                    deficit += min_w - widths[i]
                    widths[i] = min_w
            if deficit > 0:
                for i in (0, 1, 2):
                    if deficit <= 0:
                        break
                    reducible = widths[i] - mins[i]
                    take = min(deficit, max(0, reducible))
                    widths[i] -= take
                    deficit -= take
        else:
            # In narrow windows prioritize visibility over minimum preferred widths.
            widths = [int(available * 0.50), int(available * 0.25), 0]
            widths[2] = available - widths[0] - widths[1]

        self.table.setColumnWidth(2, max(80, widths[0]))
        self.table.setColumnWidth(3, max(70, widths[1]))
        self.table.setColumnWidth(4, max(70, widths[2]))

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        self._apply_auto_column_widths()

    def _editable_flags(self, column: int, built_in: bool) -> Qt.ItemFlags:
        flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
        if column == 0:
            return flags
        can_edit_all = self.main_app.auth_level == 2 and column in (1, 2, 3, 4, 5, 6)
        can_edit_customer_only = self.main_app.auth_level == 1 and column == 4
        if can_edit_all or can_edit_customer_only:
            flags |= Qt.ItemIsEditable
        return flags

    def _add_category(self) -> None:
        if self.main_app.auth_level < 1:
            QMessageBox.warning(self, self.main_app.t("notice_title"), self.main_app.t("auth_admin_required"))
            return
        name, ok = QInputDialog.getText(self, self.main_app.t("admin_add_category"), self.main_app.t("admin_enter_category"))
        name = name.strip()
        if not ok:
            return
        if not name:
            QMessageBox.warning(self, self.main_app.t("notice_title"), self.main_app.t("admin_enter_category"))
            return
        if name in self._all_categories():
            QMessageBox.warning(self, self.main_app.t("notice_title"), f"{name} already exists.")
            return
        self.db.add_category(name)
        self.refresh_data()
        for i in range(self.category_list.count()):
            if self.category_list.item(i).text() == name:
                self.category_list.setCurrentRow(i)
                break

    def _delete_selected_products(self) -> None:
        if self.main_app.auth_level < 2:
            QMessageBox.warning(self, self.main_app.t("notice_title"), self.main_app.t("auth_factory_required"))
            return
        rows = sorted({idx.row() for idx in self.table.selectionModel().selectedRows()})
        if not rows:
            self._delete_selected_category()
            return
        selected_ids: list[str] = []
        for row in rows:
            id_item = self.table.item(row, 7)
            if not id_item:
                continue
            product_id = id_item.text()
            product = self.db.get_product(product_id)
            if not product:
                continue
            selected_ids.append(product_id)
        if not selected_ids:
            return
        message = self.main_app.t("admin_delete_confirm", name=f"{len(selected_ids)} selected items")
        if QMessageBox.question(self, self.main_app.t("admin_delete_product"), message) != QMessageBox.Yes:
            return
        self.db.products = [product for product in self.db.products if product.get("id") not in selected_ids]
        self.db.save()
        self.refresh_data()
        self.data_changed.emit()

    def _delete_selected_category(self) -> None:
        category = self._current_category()
        if not category:
            QMessageBox.information(self, self.main_app.t("notice_title"), self.main_app.t("delete_selected"))
            return
        if category not in self.db.extra_categories:
            QMessageBox.information(self, self.main_app.t("notice_title"), self.main_app.t("admin_delete_category"))
            return

        category_products = [product for product in self.db.products if product.get("category") == category]
        built_in_products = [product for product in category_products if bool(product.get("built_in", True))]
        if built_in_products:
            QMessageBox.warning(self, self.main_app.t("notice_title"), self.main_app.t("admin_category_in_use"))
            return

        delete_count = len(category_products)
        delete_label = f"{category}"
        if delete_count > 0:
            delete_label = f"{category} ({delete_count} products)"
        message = self.main_app.t("admin_delete_confirm", name=delete_label)
        if QMessageBox.question(self, self.main_app.t("admin_delete_category"), message) != QMessageBox.Yes:
            return

        self.db.extra_categories = [item for item in self.db.extra_categories if item != category]
        if delete_count > 0:
            self.db.products = [product for product in self.db.products if product.get("category") != category]
        self.db.save()
        self.refresh_data()
        self.data_changed.emit()

    def _add_product(self) -> None:
        if self.main_app.auth_level < 1:
            QMessageBox.warning(self, self.main_app.t("notice_title"), self.main_app.t("auth_admin_required"))
            return
        categories = self._all_categories() or self.db.categories()
        category, ok = QInputDialog.getItem(
            self,
            self.main_app.t("admin_add_product"),
            self.main_app.t("product_category") + ":",
            categories,
            0,
            False,
        )
        if not ok:
            return
        factory_name, ok = QInputDialog.getText(
            self, self.main_app.t("admin_add_product"), self.main_app.t("product_factory_name") + ":"
        )
        if not ok or not factory_name.strip():
            return
        product_name, ok = QInputDialog.getText(
            self, self.main_app.t("admin_add_product"), self.main_app.t("product_name") + ":"
        )
        if not ok:
            return
        self.db.products.append(
            {
                "id": self.db.next_product_id(),
                "category": category,
                "factory_name": factory_name.strip(),
                "customer_name": factory_name.strip(),
                "product_name": product_name.strip(),
                "standby": 0.5,
                "alarm": 2.0,
                "ledCost": 1,
                "type": category,
                "built_in": False,
            }
        )
        self.db.save()
        self.refresh_data()
        self.data_changed.emit()

    def _save_changes(self) -> None:
        if self.main_app.auth_level < 1:
            QMessageBox.warning(self, self.main_app.t("notice_title"), self.main_app.t("auth_admin_required"))
            return
        try:
            updates: dict[str, dict[str, Any]] = {}
            for row in range(self.table.rowCount()):
                id_item = self.table.item(row, 7)
                if not id_item:
                    continue
                product_id = id_item.text()
                updates[product_id] = {
                    "category": self.table.item(row, 1).text(),
                    "product_name": self.table.item(row, 2).text(),
                    "factory_name": self.table.item(row, 3).text(),
                    "customer_name": self.table.item(row, 4).text(),
                    "standby": float(self.table.item(row, 5).text() or 0),
                    "alarm": float(self.table.item(row, 6).text() or 0),
                }
            for product in self.db.products:
                pid = product.get("id")
                if pid in updates:
                    if self.main_app.auth_level >= 2:
                        product.update(updates[pid])
                    else:
                        product["customer_name"] = updates[pid]["customer_name"]
                    if not product.get("type"):
                        product["type"] = product.get("category", "Other")
            self.db.save()
            QMessageBox.information(self, self.main_app.t("admin_save"), self.main_app.t("admin_save_success"))
            self.refresh_data()
            self.data_changed.emit()
        except Exception as exc:
            QMessageBox.critical(self, self.main_app.t("notice_title"), f"{self.main_app.t('admin_save_error')}: {exc}")

    def _restore_defaults(self) -> None:
        if self.main_app.auth_level < 2:
            QMessageBox.warning(self, self.main_app.t("notice_title"), self.main_app.t("auth_factory_required"))
            return
        if hasattr(self.main_app, "_restore_default_data"):
            self.main_app._restore_default_data()

    def refresh_permissions(self) -> None:
        is_admin = self.main_app.auth_level >= 1
        is_factory = self.main_app.auth_level >= 2
        self.btn_add_product.setEnabled(is_admin)
        self.btn_add_category.setEnabled(is_admin)
        self.btn_delete_selected.setEnabled(is_factory)
        self.btn_restore_defaults.setEnabled(is_factory)
        self.btn_save.setEnabled(is_admin)
        self.refresh_data()

    def apply_style(self, p: dict[str, str]) -> None:
        self.p = p
        mono_font = "font-family: 'Space Mono', monospace; font-size: 12px;"
        divider = p.get("divider", p["border"])
        header_h = max(28, self.table.horizontalHeader().height())
        row_h = self._s(38)
        self.category_label.setFixedHeight(header_h)
        self.category_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {p['surface']};
                border: none;
                border-radius: 0px;
                color: {p['text']};
                font-family: 'Space Mono', monospace;
                font-size: 13px;
                font-weight: 500;
                outline: none;
            }}
            QListWidget::item {{
                padding: 6px 12px;
                min-height: {max(20, row_h - 14)}px;
                border-bottom: 1px solid {divider};
            }}
            QListWidget::item:hover {{
                background-color: {p['surface_alt']};
                color: {p['text']};
            }}
            QListWidget::item:selected {{
                background-color: {p['accent_soft']};
                color: {p['text']};
                font-weight: 700;
                border-left: 3px solid {p['accent']};
            }}
            """
        )
        self.category_label.setStyleSheet(
            f"""
            QLabel#categoryHeader {{
                background-color: {p['surface_alt']};
                color: {p['text']};
                font-family: 'Space Grotesk', 'Segoe UI', sans-serif;
                font-weight: 800;
                font-size: 11px;
                line-height: {max(1, header_h - 2)}px;
                letter-spacing: 0.8px;
                text-transform: uppercase;
                border-bottom: 1px solid {divider};
                padding: 0 10px;
                min-height: {header_h}px;
                max-height: {header_h}px;
            }}
            """
        )
        self.left_panel.setStyleSheet(
            f"""
            QFrame#productCategoryPanel {{
                border: 1px solid {p['border']};
                border-radius: 0px;
                background-color: {p['surface']};
            }}
            """
        )
        self.toolbar_frame.setStyleSheet(
            f"""
            QFrame#productToolbar {{
                border: 1px solid {p['border']};
                border-radius: 12px;
                background-color: {p['surface']};
            }}
            QLabel#productToolbarTitle {{
                color: {p['text']};
                font-size: 13px;
                font-weight: 800;
                letter-spacing: 0.8px;
            }}
            """
        )
        self.table.setStyleSheet(
            unified_table_style(p)
            + f"""
QTableWidget::item {{{mono_font}}}
QTableWidget {{
    border-radius: 0px;
}}
QHeaderView::section {{
    border-radius: 0px;
}}
"""
        )
        self.search_input.setStyleSheet(
            f"border: 1px solid {p['border']}; border-radius: 10px; background: {p['surface_alt']}; color: {p['text']}; padding: 0 12px;"
        )
        self.btn_add_product.setStyleSheet(self.main_app.primary_button_style())
        self.btn_add_category.setStyleSheet(self.main_app.secondary_button_style())
        self.btn_delete_selected.setStyleSheet(self.main_app.danger_outline_button_style())
        self.btn_restore_defaults.setStyleSheet(self.main_app.danger_outline_button_style())
        self.btn_save.setStyleSheet(self.main_app.primary_outline_button_style())
