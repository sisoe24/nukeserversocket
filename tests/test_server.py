
from __future__ import annotations

import json
import socket

import pytest
from pytestqt.qtbot import QtBot

from nukeserversocket.utils import exec_code
from nukeserversocket.server import NssServer
from nukeserversocket.settings import _NssSettings
from nukeserversocket.controllers.base import EditorController

from nukeserversocket._qt import (QTextEdit, QTcpSocket, QHostAddress,
                                  QPlainTextEdit)

PORT = 55559


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

    def execute_code(self) -> None:
        self.output_editor.setPlainText(
            exec_code(self.input_editor.toPlainText())
        )


@pytest.fixture()
def editor(mock_settings: _NssSettings):
    editor = MockEditorController()
    editor.settings = mock_settings

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


def test_server_listens_on_localhost_by_default(server: NssServer):
    assert server.try_connect(PORT)
    assert server.serverAddress() == QHostAddress(QHostAddress.LocalHost)


def test_server_listens_on_all_interfaces_with_allow_lan(server: NssServer):
    assert server.try_connect(PORT, allow_lan=True)
    assert server.serverAddress() == QHostAddress(QHostAddress.Any)


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


def test_server_replies_to_each_client(qtbot: QtBot, server: NssServer):
    server._editor.settings.set('mirror_script_editor', False)
    server.try_connect(PORT)

    first = socket.create_connection(('127.0.0.1', PORT))
    second = socket.create_connection(('127.0.0.1', PORT))
    # without a timeout a lost reply hangs the test run
    first.settimeout(1)
    second.settimeout(1)
    qtbot.wait(100)

    second.sendall(json.dumps({'text': "print('second')"}).encode('utf-8'))
    qtbot.wait(100)
    first.sendall(json.dumps({'text': "print('first')"}).encode('utf-8'))
    qtbot.wait(100)

    assert first.recv(1024).decode('utf-8').strip() == 'first'
    assert second.recv(1024).decode('utf-8').strip() == 'second'

    first.close()
    second.close()


def test_server_frees_closed_sockets(qtbot: QtBot, server: NssServer):
    server._editor.settings.set('mirror_script_editor', False)
    server.try_connect(PORT)

    with qtbot.waitSignal(server.on_data_received):
        send_data(PORT)

    qtbot.waitUntil(lambda: not server.findChildren(QTcpSocket), timeout=1000)


@pytest.mark.parametrize('payload', (b'not json', b'{"text": ""}'))
def test_server_rejects_missing_code(qtbot: QtBot, server: NssServer, payload: bytes):
    server._editor.settings.set('mirror_script_editor', False)
    server.try_connect(PORT)

    client = socket.create_connection(('127.0.0.1', PORT))
    client.settimeout(1)
    client.sendall(payload)
    qtbot.wait(100)

    assert 'no code received' in client.recv(1024).decode('utf-8')
    assert server._editor.input_editor.toPlainText() == 'initial input'
    assert server._editor.output_editor.toPlainText() == 'initial output'

    client.close()
