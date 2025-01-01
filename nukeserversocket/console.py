from __future__ import annotations

import sys
import logging
from typing import Optional

from PySide2.QtCore import Slot
from PySide2.QtWidgets import (QWidget, QCheckBox, QGroupBox, QHBoxLayout,
                               QPushButton, QVBoxLayout, QPlainTextEdit)

from .logger import get_logger

LOGGER = get_logger()

LOG_COLORS = {
    'DEBUG': 'aqua',
    'INFO': 'white',
    'WARNING': 'orange',
    'ERROR': 'red',
    'CRITICAL': 'magenta',
}


class NssConsole(QGroupBox):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent, title='Logs')

        self._console = QPlainTextEdit()

        if sys.platform == 'darwin':
            font = 'menlo'
        elif sys.platform == 'win32':
            font = 'consolas'
        else:
            font = 'monospace'

        self._console.setStyleSheet(f'font-family: {font};')
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
        LOGGER.console.setLevel(logging.DEBUG if state == 2 else logging.INFO)

    def write(self, text: str, level_name: str = 'INFO') -> None:
        color = LOG_COLORS.get(level_name, 'white')
        text = text.replace(' ', '&nbsp;')
        self._console.appendHtml(f'<font color="{color}">{text}</font>')
        self._console.verticalScrollBar().setValue(
            self._console.verticalScrollBar().maximum()
        )
