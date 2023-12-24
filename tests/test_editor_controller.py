from __future__ import annotations

import re
import json
import pathlib
from typing import Any
from datetime import datetime
from unittest.mock import patch

import pytest
from pytestqt.qtbot import QtBot
from PySide2.QtWidgets import QTextEdit, QPlainTextEdit

from nukeserversocket.settings import _NssSettings, get_settings
from nukeserversocket.received_data import ReceivedData
from nukeserversocket.editor_controller import EditorController, format_output

pytestmark = pytest.mark.quick


def now():
    return datetime.now().strftime('%H:%M:%S')


class MockEditorController(EditorController):
    def __init__(self):
        self._input_editor = QPlainTextEdit()
        self._input_editor.setPlainText('initial input')

        self._output_editor = QTextEdit()
        self._output_editor.setPlainText('initial output')

    @property
    def input_editor(self):
        return self._input_editor

    @property
    def output_editor(self):
        return self._output_editor

    def execute(self):
        self._output_editor.setPlainText('hello world\n')


@pytest.fixture()
def editor(qtbot: QtBot) -> MockEditorController:
    editor = MockEditorController()
    qtbot.addWidget(editor.input_editor)
    yield editor
    editor.history.clear()


@pytest.fixture()
def data() -> ReceivedData:
    d = {
        'file': 'test.py',
        'text': 'print("hello world")'
    }
    return ReceivedData(json.dumps(d))


def test_execute_no_mirror(editor: MockEditorController, data: ReceivedData, tmp_settings: pathlib.Path):
    result = editor.run(data)
    assert result == 'hello world\n'
    assert editor.output_editor.toPlainText() == 'initial output'
    assert editor.input_editor.toPlainText() == 'initial input'


def test_execute_mirror(editor: MockEditorController, data: ReceivedData, tmp_settings: pathlib.Path):
    settings = get_settings()
    settings.set('mirror_script_editor', True)

    with patch('nukeserversocket.editor_controller.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2000, 1, 1, 0, 0, 0)

        result = editor.run(data)

        output = '[00:00:00 NukeTools] test.py\nhello world\n'
        assert result == output
        assert editor.output_editor.toPlainText() == output
        assert editor.input_editor.toPlainText() == 'print("hello world")'


def test_execute_mirror_no_output_format(editor: MockEditorController, data: ReceivedData, tmp_settings: pathlib.Path):
    settings = get_settings()
    settings.set('mirror_script_editor', True)
    settings.set('format_output', '')

    result = editor.run(data)
    assert result == 'hello world\n'
    assert editor.output_editor.toPlainText() == 'hello world\n'
    assert editor.input_editor.toPlainText() == 'print("hello world")'


def test_execute_no_clear_output(editor: MockEditorController, data: ReceivedData, tmp_settings: pathlib.Path):
    settings = get_settings()
    settings.set('mirror_script_editor', True)
    settings.set('format_output', '')
    settings.set('clear_output', False)

    editor.run(data)
    editor.run(data)

    assert editor.output_editor.toPlainText() == 'hello world\n\nhello world\n\n'
    assert editor.history == ['hello world\n', 'hello world\n']


def test_execute_clear_output(editor: MockEditorController, data: ReceivedData, tmp_settings: pathlib.Path):
    settings = get_settings()
    settings.set('mirror_script_editor', True)
    settings.set('format_output', '')
    settings.set('clear_output', True)

    editor.run(data)
    editor.run(data)

    assert editor.output_editor.toPlainText() == 'hello world\n'
    assert editor.history == []


@pytest.mark.parametrize('file, text, format, expected', [
    ('test.py', 'hello world', '%d', '00:00:00'),
    ('path/test.py', 'hello world', '%f', 'path/test.py'),
    ('path/test.py', 'hello world', '%F', 'test.py'),
    ('test.py', 'hello world', '%t', 'hello world'),
    ('test.py', 'hello world', '%n', '\n'),
    ('path/test.py', 'hello world', '%d %f %F %t %n', '00:00:00 path/test.py test.py hello world \n'),
])
def test_formatting_placeholders(file: str, text: str, format: str, expected: str):
    with patch('nukeserversocket.editor_controller.datetime') as mock_datetime:
        mock_datetime.now.return_value = datetime(2000, 1, 1, 0, 0, 0)
        output = format_output(file, text, format)
        assert output == expected
