"""Test SettingsWidget class."""
import configparser

import pytest
from PySide2.QtWidgets import QCheckBox

from src.widgets import settings_widget


@pytest.fixture()
def _settings(qtbot, tmp_settings_file):
    """Initialize the SettingsWidget class."""
    widget = settings_widget.SettingsWidget()
    qtbot.addWidget(widget)

    yield widget


def test_output_console_is_true(_settings):
    """Test output_to_console enabled settings.

    If `console_output` is enable, so it should be for `clear_text` and
    `format_output`.
    """
    _settings._output_console.setChecked(True)

    assert _settings._clear_output.isChecked()
    assert _settings._format_output.isChecked()


def test_output_console_is_false(_settings):
    """Test console_output disabled settings.

    If `console_output` is disabled, so it should be for `clear_text` and
    `format_output`.
    """
    _settings._output_console.setChecked(False)

    assert not _settings._format_output.isChecked()
    assert not _settings._format_output.isEnabled()

    assert not _settings._clear_output.isChecked()
    assert not _settings._clear_output.isEnabled()


def test_format_text_is_false(_settings):
    """Test format text disabled setting.

    If `format_text` is disabled so it should be for `clear_text`.
    """
    _settings._output_console.setChecked(True)
    _settings._format_output.setChecked(False)

    assert not _settings._clear_output.isEnabled()
    assert not _settings._clear_output.isChecked()


@pytest.fixture()
def _toggle_options(_settings):
    """Toggle all options to True state."""
    for checkbox in _settings.findChildren(QCheckBox):
        checkbox.toggle()
        checkbox.setChecked(True)


def test_check_value(_toggle_options, tmp_settings_file):
    """Check if checkboxes saved their state on the file settings.

    All values should be True because tests call fixture which toggles all
    of them to True.
    """
    config = configparser.ConfigParser()
    config.read(tmp_settings_file)

    settings_values = config['options']

    for opt in settings_values:
        assert config.getboolean('options', opt)


def test_no_settings_default_values(_settings):
    """Check checkbox default values.

    If no settings.ini is found, checkbox should start with a default value.
    """
    initial_values = {
        'output_to_console': True,
        'format_text': True,
        'clear_output': True,
        'override_input_editor': False,
        'show_file_path': False,
        'show_unicode': True,
    }

    for checkbox in _settings.findChildren(QCheckBox):
        value = initial_values[checkbox.objectName()]
        assert checkbox.isChecked() == value
