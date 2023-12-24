from __future__ import annotations

import logging

from PySide2.QtCore import Slot
from PySide2.QtWidgets import (QCheckBox, QGroupBox, QHBoxLayout, QPushButton,
                               QVBoxLayout, QPlainTextEdit)

LOGGER = logging.getLogger('nukeserversocket')


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


class NssConsole(QGroupBox):
    def __init__(self, parent=None):
        super().__init__(parent, title='Logs')

        self._console_handler = _ConsoleHandler(self)
        LOGGER.addHandler(self._console_handler)

        self._console = QPlainTextEdit()
        self._console.setStyleSheet('font-family: menlo;')
        self._console.setReadOnly(True)
        self._console.setLineWrapMode(QPlainTextEdit.NoWrap)

        self._enable_debug = QCheckBox('Enable Debug')
        self._enable_debug.stateChanged.connect(self._on_enable_debug)

        self._wrap_lines = QCheckBox('Wrap Lines')
        self._wrap_lines.stateChanged.connect(
            lambda state: self._console.setLineWrapMode(
                QPlainTextEdit.WidgetWidth if state == 2 else QPlainTextEdit.NoWrap
            )
        )

        self.clear_logs_btn = QPushButton('Clear Logs')
        self.clear_logs_btn.clicked.connect(self._console.clear)

        top_layout = QHBoxLayout()
        top_layout.addWidget(self._enable_debug)
        top_layout.addWidget(self._wrap_lines)
        top_layout.addStretch()
        top_layout.addWidget(self.clear_logs_btn)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self._console)

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
