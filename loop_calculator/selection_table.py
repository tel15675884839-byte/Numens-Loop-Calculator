from __future__ import annotations

from PySide6.QtCore import QPersistentModelIndex, QTimer, Qt, Signal
from PySide6.QtGui import QMouseEvent
from PySide6.QtCore import QItemSelectionModel
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QStyle, QStyledItemDelegate, QTableView, QTableWidget


class NoHoverDelegate(QStyledItemDelegate):
    """Item delegate that strips the State_MouseOver flag before painting,
    ensuring no hover highlight is ever drawn by the native style engine."""

    def initStyleOption(self, option, index):
        super().initStyleOption(option, index)
        # Remove the hover (mouse-over) state so the native painter
        # never draws a hover highlight row/cell.
        option.state &= ~QStyle.StateFlag.State_MouseOver


class StableMultiSelectTable(QTableWidget):
    selected_rows_changed = Signal(set)

    def __init__(self, rows: int = 0, columns: int = 0, parent=None):
        super().__init__(rows, columns, parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._selected_rows_cache: set[int] = set()
        self.itemSelectionChanged.connect(self._emit_selected_rows)
        # Install the no-hover delegate so the native style engine never
        # paints a hover highlight on any cell.
        self.setItemDelegate(NoHoverDelegate(self))

    def _emit_selected_rows(self) -> None:
        rows = {index.row() for index in self.selectionModel().selectedRows()} if self.selectionModel() else set()
        if rows == self._selected_rows_cache:
            return
        self._selected_rows_cache = set(rows)
        self.selected_rows_changed.emit(set(rows))


class StableMultiSelectView(QTableView):
    selected_rows_changed = Signal(set)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self._selected_rows_cache: set[int] = set()
        self._dropdown_columns: set[int] = set()
        self.setItemDelegate(NoHoverDelegate(self))

    def setModel(self, model):  # type: ignore[override]
        current = self.selectionModel()
        if current is not None:
            try:
                current.selectionChanged.disconnect(self._emit_selected_rows)
            except Exception:
                pass
        super().setModel(model)
        new_selection = self.selectionModel()
        if new_selection is not None:
            new_selection.selectionChanged.connect(self._emit_selected_rows)

    def _emit_selected_rows(self, *_args) -> None:
        selection_model = self.selectionModel()
        rows = {index.row() for index in selection_model.selectedRows()} if selection_model else set()
        if rows == self._selected_rows_cache:
            return
        self._selected_rows_cache = set(rows)
        self.selected_rows_changed.emit(set(rows))

    def set_dropdown_columns(self, columns: set[int] | list[int] | tuple[int, ...]) -> None:
        self._dropdown_columns = {int(column) for column in columns}

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # type: ignore[override]
        index = self.indexAt(event.pos())
        was_current = bool(index.isValid() and self.currentIndex() == index)
        is_dropdown_click = bool(index.isValid() and index.column() in self._dropdown_columns and self._arrow_hit_rect(index).contains(event.pos()))

        super().mouseReleaseEvent(event)

        if event.button() != Qt.LeftButton or not index.isValid() or not was_current:
            return
        if not (self.model() and (self.model().flags(index) & Qt.ItemIsEditable)):
            return
        if index.column() in self._dropdown_columns:
            if not is_dropdown_click:
                return
            self.edit(index)
            QTimer.singleShot(0, lambda current=QPersistentModelIndex(index): self._show_combo_popup(current))
            return
        self.edit(index)

    def _arrow_hit_rect(self, index) -> object:
        rect = self.visualRect(index)
        return rect.adjusted(max(0, rect.width() - 28), 0, -4, 0)

    def _show_combo_popup(self, index: QPersistentModelIndex) -> None:
        if not index.isValid():
            return
        for combo in self.findChildren(QComboBox):
            if combo.isVisible():
                combo.showPopup()
                return
