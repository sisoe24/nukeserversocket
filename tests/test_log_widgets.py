"""Test log widgets."""
import re
from PySide2.QtWidgets import QGroupBox

import pytest

from src.widgets import LogWidgets


@pytest.fixture()
def log_obj(qtbot):
    """Create a log widget object.

    After tests, will clear the log text.
    """
    logs = LogWidgets()
    qtbot.addWidget(logs)

    yield logs

    for box in logs.findChildren(QGroupBox):
        box.text_box.clear()


@pytest.mark.parametrize('log_methods',
                         ('set_status_text',
                          'set_received_text',
                          'set_output_text'),
                         ids=['status', 'received', 'output'])
def test_log_widgets(log_methods, log_obj):
    """Test that log widgets receive text.

    This method is a bit of a hack for no good reason. should change it.
    """
    set_method = getattr(log_obj, log_methods)
    set_method(log_methods)

    log_output = getattr(log_obj, log_methods.replace('set_', ''))
    assert re.match(r'\[\d\d:\d\d:\d\d\] ' + log_methods, log_output)
