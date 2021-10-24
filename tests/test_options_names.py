"""Test configuration options name written in various files.

Settings key are referenced with a string and usually if no settings is
found, will be replaced with a default value. If then a string is misspelled
its going to hard to debug.
"""
import os
import re

import pytest

from src.widgets import settings_widget


def _uses_settings(file):
    """Check if file imports AppSettings class.

    Returns:
        bool: True if it does, False otherwise.
    """
    with open(file) as src_file:
        return bool(re.search('AppSettings', src_file.read()))


def _traverse_dir(package):
    """Traverse the package directory in search for a python file."""
    for dirpath, _, filenames in os.walk(package):
        for filename in filenames:
            fp = os.path.join(dirpath, filename)
            if filename.endswith('py') and _uses_settings(fp):
                yield fp


def _get_options_keys(file):
    """Get all of the options reference inside the source file.

    Returns:
        list: list with all of the options reference found.
    """
    with open(file) as src_file:
        return re.findall(r'(?<=options/)\w+', src_file.read())


@pytest.fixture()
def options_name(qtbot):
    """Get the options name from the SettingsWidget."""
    widget = settings_widget.SettingsWidget()
    qtbot.addWidget(widget)

    checkboxes = widget.findChildren(settings_widget.CheckBox)
    return [x.text().lower().replace(' ', '_') for x in checkboxes]


def test_options_names(package, options_name):
    """Test that options name are valid.

    Search for the files that are using the setting system, and confirm that
    names are valid.
    """
    for file in _traverse_dir(package):
        for opt in _get_options_keys(file):
            msg = 'Option name was not update in file: {}'.format(file)
            assert opt in options_name, msg
