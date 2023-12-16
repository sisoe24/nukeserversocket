"""Test PythonController class."""
from __future__ import annotations

import re
from collections import namedtuple

import pytest

from nukeserversocket.settings import AppSettings
from nukeserversocket.widgets.settings_widget import _ScriptEditorSettings
from nukeserversocket.controllers.nuke_controllers import _PyController

BEGIN_PATTERN = r'(\[\d\d:\d\d:\d\d\] \[Nuke Tools\]) '
SAMPLE_WORD = 'NukeServerSocket'

pytestmark = pytest.mark.controllers


@pytest.fixture()
def _app_settings():
    """Initiate the application settings class."""
    yield AppSettings()


@pytest.fixture()
def _py_controller(_init_fake_editor):
    """Initialize the PyController Class.

    Before and after each tests, clear the text widgets.
    """
    controller = _PyController('path/to/file.py')

    yield controller


def _show_path_settings():
    """Create a namedtuple with show_file settings values.

    Values will be:
        * state: True, expected: 'path/to/file.py'
        * state: False, expected: 'file.py'

    Returns:
        tuple[ShowPath, ShowPath]: ShowPath tuple with key: settings, expected.
    """
    ShowPath = namedtuple('ShowPath', ['state', 'expected'])
    return (ShowPath(True, 'path/to/file.py'), ShowPath(False, 'file.py'))


@pytest.mark.parametrize('setting', _show_path_settings(),
                         ids=['fullpath', 'basename'])
def test_show_filename(setting, _app_settings, _py_controller):
    """Check if file path is displayed correctly based on settings.

    If settings if True, should display full path of the file. If False only
    the basename.
    """
    _app_settings.setValue('options/show_file_path', setting.state)
    assert _py_controller._show_file() == setting.expected


@pytest.mark.parametrize('msg', ['RandomCode Result: Hello', 'Hello'],
                         ids=['With Result', 'No Result'])
def test_clean_output(_py_controller, msg):
    """Check if output text is getting cleaned from Result.

    When `Result: Hello` is present, clean output should return only Hello. If
    output is only `Hello`, clean output should do nothing
    """
    assert _py_controller._clean_output(msg) == 'Hello'


def output_format_settings():
    """Create a series of settings combinations to test the output format.

    Create a namedtuple with the following keys:
        * show_file: Show File setting state.
        * show_unicode: Show Unicode setting state.
        * pattern: The pattern that should match the output.

    Returns:
        tuple[Format, Format, Format, Format]
    """
    def pattern(s):
        r"""Generate the pattern for the test.

        Pattern: `[timestamp] [NukeTools] \nNukeServerSocket
        """
        return BEGIN_PATTERN + s + '\n' + SAMPLE_WORD

    # unicode must be created like this for py 2/3 compatibility.
    unicode = u'\u21B4'

    Format = namedtuple('Format', ['show_file', 'show_unicode', 'pattern'])
    return (
        Format(True, True, pattern(r'path/to/file\.py ' + unicode)),
        Format(True, False, pattern(r'path/to/file\.py ')),
        Format(False, True, pattern(r'file\.py ' + unicode)),
        Format(False, False, pattern(r'file\.py ')),
    )


@pytest.mark.parametrize('output', output_format_settings(),
                         ids=['filepath + unicode', 'filepath no unicode',
                              'filename + unicode', 'filename no unicode'])
def test_output_format(_py_controller, _app_settings, output):
    """Test a combinations of settings to see if output matches."""
    _app_settings.setValue('options/show_file_path', output.show_file)
    _app_settings.setValue('options/show_unicode', output.show_unicode)

    result = _py_controller._format_output(SAMPLE_WORD)
    assert re.match(output.pattern, result)


def test_append_output(_py_controller):
    """Append output to history list."""
    # TODO: when randomly testing, this could have some values left from the
    # tests bellow that append to history.
    _py_controller._append_output(SAMPLE_WORD)
    assert len(_py_controller.history) >= 1


def test_clear_history(_py_controller):
    """Clear history."""
    _py_controller._append_output(SAMPLE_WORD)
    _py_controller._clear_history()
    assert len(_py_controller.history) == 0


@pytest.mark.skip(reason='not implemented')
def test_history_size():
    """Test history clean last element if too big."""


@pytest.fixture()
def _overwrite_input_editor(_py_controller, _app_settings):
    """Overwrite input editor fixture factory.

    Set the controller input to the SAMPLE_TEXT var: 'NukeServerSocket' and
    initiate the restore state.
    """
    def _init_restore(value, text):
        """Set setting value and check get input editor text.

        Args:
            text (str): text to insert in the input editor.
            value (bool): True if input will be overwritten, False otherwise.

        Returns:
            str: the controller input text.
        """
        _py_controller.set_input(text)

        if value:
            _py_controller.script_editor.set_input(text)

        _app_settings.setValue('options/override_input_editor', value)
        return _py_controller.script_editor.input()

    return _init_restore


def test_overwrite_input_editor(_overwrite_input_editor):
    """Check if input editor was overwritten.

    After execution, input editor should retain the executed code.
    """
    input_text = _overwrite_input_editor(True, SAMPLE_WORD)
    assert input_text == SAMPLE_WORD


@pytest.fixture()
def _overwrite_output_editor(_py_controller, _app_settings):
    """Output to console fixture factory."""
    def _restore_output(value, text):
        """Execute code and restore output.

        Set the input to be executed, then set the value that decides if output
        will be restored and get the output content.

        Args:
            value (bool): True if sending output to console, False otherwise.
            text (str): text to execute. Text will be execute in the expression
            `print('text')`.

        Returns:
            str: the output editor text.
        """
        _py_controller.set_input("print('{}')".format(text))
        _py_controller.execute()

        _app_settings.setValue('options/override_output_editor', value)
        _py_controller.to_console()

        return _py_controller.script_editor.output()

    return _restore_output


def test_format_text_settings(_overwrite_output_editor, _app_settings):
    """Test Format Text option.

    If Format Text is false, then console output should be a simple string.
    """
    settings = _ScriptEditorSettings()
    settings.setChecked(True)

    _app_settings.setValue('options/format_text', False)
    output = _overwrite_output_editor(True, SAMPLE_WORD)

    assert output.startswith(SAMPLE_WORD)


def test_restore_output(_overwrite_output_editor, _app_settings):
    """Check if output was sent to console.

    If Output to console is true, then so it should be for the format text
    (unless specified otherwise), so the output should return the formatted
    string.

    Method will also set the `show_file_path` and `show_unicode` settings to
    False for simpler pattern match.
    """
    _app_settings.setValue('options/show_file_path', False)
    _app_settings.setValue('options/show_unicode', False)

    output = _overwrite_output_editor(True, SAMPLE_WORD)

    output_pattern = BEGIN_PATTERN + r'file.py \n' + SAMPLE_WORD
    assert re.match(output_pattern, output)


def test_override_output(_overwrite_output_editor, _py_controller):
    """Check if output was not sent to console.

    After execution, output editor should be restored with the initial text: an
    empty string.
    """
    output = _overwrite_output_editor(False, SAMPLE_WORD)
    assert output == _py_controller.script_editor.output()


@pytest.fixture()
def _clear_output(_overwrite_output_editor, _app_settings):
    """Clear output console.

    After executing code, setting Clear Output should clear the output based on
    its state.
    """
    def _execute_output(value):
        """Execute code twice.

        Args:
            value (bool): If True output should be clear at each execution, if
            not the output should retain all of the text.

        Returns:
            bool: True if there is only one line, False otherwise.
        """
        _app_settings.setValue('options/clear_output', value)
        for _ in range(2):
            output = _overwrite_output_editor(True, SAMPLE_WORD)

        # because text is garanteed to be always formatted, we can search for
        # [Nuke Tools] pattern inside the output string.
        return re.findall(r'\[Nuke Tools\]', output)

    return _execute_output


def test_no_clear_output(_clear_output):
    """Check if output widget wasn't cleaned.

    This will result in having multiple lines of text.
    """
    assert len(_clear_output(False)) > 1


def test_clear_output(_clear_output):
    """Check if output widget was cleaned.

    This will result in having a single line of text.
    """
    assert len(_clear_output(True)) == 1
