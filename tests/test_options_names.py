"""Test configuration options name written in various files.

Settings key are referenced with a string and usually if no settings is
found, will be replaced with a default value. If then a string is misspelled
its going to hard to debug.
"""
import os
import re

import pytest

from src.widgets import settings_widget


@pytest.fixture()
def options_name(qtbot):
    """Get the options name from the SettingsWidget."""
    settings = settings_widget.SettingsWidget()
    checkboxes = settings.findChildren(settings_widget.CheckBox)
    return [x.text().lower().replace(' ', '_') for x in checkboxes]


def traverse_dir(package):
    """Traverse the package directory in search for a python file."""
    for dirpath, _, filenames in os.walk(package):
        for filename in filenames:
            if filename.endswith('py'):
                fp = os.path.join(dirpath, filename)
                yield fp


# TODO: make this parametrized

def test_options_names(package, options_name):
    """Test that options name are valid.

    Search for the files that are using the settings system, and confirm that
    the options name are valid.
    """
    for file in traverse_dir(package):
        with open(file) as f:
            content = f.read()
            if re.search(r'AppSettings', content):
                opts = re.findall(r'(?<=options/)\w+', content)
                for opt in opts:
                    msg = 'Option name was not update in file: {}'.format(file)
                    assert opt in options_name, msg
