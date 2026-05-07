from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QListWidget,
    QMessageBox,
    QPushButton,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionComboBox,
    QStylePainter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .ui_support import set_message_box_texts


class _MainAppProtocol(Protocol):
    auth_level: int

    def t(self, key: str, **kwargs: Any) -> str: ...
    def primary_button_style(self) -> str: ...
    def secondary_button_style(self) -> str: ...
    def danger_outline_button_style(self) -> str: ...
    def reload_products(self, refresh_only: bool = False) -> None: ...


class _ProductPopupDelegate(QStyledItemDelegate):
    def initStyleOption(self, option, index):  # type: ignore[override]
        super().initStyleOption(option, index)
        popup_name = index.data(Qt.UserRole + 3)
        if popup_name:
            option.text = str(popup_name)


class ProductComboBox(QComboBox):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("deviceProductCombo")
        self.setFrame(False)
        self.setEditable(False)
        self.setItemDelegate(_ProductPopupDelegate(self))

    def add_product_option(self, option: dict[str, Any]) -> None:
        self.addItem(option.get('display_name', ''), option.get('product_id'))
        index = self.count() - 1
        self.setItemData(index, option.get('display_name', ''), Qt.UserRole + 1)
        self.setItemData(index, dict(option), Qt.UserRole + 2)
        self.setItemData(index, option.get('popup_name', ''), Qt.UserRole + 3)

    def paintEvent(self, event) -> None:
        option = QStyleOptionComboBox()
        self.initStyleOption(option)
        option.currentText = str(self.currentData(Qt.UserRole + 1) or self.currentText() or "")

        painter = QStylePainter(self)
        painter.drawComplexControl(QStyle.CC_ComboBox, option)
        painter.drawControl(QStyle.CE_ComboBoxLabel, option)


class ProductDatabaseDialog(QDialog):
    def __init__(self, main_app: _MainAppProtocol, product_db: Any, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.main_app = main_app
        self.product_db = product_db
        self.working_products = [dict(product) for product in product_db.products]
        self.visible_category: str | None = None
        self.setMinimumSize(980, 620)
        self._build_ui()
        self._load_categories()
        self.retranslate_ui()
        self.refresh_theme()

    def t(self, key: str, **kwargs: Any) -> str:
        return self.main_app.t(key, **kwargs)

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setSpacing(0)

        left_panel = QWidget()
        left_panel.setFixedWidth(100)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        self.lbl_categories = QLabel()
        left_layout.addWidget(self.lbl_categories)
        self.category_list = QListWidget()
        self.category_list.setFixedWidth(100)
        self.category_list.currentRowChanged.connect(self._on_category_changed)
        left_layout.addWidget(self.category_list, 1)
        left_buttons = QVBoxLayout()
        left_buttons.setContentsMargins(0, 0, 0, 0)
        left_buttons.setSpacing(4)
        self.btn_add_category = QPushButton()
        self.btn_rename_category = QPushButton()
        self.btn_delete_category = QPushButton()
        left_buttons.addWidget(self.btn_add_category)
        left_buttons.addWidget(self.btn_rename_category)
        left_buttons.addWidget(self.btn_delete_category)
        left_layout.addLayout(left_buttons)

        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        self.lbl_products = QLabel()
        right_layout.addWidget(self.lbl_products)
        self.product_table = QTableWidget(0, 5)
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.product_table.verticalHeader().setVisible(False)
        self.product_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Interactive)
        self.product_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Interactive)
        self.product_table.setColumnWidth(0, 170)
        self.product_table.setColumnWidth(1, 170)
        self.product_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.product_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.product_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        right_layout.addWidget(self.product_table, 1)
        button_row = QHBoxLayout()
        self.btn_add_product = QPushButton()
        self.btn_delete_product = QPushButton()
        self.btn_save = QPushButton()
        self.btn_close = QPushButton()
        button_row.addWidget(self.btn_add_product)
        button_row.addWidget(self.btn_delete_product)
        button_row.addStretch()
        button_row.addWidget(self.btn_save)
        button_row.addWidget(self.btn_close)
        right_layout.addLayout(button_row)

        layout.addWidget(left_panel, 0)
        layout.addLayout(right_layout, 1)

        self.btn_add_category.clicked.connect(self._add_category)
        self.btn_rename_category.clicked.connect(self._rename_category)
        self.btn_delete_category.clicked.connect(self._delete_category)
        self.btn_add_product.clicked.connect(self._add_product)
        self.btn_delete_product.clicked.connect(self._delete_product)
        self.btn_save.clicked.connect(self._save)
        self.btn_close.clicked.connect(self.reject)

    def retranslate_ui(self) -> None:
        self.setWindowTitle(self.t('database_manage'))
        self.lbl_categories.setText(self.t('admin_categories'))
        self.lbl_products.setText(self.t('admin_products'))
        self.btn_add_category.setText(self.t('admin_add_category'))
        self.btn_rename_category.setText(self.t('admin_rename_category'))
        self.btn_delete_category.setText(self.t('admin_delete_category'))
        self.btn_add_product.setText(self.t('admin_add_product'))
        self.btn_delete_product.setText(self.t('admin_delete_product'))
        self.btn_save.setText(self.t('admin_save'))
        self.btn_close.setText(self.t('admin_close'))
        self.product_table.setHorizontalHeaderLabels([
            self.t('product_factory_name'),
            self.t('product_customer_name'),
            self.t('product_name'),
            self.t('product_standby'),
            self.t('product_alarm'),
        ])

    def refresh_theme(self) -> None:
        self.btn_add_category.setStyleSheet(self.main_app.secondary_button_style())
        self.btn_rename_category.setStyleSheet(self.main_app.secondary_button_style())
        self.btn_delete_category.setStyleSheet(self.main_app.danger_outline_button_style())
        self.btn_add_product.setStyleSheet(self.main_app.primary_button_style())
        self.btn_delete_product.setStyleSheet(self.main_app.secondary_button_style())
        self.btn_save.setStyleSheet(self.main_app.secondary_button_style())
        self.btn_close.setStyleSheet(self.main_app.secondary_button_style())

    def _categories(self) -> list[str]:
        seen: list[str] = []
        for product in self.working_products:
            category = product.get('category', 'Other')
            if category not in seen:
                seen.append(category)
        return seen

    def _load_categories(self) -> None:
        self.category_list.clear()
        for category in self._categories():
            self.category_list.addItem(category)
        if self.category_list.count():
            self.category_list.setCurrentRow(0)
        else:
            self.product_table.setRowCount(0)

    def _current_category(self) -> str | None:
        item = self.category_list.currentItem()
        return item.text() if item else None

    def _reload_products(self) -> None:
        category = self._current_category()
        self.visible_category = category
        rows = [p for p in self.working_products if p.get('category') == category] if category else []
        self.product_table.setRowCount(0)
        for row, product in enumerate(rows):
            self.product_table.insertRow(row)
            built_in = product.get('built_in', True)
            values = [
                product.get('factory_name', ''),
                product.get('customer_name', ''),
                product.get('product_name', ''),
                str(product.get('standby', 0)),
                str(product.get('alarm', 0)),
            ]
            can_edit_all = self.main_app.auth_level == 2 or not built_in
            can_edit_customer_only = self.main_app.auth_level == 1 and built_in
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, product.get('id'))
                flags = Qt.ItemIsSelectable | Qt.ItemIsEnabled
                if can_edit_all or (can_edit_customer_only and col == 1):
                    flags |= Qt.ItemIsEditable
                item.setFlags(flags)
                self.product_table.setItem(row, col, item)

    def _flush_visible_products(self) -> None:
        visible = self._collect_table_products()
        if visible:
            self.working_products = [visible.get(product['id'], product) for product in self.working_products]

    def _on_category_changed(self, _row: int = 0) -> None:
        self._flush_visible_products()
        self._reload_products()

    def _ask_text(self, title_key: str, label_key: str, text: str = '') -> tuple[str, bool]:
        value, ok = QInputDialog.getText(self, self.t(title_key), self.t(label_key), text=text)
        return value.strip(), ok

    def _add_category(self) -> None:
        name, ok = self._ask_text('admin_add_category', 'admin_enter_category')
        if ok and name and name not in self._categories():
            self.category_list.addItem(name)
            self.category_list.setCurrentRow(self.category_list.count() - 1)

    def _rename_category(self) -> None:
        self._flush_visible_products()
        category = self._current_category()
        if not category:
            return
        name, ok = self._ask_text('admin_rename_category', 'admin_enter_category', category)
        if ok and name and name != category:
            for product in self.working_products:
                if product.get('category') == category:
                    product['category'] = name
                    if product.get('type') == category:
                        product['type'] = name
            self._load_categories()
            items = self.category_list.findItems(name, Qt.MatchExactly)
            if items:
                self.category_list.setCurrentItem(items[0])

    def _delete_category(self) -> None:
        self._flush_visible_products()
        category = self._current_category()
        if not category:
            return
        if any(product.get('category') == category for product in self.working_products):
            QMessageBox.warning(self, self.t('notice_title'), self.t('admin_category_in_use'))
            return
        self.category_list.takeItem(self.category_list.currentRow())

    def _add_product(self) -> None:
        self._flush_visible_products()
        category = self._current_category()
        if not category:
            return
        self.working_products.append({
            'id': self.product_db.next_product_id(),
            'category': category,
            'factory_name': 'New Product',
            'customer_name': 'New Product',
            'product_name': '',
            'standby': 0.5,
            'alarm': 2.0,
            'ledCost': 1,
            'type': category,
            'built_in': False,
        })
        self._reload_products()
        if self.product_table.rowCount():
            self.product_table.selectRow(self.product_table.rowCount() - 1)

    def _delete_product(self) -> None:
        self._flush_visible_products()
        row = self.product_table.currentRow()
        if row < 0:
            return
        item = self.product_table.item(row, 0)
        product_id = item.data(Qt.UserRole) if item else None
        product = next((p for p in self.working_products if p.get('id') == product_id), None)
        if self.main_app.auth_level == 1 and product and product.get('built_in', True):
            QMessageBox.warning(self, self.t('notice_title'), self.t('admin_delete_built_in_error'))
            return
        self.working_products = [p for p in self.working_products if p.get('id') != product_id]
        self._reload_products()

    def _collect_table_products(self) -> dict[str, dict[str, Any]]:
        category = self.visible_category
        collected: dict[str, dict[str, Any]] = {}
        for row in range(self.product_table.rowCount()):
            first = self.product_table.item(row, 0)
            if not first:
                continue
            product_id = first.data(Qt.UserRole)
            collected[product_id] = {
                'id': product_id,
                'factory_name': self.product_table.item(row, 0).text().strip(),
                'customer_name': self.product_table.item(row, 1).text().strip(),
                'product_name': self.product_table.item(row, 2).text().strip(),
                'category': next((p.get('category', category or 'Other') for p in self.working_products if p.get('id') == product_id), category or 'Other'),
                'standby': float(self.product_table.item(row, 3).text() or 0),
                'alarm': float(self.product_table.item(row, 4).text() or 0),
                'ledCost': next((p.get('ledCost', 1) for p in self.working_products if p.get('id') == product_id), 1),
                'type': next((p.get('type', category or 'Other') for p in self.working_products if p.get('id') == product_id), category or 'Other'),
            }
        return collected

    def _save(self) -> None:
        self._flush_visible_products()
        updated_visible = self._collect_table_products()
        self.product_db.replace_all([updated_visible.get(product['id'], product) for product in self.working_products])
        self.main_app.reload_products()
        QMessageBox.information(self, self.t('notice_title'), self.t('admin_save_success'))
        self.accept()
