"""Text widgets that will log the connection state events."""
# coding: utf-8
from __future__ import print_function

from PySide2.QtWidgets import (QWidget, QGroupBox, QPushButton, QVBoxLayout,
                               QPlainTextEdit)

from ..util import insert_time


class LogBox(QGroupBox):
    """A custom QGroupBox that contains a QPlainTextEdit and a QPushButton."""

    def __init__(self, title):
        """Init method for LogBox class."""
        QGroupBox.__init__(self, title)

        self.text_box = QPlainTextEdit()
        self.text_box.setReadOnly(True)

        btn = QPushButton('Clear log')
        btn.clicked.connect(self.text_box.clear)

        _layout = QVBoxLayout()
        _layout.addWidget(self.text_box)
        _layout.addWidget(btn)

        self.setLayout(_layout)


class LogWidgets(QWidget):
    """Log Widget main layout class.

    This class consist of 3 LogBox QGroupBox: status, received, output inside a
    QVBoxLayout.
    """

    def __init__(self):
        """Init method for LogWidget class."""
        QWidget.__init__(self)
        self.status_widget = LogBox('Status')
        self.received_widget = LogBox('Received')
        self.output_widget = LogBox('Output')

        _layout = QVBoxLayout()
        _layout.addWidget(self.status_widget)
        _layout.addWidget(self.received_widget)
        _layout.addWidget(self.output_widget)

        self.setLayout(_layout)

    @property
    def status_text(self):
        """Get the status widget text."""
        return self.status_widget.text_box.toPlainText()

    @property
    def received_text(self):
        """Get the received widget text."""
        return self.received_widget.text_box.toPlainText()

    @property
    def output_text(self):
        """Get the output widget text."""
        return self.output_widget.text_box.toPlainText()

    @staticmethod
    def _write_log(widget, text):  # type: (LogBox, str) -> None
        """Write text into the appropriate widget.

        Once the text is inserted, will update the cursor position to move down
        as more text is inserted.

        Args:
            widget (LogBox): LogBox widget class to write the text.
            text ([type]): text to
        """
        widget.text_box.insertPlainText(insert_time(text))
        widget.text_box.ensureCursorVisible()

    def set_status_text(self, text):  # type: (str) -> None
        """Write text into the status log box."""
        self._write_log(self.status_widget, text)

    def set_received_text(self, text):  # type: (str) -> None
        """Write text into the received log box."""
        self._write_log(self.received_widget, text)

    def set_output_text(self, text):  # type: (str) -> None
        """Write text into the output log box."""
        text = str(text).strip()
        self._write_log(self.output_widget, text)
