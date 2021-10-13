import re

import pytest
from collections import namedtuple

from src.script_editor import nuke_se_controllers as nse
from src.utils import AppSettings

SAMPLE_TEXT = 'Random Code Result: Hello'


@pytest.fixture()
def settings(scope='session'):
    yield AppSettings()


@pytest.fixture(scope='session')
def se_controller():
    """Get the ScriptEditorController Class"""
    controller = nse.ScriptEditorController()
    yield controller


@pytest.fixture()
def py_controller():
    """Get the PyController Class"""
    controller = nse._PyController('path/to/file.py')
    yield controller


def show_path_settings():
    ShowPath = namedtuple('ShowPath', ['setting', 'expected'])
    return (ShowPath(True, 'path/to/file.py'), ShowPath(False, 'file.py'))


@pytest.mark.parametrize('show_path', show_path_settings(), ids=['fullpath', 'basename'])
def test_show_filename(show_path, settings, py_controller):
    """Check if file path is displayed correctly based on settings."""
    settings.setValue('options/show_file_path', show_path.setting)
    assert py_controller._show_file() == show_path.expected


@pytest.mark.parametrize('msg', ['RandomCode Result: Hello', 'Hello'],
                         ids=['With Result', 'No Result'])
def test_clean_output(py_controller, msg):
    """Check if output text is getting cleaned from Result."""
    assert py_controller._clean_output(msg) == 'Hello'


def output_format_settings():
    start = r'\[\d\d:\d\d:\d\d\] \[Nuke Tools\]'
    end = r'\nHello'
    Output = namedtuple('Output', ['show_file', 'show_unicode', 'pattern'])
    return (
        Output(True, True, start + r' path/to/file\.py ↴' + end),
        Output(True, False, start + r' path/to/file\.py ' + end),
        Output(False, True, start + r' file\.py ↴' + end),
        Output(False, False, start + r' file\.py ' + end),
    )


@pytest.mark.parametrize('output', output_format_settings(),
                         ids=['filepath + unicode', 'filepath no unicode',
                              'filename + unicode', 'filename no unicode'])
def test_output_format(py_controller, settings, output):
    """Test various format output settings"""
    settings.setValue('options/show_file_path', output.show_file)
    settings.setValue('options/show_unicode', output.show_unicode)

    result = py_controller._format_output(SAMPLE_TEXT)
    assert re.match(output.pattern, result)


def test_append_output(py_controller):
    """Append output to class attribute."""
    py_controller._append_output(SAMPLE_TEXT)
    assert py_controller.history == [SAMPLE_TEXT]


def test_clear_history(py_controller):
    """Clear history"""
    py_controller._clear_history()
    assert py_controller.history == []


@pytest.mark.skip()
def test_clear_output():
    pass


@pytest.mark.skip()
def test_no_clear_output():
    pass


@pytest.fixture()
def override_input_editor(se_controller, settings, py_controller):
    """Override input editor fixture factory."""

    def _override_input_editor(value):
        settings.setValue('options/override_input_editor', value)
        py_controller.restore_input()
        return se_controller.input()

    se_controller.set_input(SAMPLE_TEXT)
    return _override_input_editor


def test_restore_input(override_input_editor, se_controller):
    """Check if input was restored."""
    input_text = override_input_editor(False)
    assert input_text == se_controller.initial_input


def test_override_input(override_input_editor):
    """Check if input was overridden."""
    input_text = override_input_editor(True)
    assert input_text == SAMPLE_TEXT


@pytest.fixture()
def output_to_console(se_controller, py_controller, settings):
    """Restore output fixture factory."""

    def _restore_output(value):
        settings.setValue('options/output_to_console', value)
        py_controller.restore_output()
        return se_controller.output()

    se_controller.set_input("print('hello nukeserversocket'.upper())")
    se_controller.execute()

    return _restore_output


def test_override_output(output_to_console, se_controller):
    """Check if output was not sent to console."""
    output_text = output_to_console(False)
    assert output_text == se_controller.initial_output


def test_restore_output(output_to_console):
    """Check if output was sent to console."""
    output_text = output_to_console(True)
    assert re.search('HELLO NUKESERVERSOCKET', output_text)
