"""Test module for the Error dialog widget."""
import os
import logging

import pytest

from PySide2.QtGui import QClipboard

from src.widgets import error_dialog
from src.about import about_to_string


@pytest.fixture()
def error_log_path(_package):
    """Get the log directory path."""
    yield os.path.join(_package, 'src', 'log', 'errors.log')


@pytest.fixture(name='report')
def create_report(qtbot, error_log_path):
    """Initialize the ErrorDialog class and create an error report.

    After tests, will clean the error.logs file.

    Yields:
        Report: a namedtuple with the link and the port attributes.
    """
    widget = error_dialog.ErrorDialog('Test Error')
    qtbot.addWidget(widget)

    yield widget.prepare_report()

    with open(error_log_path, 'w') as _:
        pass


def test_report_return_value(report):
    """Check if prepare report return is a tuple."""
    assert isinstance(report, tuple)


def test_prepare_report_link(report):
    """Check if error dialog returns the issues link when clicking Report."""
    assert report.link == 'https://github.com/sisoe24/NukeServerSocket/issues'


def test_prepare_report_clipboard(report):
    """Check if report gets copied into clipboard."""
    assert 'NukeServerSocket' in QClipboard().text()


def test_prepare_report_file(report, error_log_path):
    """Check if the report file has the about to string information."""
    with open(error_log_path) as file:
        assert about_to_string() in file.read()


def test_get_critical_logger():
    """Check if method returns the critical logger file handler."""
    logger = error_dialog._get_critical_logger()
    assert logger.name == 'Critical'
    assert isinstance(logger, logging.FileHandler)
