from __future__ import annotations

from typing import Any, Protocol

from PySide6.QtCore import QPersistentModelIndex, Qt
from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QApplication, QLineEdit, QMessageBox, QStyle, QStyledItemDelegate, QStyleOptionViewItem


class TranslationHost(Protocol):
    def t(self, key: str, **kwargs: Any) -> str: ...


class NumericDelegate(QStyledItemDelegate):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._editing_index: QPersistentModelIndex | None = None

    def createEditor(self, parent, option, index):  # type: ignore[override]
        editor = QLineEdit(parent)
        validator = QDoubleValidator(0.0, 9999.0, 2, editor)
        validator.setNotation(QDoubleValidator.StandardNotation)
        editor.setValidator(validator)
        editor.setAlignment(Qt.AlignCenter)
        editor.setFrame(False)
        editor.setStyleSheet("border: none; background: transparent; padding: 0; margin: 0;")
        self._editing_index = QPersistentModelIndex(index)
        return editor

    def paint(self, painter, option, index):  # type: ignore[override]
        if self._editing_index is not None and self._editing_index == QPersistentModelIndex(index):
            clean_option = QStyleOptionViewItem(option)
            self.initStyleOption(clean_option, index)
            clean_option.text = ""
            style = option.widget.style() if option.widget else QApplication.style()
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, clean_option, painter, option.widget)
            return
        super().paint(painter, option, index)

    def destroyEditor(self, editor, index):  # type: ignore[override]
        self._editing_index = None
        super().destroyEditor(editor, index)


class PlainTextDelegate(QStyledItemDelegate):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._editing_index: QPersistentModelIndex | None = None

    def createEditor(self, parent, option, index):  # type: ignore[override]
        editor = QLineEdit(parent)
        editor.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        editor.setFrame(False)
        editor.setStyleSheet("border: none; background: transparent; padding: 0; margin: 0;")
        self._editing_index = QPersistentModelIndex(index)
        return editor

    def paint(self, painter, option, index):  # type: ignore[override]
        if self._editing_index is not None and self._editing_index == QPersistentModelIndex(index):
            clean_option = QStyleOptionViewItem(option)
            self.initStyleOption(clean_option, index)
            clean_option.text = ""
            style = option.widget.style() if option.widget else QApplication.style()
            style.drawControl(QStyle.ControlElement.CE_ItemViewItem, clean_option, painter, option.widget)
            return
        super().paint(painter, option, index)

    def destroyEditor(self, editor, index):  # type: ignore[override]
        self._editing_index = None
        super().destroyEditor(editor, index)


def set_message_box_texts(box: QMessageBox, owner: TranslationHost) -> None:
    for role, key in ((QMessageBox.Yes, 'yes'), (QMessageBox.No, 'no'), (QMessageBox.Ok, 'confirm')):
        button = box.button(role)
        if button:
            button.setText(owner.t(key))


def maybe_recalc_window(widget: Any) -> None:
    window = widget.window() if hasattr(widget, 'window') else None
    if window and hasattr(window, '_recalc_global_battery'):
        window._recalc_global_battery()
