"""Test log widgets."""
import re
from PySide2.QtWidgets import QGroupBox

import pytest

from src.widgets import LogWidgets


@pytest.fixture()
def _log_widget(qtbot):
    """Create a log widget object.

    After tests, will clear the log text.
    """
    logs = LogWidgets()
    qtbot.addWidget(logs)

    yield logs

    for box in logs.findChildren(QGroupBox):
        box.text_box.clear()


def match_log_text(text, string):
    """Match the log text output format."""
    return re.match(r'\[\d\d:\d\d:\d\d\] ' + text, string)


def test_status_widget(_log_widget):
    """Check the status log widget text."""
    _log_widget.set_status_text('hello')
    assert match_log_text('hello', _log_widget.status_text)


def test_received_widget(_log_widget):
    """Check the received log widget text."""
    _log_widget.set_received_text('hello')
    assert match_log_text('hello', _log_widget.received_text)


def test_output_widget(_log_widget):
    """Check the output log widget text."""
    _log_widget.set_output_text('hello')
    assert match_log_text('hello', _log_widget.output_text)
