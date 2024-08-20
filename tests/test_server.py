
from __future__ import annotations

import json
import socket

import pytest
from pytestqt.qtbot import QtBot
from PySide2.QtWidgets import QTextEdit, QPlainTextEdit

from nukeserversocket.utils import stdoutIO
from nukeserversocket.server import NssServer
from nukeserversocket.settings import _NssSettings
from nukeserversocket.editor_controller import EditorController

PORT = 55559

pytestmark = pytest.mark.quick


class MockEditorController(EditorController):
    def __init__(self):
        self._input_editor = QPlainTextEdit()
        self._input_editor.setPlainText('initial input')

        self._output_editor = QTextEdit()
        self._output_editor.setPlainText('initial output')

        self._settings = None

    @property
    def input_editor(self):
        return self._input_editor

    @property
    def output_editor(self):
        return self._output_editor

    def execute(self) -> None:
        with stdoutIO() as s:
            exec(self.input_editor.toPlainText())
            result = s.getvalue()
            self.output_editor.setPlainText(result)


@pytest.fixture()
def editor(get_settings: _NssSettings):
    editor = MockEditorController()
    editor.settings = get_settings

    yield editor

    editor.history.clear()
    editor.output_editor.setPlainText('initial output')
    editor.input_editor.setPlainText('initial input')


@pytest.fixture()
def server(editor: MockEditorController) -> NssServer:
    server = NssServer(editor)

    yield server

    server.close()


def send_data(port: int):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', port))
    data = {
        'text': "print('hello world'.upper())",
        'file': 'path/file.py'
    }
    s.sendall(bytes(json.dumps(data), encoding='utf-8'))
    s.close()


def test_server_on_new_connection(qtbot: QtBot, server: NssServer):

    server._editor.settings.set('mirror_script_editor', False)

    port = 55559
    server.try_connect(port)

    send_data(port)

    qtbot.wait(100)

    assert server._editor.output_editor.toPlainText() == 'initial output'
    assert server._editor.input_editor.toPlainText() == 'initial input'


def test_server_on_new_connection_mirror_editor(qtbot: QtBot, server: NssServer):
    server._editor.settings.set('mirror_script_editor', True)
    server._editor.settings.set('format_output', '')
    server._editor.settings.set('clear_output', True)

    port = 55559
    server.try_connect(port)

    send_data(port)

    qtbot.wait(100)

    assert server._editor.output_editor.toPlainText().strip() == 'HELLO WORLD'
    assert server._editor.input_editor.toPlainText() == "print('hello world'.upper())"
