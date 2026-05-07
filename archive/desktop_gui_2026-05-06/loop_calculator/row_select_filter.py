from __future__ import annotations

from PySide6.QtCore import QEvent, QItemSelectionModel, QObject, QPoint, Qt
from PySide6.QtWidgets import QAbstractItemView


class RowSelectFilter(QObject):
    """Event filter installed on widgets embedded in table cells (ComboBox,
    SpinBox) so that clicking them also triggers row selection on the parent
    table, respecting Ctrl / Shift modifiers for multi-select."""

    def __init__(self, table):
        super().__init__(table)
        self.table = table

    def eventFilter(self, obj, event):
        if event.type() != QEvent.MouseButtonPress or event.button() != Qt.LeftButton:
            return False

        viewport = self.table.viewport()
        pos = obj.mapTo(viewport, QPoint(1, 1))
        index = self.table.indexAt(pos)
        if not index.isValid():
            return False

        model = self.table.selectionModel()
        if model is None:
            return False

        row_index = self.table.model().index(index.row(), 0)
        modifiers = event.modifiers()

        if modifiers & Qt.ControlModifier:
            # Ctrl+click: toggle this row without affecting others
            flags = QItemSelectionModel.Rows | QItemSelectionModel.Toggle
            model.select(row_index, flags)
        elif modifiers & Qt.ShiftModifier:
            # Shift+click: extend selection from current to this row
            flags = QItemSelectionModel.Rows | QItemSelectionModel.Select
            current = model.currentIndex()
            if current.isValid():
                start = min(current.row(), index.row())
                end = max(current.row(), index.row())
                model.clearSelection()
                for r in range(start, end + 1):
                    model.select(
                        self.table.model().index(r, 0),
                        QItemSelectionModel.Rows | QItemSelectionModel.Select,
                    )
            else:
                model.select(row_index, flags)
        else:
            # Plain click: select only this row, clear others
            flags = QItemSelectionModel.Rows | QItemSelectionModel.ClearAndSelect
            model.select(row_index, flags)

        model.setCurrentIndex(row_index, QItemSelectionModel.NoUpdate)
        return False
