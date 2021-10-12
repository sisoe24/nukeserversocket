import os
import logging

import pytest

from PySide2.QtGui import QClipboard

from src.widgets import error_dialog
from src.about import about_to_string


@pytest.fixture()
def log_path(package):
    """Get the log directory path"""
    yield os.path.join(package, 'src', 'log')


def test_error_dialog_prepare_report(qtbot):
    """Check if error dialog returns the issues path when clicking Report bug."""
    widget = error_dialog.ErrorDialog('Test Error')
    qtbot.addWidget(widget)

    to_open = widget.prepare_report()
    assert to_open == 'https://github.com/sisoe24/NukeServerSocket/issues'
    assert 'NukeServerSocket' in QClipboard().text()


def test_prepare_port(log_path):
    """Check if the report has the about to string information."""
    with open(os.path.join(log_path, 'errors.log')) as file:
        assert about_to_string() in file.read()


def test_error_dialog_open_logs(qtbot, log_path):
    """Check if error dialog returns the log path when clicking Logs."""
    widget = error_dialog.ErrorDialog('Test Error')
    qtbot.addWidget(widget)

    to_open = widget.open_logs_path()
    assert log_path in to_open


def test_get_critical_logger():
    """Get the critical logger."""
    logger = error_dialog._get_critical_logger()
    assert logger.name == 'Critical'
    assert isinstance(logger, logging.FileHandler)
