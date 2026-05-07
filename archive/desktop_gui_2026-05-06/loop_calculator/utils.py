"""Utility helpers and Qt delegates for the loop calculator."""

from __future__ import annotations

from PySide6.QtGui import QDoubleValidator
from PySide6.QtWidgets import QLineEdit, QMessageBox, QStyledItemDelegate


class NumericDelegate(QStyledItemDelegate):
    """Delegate that limits cell editing to decimal numbers."""

    def createEditor(self, parent, option, index):  # noqa: N802 - Qt API signature
        editor = QLineEdit(parent)
        validator = QDoubleValidator(0.0, 9999.0, 2, editor)
        validator.setNotation(QDoubleValidator.StandardNotation)
        editor.setValidator(validator)
        return editor


def set_message_box_texts(box: QMessageBox, owner) -> None:
    """Apply localized labels to standard message box buttons."""

    for role, key in ((QMessageBox.Yes, "yes"), (QMessageBox.No, "no"), (QMessageBox.Ok, "confirm")):
        button = box.button(role)
        if button:
            button.setText(owner.t(key))
