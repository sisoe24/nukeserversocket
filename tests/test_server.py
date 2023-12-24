
from __future__ import annotations

import json
import socket

import pytest
from pytestqt.qtbot import QtBot
from PySide2.QtWidgets import QTextEdit, QPlainTextEdit

from nukeserversocket.server import NssServer
from nukeserversocket.settings import get_settings
from nukeserversocket.editor_controller import EditorController
from nukeserversocket.controllers.local_app import _stdoutIO

PORT = 55559

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

    def execute(self) -> None:
        with _stdoutIO() as s:
            exec(self.input_editor.toPlainText())
            result = s.getvalue()
            self.output_editor.setPlainText(result)


@pytest.fixture()
def editor():
    return MockEditorController()


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


def test_server_on_new_connection(qtbot: QtBot, server: NssServer, editor: MockEditorController):

    settings = get_settings()
    settings.set('mirror_script_editor', False)

    port = 55559
    server.try_connect(port)

    send_data(port)

    qtbot.wait(1000)
    assert editor.output_editor.toPlainText() == 'initial output'
    assert editor.input_editor.toPlainText() == 'initial input'


def test_server_on_new_connection_mirror_editor(qtbot: QtBot, server: NssServer):
    settings = get_settings()
    settings.set('mirror_script_editor', True)
    settings.set('format_output', '')

    port = 55559
    server.try_connect(port)

    send_data(port)

    qtbot.wait(1000)

    assert server._editor.output_editor.toPlainText() == 'HELLO WORLD\n\n'
    assert server._editor.input_editor.toPlainText() == "print('hello world'.upper())"
