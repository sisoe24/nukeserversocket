from __future__ import annotations

import json
import pathlib
from datetime import datetime

import pytest
from pytestqt.qtbot import QtBot
from PySide2.QtWidgets import QTextEdit, QPlainTextEdit

from nukeserversocket.settings import _NssSettings, get_settings
from nukeserversocket.received_data import ReceivedData
from nukeserversocket.editor_controller import EditorController

pytestmark = pytest.mark.quick


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
    app = MockEditorController()
    qtbot.addWidget(app.input_editor)
    return app


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

    result = editor.run(data)
    # XXX: risky test since it depends on the current time

    now = datetime.now().strftime('%H:%M:%S')
    output = f'[{now} NukeTools] test.py\nhello world\n'

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

    # TODO: settings should reset after each test but it doesn't
    settings.set('clear_output', True)


def test_execute_clear_output(editor: MockEditorController, data: ReceivedData, tmp_settings: pathlib.Path):
    settings = get_settings()
    settings.set('mirror_script_editor', True)
    settings.set('format_output', '')
    settings.set('clear_output', True)

    editor.run(data)
    editor.run(data)

    assert editor.output_editor.toPlainText() == 'hello world\n'
    assert editor.history == []
