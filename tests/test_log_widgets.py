import re
from PySide2.QtWidgets import QGroupBox

from collections import namedtuple
import pytest

from src.widgets import LogWidgets


@pytest.fixture()
def log_obj():
    logs = LogWidgets()
    print("➡ logs :", logs)
    yield logs

    for box in logs.findChildren(QGroupBox):
        box.text_box.clear()


log_methods = (
    'set_status_text',
    'set_received_text',
    'set_output_text',
)


@pytest.mark.parametrize('log_methods', log_methods, ids=['status', 'received', 'output'])
def test_log_widgets(log_methods, log_obj):
    """Test that log widgets receive text.

    This method is a bit of a hack for no good reason. should change it. 
    """
    set_method = getattr(log_obj, log_methods)
    set_method(log_methods)

    log_output = getattr(log_obj, log_methods.replace('set_', ''))
    assert re.match(r'\[\d\d:\d\d:\d\d\] ' + log_methods, log_output)