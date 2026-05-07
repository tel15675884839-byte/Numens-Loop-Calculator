from __future__ import annotations

"""Delegate scaffolding for the future Device List table-view migration.

These delegates are intentionally isolated from the current widget-based UI.
They document the roles and editor behavior that the future QAbstractTableModel
is expected to provide, so the eventual migration only needs to swap the view
layer.
"""

from typing import Any, Protocol

from PySide6.QtCore import QPersistentModelIndex, Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QApplication, QComboBox, QLineEdit, QSpinBox, QStyle, QStyledItemDelegate, QStyleOptionViewItem, QWidget

from .core_widgets import ProductComboBox
from .device_list_qt_model import DeviceListQtRoles
from .styles import device_combo_style, palette, table_lineedit_style, table_spinbox_style

ROLE_ROW_KIND = DeviceListQtRoles.CategoryRole
ROLE_PRODUCT_ID = DeviceListQtRoles.ProductIdRole
ROLE_PRODUCT_PAYLOAD = DeviceListQtRoles.RawPayloadRole


class ProductDbProtocol(Protocol):
    """Minimal product-db contract expected by the delegates."""

    def product_options_by_category(self, category: str) -> list[dict[str, Any]]: ...


class DeviceListDelegateHost(Protocol):
    """Host contract for the delegate layer.

    The delegates only need access to the product database today. More hooks
    can be added later without changing the editor widgets.
    """

    product_db: ProductDbProtocol


def _index_data(index, role: int, default: Any = None) -> Any:
    model = index.model() if hasattr(index, "model") else None
    if model is None:
        return default
    value = model.data(index, role)
    return default if value is None else value


def _select_combo_item(combo: ProductComboBox, *, product_id: Any = None, display_name: Any = None) -> None:
    if product_id not in (None, ""):
        found = combo.findData(product_id)
        if found >= 0:
            combo.setCurrentIndex(found)
            return
    if display_name not in (None, ""):
        found = combo.findText(str(display_name))
        if found >= 0:
            combo.setCurrentIndex(found)


def _configure_product_combo(combo: ProductComboBox) -> None:
    combo.setInsertPolicy(QComboBox.NoInsert)
    combo.setMinimumContentsLength(20)
    combo.setMinimumHeight(30)
    combo.setFocusPolicy(Qt.StrongFocus)
    combo.view().setMinimumWidth(380)
    combo.view().setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)


def _configure_distance_editor(editor: QLineEdit) -> None:
    validator = QDoubleValidator(0.0, 9999.0, 2, editor)
    validator.setNotation(QDoubleValidator.StandardNotation)
    editor.setValidator(validator)
    editor.setAlignment(Qt.AlignCenter)
    editor.setFrame(False)


def _configure_qty_editor(editor: QSpinBox) -> None:
    editor.setRange(1, 999)
    editor.setFrame(False)
    editor.setAlignment(Qt.AlignCenter)
    editor.setButtonSymbols(QSpinBox.NoButtons)


def _paint_blank_editing_cell(delegate: QStyledItemDelegate, painter, option, index) -> bool:
    editing_index = getattr(delegate, "_editing_index", None)
    if editing_index is None or editing_index != QPersistentModelIndex(index):
        return False
    clean_option = QStyleOptionViewItem(option)
    delegate.initStyleOption(clean_option, index)
    clean_option.text = ""
    style = option.widget.style() if option.widget else QApplication.style()
    style.drawControl(QStyle.ControlElement.CE_ItemViewItem, clean_option, painter, option.widget)
    return True


def _editor_is_owned_by_view(editor: QWidget) -> bool:
    parent = editor.parentWidget()
    while parent is not None:
        if parent.metaObject().className() == "qt_scrollarea_viewport":
            return True
        parent = parent.parentWidget()
    return False


def _mark_editor_committed(editor: QWidget) -> bool:
    if editor.property("_codex_committed"):
        return False
    editor.setProperty("_codex_committed", True)
    return True


class DeviceProductDelegate(QStyledItemDelegate):
    """Product picker delegate for the Device column.

    Assumptions:
    - the model exposes the row category through `ROLE_ROW_KIND`
    - the model exposes the current product id through `ROLE_PRODUCT_ID`
    - the display text is the user-facing product label
    """

    def __init__(self, host: DeviceListDelegateHost, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.host = host
        self._editing_index: QPersistentModelIndex | None = None

    def _table_palette(self) -> dict[str, str]:
        main_app = getattr(self.host, "main_app", None)
        if main_app is not None and hasattr(main_app, "p"):
            return main_app.p
        if hasattr(self.host, "p"):
            return self.host.p
        return palette()

    def _commit_and_close(self, editor: QWidget) -> None:
        if editor is None or not _editor_is_owned_by_view(editor):
            return
        if not _mark_editor_committed(editor):
            return
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QStyledItemDelegate.NoHint)

    def createEditor(self, parent, option, index):  # type: ignore[override]
        combo = ProductComboBox(parent)
        _configure_product_combo(combo)
        combo.setStyleSheet(device_combo_style(self._table_palette()))
        combo.setAutoFillBackground(True)
        category = _index_data(index, ROLE_ROW_KIND, "Other")
        current_product_id = _index_data(index, ROLE_PRODUCT_ID)
        current_display_name = _index_data(index, Qt.DisplayRole, "")
        for product in self.host.product_db.product_options_by_category(str(category)):
            combo.add_product_option(product)
        _select_combo_item(combo, product_id=current_product_id, display_name=current_display_name)
        self._editing_index = QPersistentModelIndex(index)
        combo.activated.connect(lambda *_args, editor=combo: self._commit_and_close(editor))
        return combo

    def paint(self, painter, option, index):  # type: ignore[override]
        if self._editing_index is not None and self._editing_index == QPersistentModelIndex(index):
            clean_option = QStyleOptionViewItem(option)
            self.initStyleOption(clean_option, index)
            clean_option.text = ""
            style = option.widget.style() if option.widget else QApplication.style()
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, clean_option, painter, option.widget)
            return
        if not self._should_show_dropdown_hint(option, index):
            super().paint(painter, option, index)
            return

        clean_option = QStyleOptionViewItem(option)
        self.initStyleOption(clean_option, index)
        clean_option.text = ""
        style = option.widget.style() if option.widget else QApplication.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, clean_option, painter, option.widget)

        text_rect = option.rect.adjusted(12, 0, -28, 0)
        arrow_rect = option.rect.adjusted(option.rect.width() - 24, 0, -8, 0)
        palette = option.palette
        text_color = palette.highlightedText().color() if option.state & QStyle.State_Selected else palette.text().color()

        painter.save()
        painter.setPen(text_color)
        painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, str(index.data(Qt.DisplayRole) or ""))
        painter.drawText(arrow_rect, Qt.AlignVCenter | Qt.AlignHCenter, "▼")
        painter.restore()

    def _should_show_dropdown_hint(self, option, index) -> bool:
        view = option.widget
        if view is None or not hasattr(view, "currentIndex"):
            return False
        current_index = view.currentIndex()
        return bool(current_index.isValid() and current_index == index)

    def setEditorData(self, editor, index):  # type: ignore[override]
        if isinstance(editor, ProductComboBox):
            _select_combo_item(
                editor,
                product_id=_index_data(index, ROLE_PRODUCT_ID),
                display_name=_index_data(index, Qt.DisplayRole, ""),
            )

    def setModelData(self, editor, model, index):  # type: ignore[override]
        if not isinstance(editor, ProductComboBox):
            return
        option = editor.currentData(Qt.UserRole + 2) or {}
        payload = {
            "product_id": editor.currentData(),
            "display_name": editor.currentData(Qt.UserRole + 1) or "",
        }
        if isinstance(option, dict):
            payload.update(option)
        model.setData(index, payload, Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):  # type: ignore[override]
        editor.setGeometry(option.rect)

    def destroyEditor(self, editor, index):  # type: ignore[override]
        self._editing_index = None
        super().destroyEditor(editor, index)


class DeviceQtyDelegate(QStyledItemDelegate):
    """Quantity editor delegate for the Qty column.

    The future model can clamp or reject invalid values. The editor itself
    stays intentionally simple and predictable.
    """

    def __init__(self, host: DeviceListDelegateHost | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.host = host
        self._editing_index: QPersistentModelIndex | None = None

    def _table_palette(self) -> dict[str, str]:
        if self.host is not None:
            main_app = getattr(self.host, "main_app", None)
            if main_app is not None and hasattr(main_app, "p"):
                return main_app.p
            if hasattr(self.host, "p"):
                return self.host.p
        return palette()

    def _commit_and_close(self, editor: QWidget) -> None:
        if editor is None or not _editor_is_owned_by_view(editor):
            return
        if not _mark_editor_committed(editor):
            return
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QStyledItemDelegate.NoHint)

    def createEditor(self, parent, option, index):  # type: ignore[override]
        spin = QSpinBox(parent)
        _configure_qty_editor(spin)
        spin.setStyleSheet(table_spinbox_style(self._table_palette()))
        spin.setAutoFillBackground(True)
        self._editing_index = QPersistentModelIndex(index)
        spin.editingFinished.connect(lambda editor=spin: self._commit_and_close(editor))
        return spin

    def paint(self, painter, option, index):  # type: ignore[override]
        if _paint_blank_editing_cell(self, painter, option, index):
            return
        super().paint(painter, option, index)

    def setEditorData(self, editor, index):  # type: ignore[override]
        if isinstance(editor, QSpinBox):
            editor.setValue(int(_index_data(index, Qt.EditRole, 1) or 1))

    def setModelData(self, editor, model, index):  # type: ignore[override]
        if isinstance(editor, QSpinBox):
            model.setData(index, editor.value(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):  # type: ignore[override]
        editor.setGeometry(option.rect)

    def destroyEditor(self, editor, index):  # type: ignore[override]
        self._editing_index = None
        super().destroyEditor(editor, index)


class DeviceDistanceDelegate(QStyledItemDelegate):
    """Numeric distance editor delegate for lead/interval columns.

    Assumptions:
    - the model stores values as text or numbers that can be parsed as floats
    - the delegate should allow direct typing with minimal chrome
    """

    def __init__(self, host: DeviceListDelegateHost | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.host = host
        self._editing_index: QPersistentModelIndex | None = None

    def _table_palette(self) -> dict[str, str]:
        if self.host is not None:
            main_app = getattr(self.host, "main_app", None)
            if main_app is not None and hasattr(main_app, "p"):
                return main_app.p
            if hasattr(self.host, "p"):
                return self.host.p
        return palette()

    def _commit_and_close(self, editor: QWidget) -> None:
        if editor is None or not _editor_is_owned_by_view(editor):
            return
        if not _mark_editor_committed(editor):
            return
        self.commitData.emit(editor)
        self.closeEditor.emit(editor, QStyledItemDelegate.NoHint)

    def createEditor(self, parent, option, index):  # type: ignore[override]
        editor = QLineEdit(parent)
        _configure_distance_editor(editor)
        editor.setStyleSheet(table_lineedit_style(self._table_palette()))
        editor.setAutoFillBackground(True)
        self._editing_index = QPersistentModelIndex(index)
        editor.editingFinished.connect(lambda current=editor: self._commit_and_close(current))
        return editor

    def paint(self, painter, option, index):  # type: ignore[override]
        if _paint_blank_editing_cell(self, painter, option, index):
            return
        super().paint(painter, option, index)

    def setEditorData(self, editor, index):  # type: ignore[override]
        if isinstance(editor, QLineEdit):
            editor.setText(str(_index_data(index, Qt.EditRole, "") or ""))
            editor.selectAll()

    def setModelData(self, editor, model, index):  # type: ignore[override]
        if isinstance(editor, QLineEdit):
            model.setData(index, editor.text().strip(), Qt.EditRole)

    def updateEditorGeometry(self, editor, option, index):  # type: ignore[override]
        editor.setGeometry(option.rect)

    def destroyEditor(self, editor, index):  # type: ignore[override]
        self._editing_index = None
        super().destroyEditor(editor, index)
