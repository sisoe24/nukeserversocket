"""Text widgets that will log the connection state events."""
# coding: utf-8

from PySide2.QtWidgets import (QWidget, QGroupBox, QPushButton, QVBoxLayout,
                               QPlainTextEdit)

from ..util import insert_time
from ..settings import AppSettings


class LogBox(QGroupBox):
    """A custom QGroupBox that contains a QPlainTextEdit and a QPushButton."""

    _setting_key = 'hide_log'

    def __init__(self, title):
        """Init method for LogBox class."""
        QGroupBox.__init__(self, title)
        self.setCheckable(True)
        self.clicked.connect(self._update_visibility)

        self.text_box = QPlainTextEdit()
        self.text_box.setReadOnly(True)

        self._btn = QPushButton('Clear log')
        self._btn.clicked.connect(self.text_box.clear)

        _layout = QVBoxLayout()
        _layout.addWidget(self.text_box)
        _layout.addWidget(self._btn)

        self.setLayout(_layout)

        self._load_settings()

    def _get_setting_key(self):
        settings = AppSettings()
        key = '%s/%s' % (self._setting_key, self.title())
        return settings, key

    def _load_settings(self):
        """Load visibility status from settings file."""
        settings, key = self._get_setting_key()
        value = settings.get_bool(key, True)

        self.text_box.setHidden(value)
        self._btn.setHidden(value)
        self.setChecked(not value)

    def _update_visibility(self, state):  # type: (bool) -> None
        """Update the widget visibility.

        Hide/Unhide widget visibility if QGroupBox is checked.

        Args:
            state (bool): state of the QGroupBox.
        """
        settings, key = self._get_setting_key()
        settings.setValue(key, not state)

        self.text_box.setHidden(not state)
        self._btn.setHidden(not state)


def _logs_are_hidden():  # type: () -> bool
    """Check hide log settings value.

    Emit a signal with the status of all of the log visibility values. When
    value is True, means that all of the logs are hidden so the parent widget
    will insert a stretcher item to avoid breaking the layout.
    """
    settings = AppSettings()
    settings.beginReadArray(LogBox._setting_key)
    value = all(settings.get_bool(i) for i in settings.allKeys())
    settings.endArray()
    return value


class LogWidgets(QWidget):
    """Log Widget main layout class.

    This class consist of 3 LogBox QGroupBox: status, received, output inside a
    QVBoxLayout.
    """

    def __init__(self):
        """Init method for LogWidget class."""
        QWidget.__init__(self)
        self.status_widget = LogBox('Status')
        self.status_widget.clicked.connect(self._add_stretch)

        self.received_widget = LogBox('Received')
        self.received_widget.clicked.connect(self._add_stretch)

        self.output_widget = LogBox('Output')
        self.output_widget.clicked.connect(self._add_stretch)

        self._stretch_layout = QVBoxLayout()
        self._stretch_layout.addStretch()

        self._layout = QVBoxLayout()
        self._layout.addWidget(self.status_widget)
        self._layout.addWidget(self.received_widget)
        self._layout.addWidget(self.output_widget)

        self.setLayout(self._layout)
        self._add_stretch()

    def _add_stretch(self):
        """Add a stretch layout item bellow the widgets.

        When arg is True, add a stretch layout at the bottom layout, otherwise
        remove it.

        Args:
            value (bool): True to add a stretch, False to remove it.
        """
        if _logs_are_hidden():
            self._layout.addLayout(self._stretch_layout)
        else:
            self._layout.removeItem(self._stretch_layout)

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
        self._write_log(self.output_widget, str(text).strip())
