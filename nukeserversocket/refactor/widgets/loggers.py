from __future__ import annotations

from datetime import datetime

from PySide2.QtCore import Slot
from PySide2.QtWidgets import (QFrame, QLabel, QWidget, QToolBox, QGroupBox,
                               QLineEdit, QPushButton, QVBoxLayout,
                               QPlainTextEdit)


class LogWidget(QWidget):
    """A custom QGroupBox that contains a QPlainTextEdit and a QPushButton."""

    def __init__(self, parent=None):
        """Init method for LogBox class."""
        super().__init__()

        self.text_box = QPlainTextEdit()
        self.text_box.setReadOnly(True)

        self._btn = QPushButton('Clear log')
        self._btn.clicked.connect(self.text_box.clear)

        layout = QVBoxLayout()
        layout.addWidget(self.text_box)
        layout.addWidget(self._btn)

        self.setLayout(layout)

    def write(self, text: str):
        time = datetime.now().strftime('%H:%M:%S')
        self.text_box.appendPlainText(f'[{time}] {text}')

    def text(self):
        return self.text_box.toPlainText()


class LogWidgets(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.status_widget = LogWidget('Status')

        self.search_widget = QLineEdit()
        self.search_widget.setPlaceholderText('Search...')
        self.search_widget.textChanged.connect(self._on_search_text_changed)

        loggers = QToolBox()
        loggers.addItem(self.status_widget, 'Status')

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Logs'))
        # layout.addWidget(self.search_widget)
        layout.addWidget(self.status_widget)
        self.setLayout(layout)

    @Slot(str)
    def _on_search_text_changed(self, text: str):
        self.status_widget.text_box.find(text)
