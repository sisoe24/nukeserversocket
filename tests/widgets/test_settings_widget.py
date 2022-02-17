"""Test ScriptEditorSettings class."""
import configparser

import pytest
from PySide2.QtWidgets import QCheckBox

from src.widgets.settings_widget import ScriptEditorSettings, CheckBox


@pytest.fixture()
def _settings(qtbot, _tmp_settings_file):
    """Initialize the ScriptEditorSettings class."""
    widget = ScriptEditorSettings()
    qtbot.addWidget(widget)

    yield widget


def is_enabled(widget):  # type: (CheckBox) -> None
    """Check if CheckBox widget is enabled."""
    assert widget.isEnabled()
    assert widget.isChecked()


def is_disabled(widget):  # type: (CheckBox) -> None
    """Check if CheckBox widget is disabled."""
    assert not widget.isEnabled()
    assert not widget.isChecked()


def test_all_options_are_enabled(_settings):  # type: (ScriptEditorSettings) -> None
    """Test output_to_console enabled settings.

    If `console_output` is enable, so it should be for `clear_text` and
    `format_output`.
    """
    _settings.setChecked(False)
    _settings.setChecked(True)

    is_enabled(_settings._output_console)
    is_enabled(_settings._format_output)
    is_enabled(_settings._clear_output)
    is_enabled(_settings._show_path)
    is_enabled(_settings._show_unicode)
    is_enabled(_settings._override_input)


def test_all_options_are_disabled(_settings):  # type: (ScriptEditorSettings) -> None
    """Test output_to_console enabled settings.

    If `console_output` is enable, so it should be for `clear_text` and
    `format_output`.
    """
    _settings.setChecked(True)
    _settings.setChecked(False)

    is_disabled(_settings._output_console)
    is_disabled(_settings._format_output)
    is_disabled(_settings._clear_output)
    is_disabled(_settings._show_path)
    is_disabled(_settings._show_unicode)
    is_disabled(_settings._override_input)


def test_output_console_is_true(_settings):  # type: (ScriptEditorSettings) -> None
    """Test output_to_console enabled settings.

    If `console_output` is enable, so it should be for `clear_text` and
    `format_output`.
    """
    _settings._output_console.setChecked(False)
    _settings._output_console.setChecked(True)

    is_enabled(_settings._format_output)
    is_enabled(_settings._clear_output)
    is_enabled(_settings._show_path)
    is_enabled(_settings._show_unicode)


def test_output_console_is_false(_settings):  # type: (ScriptEditorSettings) -> None
    """Test console_output disabled settings.

    If `console_output` is disabled, so it should be for the other sub options.
    """
    _settings._output_console.setChecked(True)
    _settings._output_console.setChecked(False)

    is_disabled(_settings._format_output)
    is_disabled(_settings._clear_output)
    is_disabled(_settings._show_path)
    is_disabled(_settings._show_unicode)


def test_format_text_is_false(_settings):  # type: (ScriptEditorSettings) -> None
    """Test format text disabled setting.

    If `format_text` is disabled so it should be for other sub options.
    """
    _settings._output_console.setChecked(True)
    _settings._format_output.setChecked(False)

    is_disabled(_settings._clear_output)
    is_disabled(_settings._show_path)
    is_disabled(_settings._show_unicode)


@pytest.fixture()
def _toggle_options(_settings):
    """Toggle all options to True state."""
    for checkbox in _settings.findChildren(QCheckBox):
        checkbox.toggle()
        checkbox.setChecked(True)


def test_check_value(_toggle_options, _tmp_settings_file):
    """Check if checkboxes saved their state on the file settings.

    All values should be True because tests call fixture which toggles all
    of them to True.
    """
    config = configparser.ConfigParser()
    config.read(_tmp_settings_file)

    settings_values = config['options']

    for opt in settings_values:
        assert config.getboolean('options', opt)


def test_no_settings_default_values(_settings):
    """Check checkbox default values.

    If no settings.ini is found, checkbox should start with a default value.
    """
    initial_values = {
        'override_output_editor': False,
        'format_text': False,
        'clear_output': False,
        'override_input_editor': False,
        'show_file_path': False,
        'show_unicode': False,
    }

    for checkbox in _settings.findChildren(QCheckBox):
        value = initial_values[checkbox.objectName()]
        assert checkbox.isChecked() == value
