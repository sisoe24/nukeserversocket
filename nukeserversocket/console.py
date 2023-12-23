from __future__ import annotations

import logging

from PySide2.QtCore import Slot
from PySide2.QtWidgets import (QFrame, QLabel, QCheckBox, QPushButton,
                               QVBoxLayout, QPlainTextEdit)

from .logger import get_logger


class _ConsoleHandler(logging.Handler):
    def __init__(self, console: NssConsole) -> None:
        super().__init__()
        self.setLevel(logging.INFO)
        self.setFormatter(
            logging.Formatter(
                '[%(asctime)s] %(levelname)-8s - %(message)s', '%H:%M:%S'
            )
        )
        self._console = console

    def emit(self, record: logging.LogRecord) -> None:
        self._console.write(self.format(record) + '\n')


class NssConsole(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        # self.setFrameStyle(QFrame.StyledPanel )
        # self.setStyleSheet("QFrame {background-color: #3B3B3B;}")

        self._console_handler = _ConsoleHandler(self)
        get_logger().addHandler(self._console_handler)

        self._console = QPlainTextEdit()
        self._console.setStyleSheet('font-family: menlo;')
        self._enable_debug = QCheckBox('Enable Debug')
        self._enable_debug.stateChanged.connect(self._on_enable_debug)

        # self._console.setStyleSheet("QPlainTextEdit {background-color: #FFFFFF}")
        self._console.setReadOnly(True)

        self.clear_logs_btn = QPushButton('Clear Logs')
        self.clear_logs_btn.clicked.connect(self._console.clear)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('<h3>Logs</h3>'))
        layout.addWidget(self._enable_debug)
        layout.addWidget(self._console)
        layout.addWidget(self.clear_logs_btn)

        self.setLayout(layout)

    @Slot(int)
    def _on_enable_debug(self, state: int) -> None:
        self._console_handler.setLevel(
            logging.DEBUG if state == 2 else logging.INFO
        )

    def write(self, text: str) -> None:
        self._console.insertPlainText(f'{text}')
        self._console.verticalScrollBar().setValue(
            self._console.verticalScrollBar().maximum()
        )
