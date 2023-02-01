"""Test configuration options name written in various files.

Settings key are referenced with a string and usually if no settings is
found, will be replaced with a default value. If then a string is misspelled
its going to hard to debug.
"""
import os
import re

import pytest
from PySide2.QtWidgets import QCheckBox, QRadioButton

from nukeserversocket.widgets.settings_widget import (SettingsWidget,
                                                      _format_name,
                                                      _ScriptEditorSettings)

pytestmark = pytest.mark.settings_name


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
    # TODO: this will not find the names in the test_settings_widget.py file.
    with open(file) as src_file:
        return re.findall(r'(?<=options/)\w+', src_file.read())


def _get_engine_keys(file):
    """Get all of the options reference inside the source file.

    Returns:
        list: list with all of the options reference found.
    """
    # TODO: this will not find the names in the test_settings_widget.py file.
    with open(file) as src_file:
        return re.findall(r'(?<=code_execution_engine/)\w+', src_file.read())


def _format_name(name):
    """Format name.

    Format a name into lowercase and no space: `This Button` to `this_button`.

    Args:
        name (str): name to be formatted

    Returns:
        str: the formatted name.
    """
    return name.lower().replace(' ', '_')


@pytest.fixture()
def _options_name(qtbot):
    """Get the options name from the SettingsWidget."""
    widget = SettingsWidget()
    qtbot.addWidget(widget)

    checkboxes = widget.findChildren(QCheckBox)
    options_names = [_format_name(_.text()) for _ in checkboxes]

    # add the groupbox title name since it being used as a setting value
    options_names.append(_format_name(
        _ScriptEditorSettings().title()))

    return options_names


@pytest.fixture()
def _engine_name(qtbot):
    """Get the options name from the SettingsWidget."""
    widget = SettingsWidget()
    qtbot.addWidget(widget)

    radio_buttons = widget.findChildren(QRadioButton)
    return [_format_name(_.text()) for _ in radio_buttons]


def test_engine_names(_package, _engine_name):
    """Test that options name are valid.

    Search for the files that are using the setting system, and confirm that
    names are valid.
    """
    for file in _traverse_dir(_package):
        for opt in _get_engine_keys(file):
            msg = 'Option name was not update in file: {}'.format(file)
            assert opt in _engine_name, msg


def test_options_names(_package, _options_name):
    """Test that options name are valid.

    Search for the files that are using the setting system, and confirm that
    names are valid.
    """
    for file in _traverse_dir(_package):
        for opt in _get_options_keys(file):
            msg = 'Option name was not update in file: {}'.format(file)
            assert opt in _options_name, msg
