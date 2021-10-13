import re

import pytest
from collections import namedtuple

from src.script_editor import nuke_se_controllers as nse
from src.utils import AppSettings

TEXT = 'Random Code Result: Hello'


@pytest.fixture()
def settings():
    yield AppSettings()


@pytest.fixture()
def py_controller():
    """Get the PyController Class"""
    controller = nse._PyController('path/to/file.py')
    yield controller


@pytest.fixture()
def se_controller():
    """Get the ScriptEditorController Class"""
    controller = nse.ScriptEditorController()
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

    result = py_controller._format_output(TEXT)
    assert re.match(output.pattern, result)


def test_append_output(py_controller):
    """Append output to class attribute."""
    py_controller._append_output(TEXT)
    assert py_controller.history == [TEXT]


def test_clear_history(py_controller):
    """Clear history"""
    py_controller._clear_history()
    assert py_controller.history == []


def test_restore_input(settings, se_controller,  py_controller):
    input_widget = se_controller.script_editor.input_widget
    initial_input = se_controller.initial_input

    input_widget.setPlainText(TEXT)

    settings.setValue('options/override_input_editor', False)
    py_controller.restore_input()

    assert initial_input == input_widget.toPlainText()


def test_override_input(settings, se_controller,  py_controller):
    input_widget = se_controller.script_editor.input_widget
    initial_input = se_controller.initial_input

    input_widget.setPlainText(TEXT)

    settings.setValue('options/override_input_editor', True)
    py_controller.restore_input()

    assert initial_input != input_widget.toPlainText()


def test_override_ouput(settings, se_controller,  py_controller):
    input_widget = se_controller.script_editor.input_widget
    input_widget.setPlainText("print('Hello NSS'.upper())")
    se_controller.execute()

    settings.setValue('options/output_to_console', False)
    py_controller.restore_output()

    output_widget = se_controller.script_editor.output_widget

    assert output_widget.toPlainText() == ''


def test_restore_ouput(settings, se_controller,  py_controller):
    input_widget = se_controller.script_editor.input_widget
    input_widget.setPlainText("print('Hello NSS'.upper())")
    se_controller.execute()

    settings.setValue('options/output_to_console', True)
    py_controller.restore_output()

    output_widget = se_controller.script_editor.output_widget

    assert re.search('HELLO NSS', output_widget.toPlainText())
