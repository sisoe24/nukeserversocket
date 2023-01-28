"""Test module for the Error dialog widget."""
import os

import pytest
from PySide2.QtGui import QClipboard

from src.about import about_to_string
from src.widgets import error_dialog


@pytest.fixture()
def _error_log_path(_package):
    """Get the log directory path."""
    yield os.path.join(_package, 'src', 'logs', 'errors.log')


@pytest.fixture(name='report')
def create_report(qtbot, _error_log_path):
    """Initialize the ErrorDialog class and create an error report.

    After tests, will clean the error.logs file.

    Yields:
        Report: a namedtuple with the link and the port attributes.
    """
    widget = error_dialog.ErrorDialog('Test Error')
    qtbot.addWidget(widget)

    yield widget._prepare_report()


def test_prepare_report_clipboard(report):
    """Check if report gets copied into clipboard."""
    assert about_to_string() in QClipboard().text()
