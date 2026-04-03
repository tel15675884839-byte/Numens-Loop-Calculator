from __future__ import annotations

import sys

from PySide6.QtCore import QtMsgType, qInstallMessageHandler
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QApplication

from loop_calculator.main_window import CIEMainWindow


def _install_qt_warning_filter() -> None:
    previous = qInstallMessageHandler(None)

    def handler(msg_type: QtMsgType, context, message: str) -> None:
        if "QFont::setPointSize: Point size <= 0 (-1)" in message:
            return
        if previous:
            previous(msg_type, context, message)
            return
        sys.stderr.write(message + "\n")

    qInstallMessageHandler(handler)


def main() -> int:
    _install_qt_warning_filter()
    app = QApplication.instance() or QApplication(sys.argv)
    app.setFont(QFont('Segoe UI', 9))
    window = CIEMainWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    raise SystemExit(main())
