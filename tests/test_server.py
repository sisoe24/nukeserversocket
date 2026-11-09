
from __future__ import annotations

import re
import sys
import json
import socket
import logging

import pytest
from pytestqt.qtbot import QtBot

from nukeserversocket.tools import Tool
from nukeserversocket.utils import exec_code
from nukeserversocket.server import NssServer
from nukeserversocket.console import NssConsole
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


def test_server_accepts_chunked_payload(qtbot: QtBot, server: NssServer):
    server._editor.settings.set('mirror_script_editor', False)
    server.try_connect(PORT)

    payload = json.dumps({'text': "print('hello chunked'.upper())"}).encode('utf-8')
    client = socket.create_connection(('127.0.0.1', PORT))
    client.settimeout(1)

    for i in range(0, len(payload), 8):
        client.sendall(payload[i:i + 8])
        qtbot.wait(20)

    assert client.recv(1024).decode('utf-8').strip() == 'HELLO CHUNKED'
    client.close()


@pytest.mark.parametrize('payload', (
    b"{'text': 'x'}",
    b'{"text": "x",}',
    b'{"text": "x"}{"text": "y"}',
    b'{"text": "x',
))
def test_server_replies_to_malformed_object(qtbot: QtBot, server: NssServer, payload: bytes):
    server.REQUEST_IDLE_MS = 50
    server.try_connect(PORT)

    client = socket.create_connection(('127.0.0.1', PORT))
    client.settimeout(1)
    client.sendall(payload)
    qtbot.wait(200)

    assert 'no code received' in client.recv(1024).decode('utf-8')
    assert not server._buffers
    client.close()


def test_server_drops_buffer_when_client_disconnects(qtbot: QtBot, server: NssServer):
    server.REQUEST_IDLE_MS = 50
    server.try_connect(PORT)

    client = socket.create_connection(('127.0.0.1', PORT))
    client.sendall(b'{"text": "x')
    qtbot.waitUntil(lambda: bool(server._buffers), timeout=1000)
    client.close()

    qtbot.waitUntil(lambda: not server._buffers, timeout=1000)
    qtbot.wait(100)
    assert server._editor.input_editor.toPlainText() == 'initial input'


@pytest.fixture()
def logged(monkeypatch) -> list:
    """The (level, line) pairs the server logs for requests."""
    lines: list = []
    monkeypatch.setattr('nukeserversocket.server.LOGGER.log',
                        lambda level, fmt, *args: lines.append((level, fmt % args)))
    return lines


def handled(qtbot: QtBot, logged: list, payload) -> tuple:
    """Send one request and return the (level, line) the server logged for it."""
    count = len(logged)
    client = socket.create_connection(('127.0.0.1', PORT))
    client.sendall(payload if isinstance(payload, bytes) else json.dumps(payload).encode())
    qtbot.waitUntil(lambda: len(logged) > count, timeout=1000)
    client.close()
    return logged[-1]


@pytest.mark.parametrize('file, source', [('', '(127.0.0.1)'), ('main.py', '(127.0.0.1 main.py)'),
                                          ('MCP', '(MCP)')])
def test_server_logs_code_with_its_source(qtbot: QtBot, server: NssServer, monkeypatch, logged,
                                          file, source):
    server._editor.settings.set('mirror_script_editor', False)
    monkeypatch.delenv('NSS_TOOLS', raising=False)
    server.try_connect(PORT)

    assert handled(qtbot, logged, {'text': "print('hi')", 'file': file}) == (
        logging.INFO, f'{source} code executed')


def test_server_logs_the_time_of_slow_requests(qtbot: QtBot, server: NssServer, monkeypatch,
                                               logged):
    monkeypatch.delenv('NSS_TOOLS', raising=False)
    server.try_connect(PORT)
    times = iter([10.0, 12.34])
    monkeypatch.setattr('nukeserversocket.server.time.perf_counter', lambda: next(times))
    monkeypatch.setattr(server._editor, 'execute', lambda data: 'done')

    assert handled(qtbot, logged, {'text': 'render()'}) == (
        logging.INFO, '(127.0.0.1) code executed (2.3 s)')


@pytest.mark.parametrize('payload, line', [
    (b'not json', '(127.0.0.1) request has no code'),
    ({'text': '', 'file': 'MCP'}, '(MCP) request has no code'),
])
def test_server_logs_one_warning_for_bad_requests(qtbot: QtBot, server: NssServer, monkeypatch,
                                                  logged, payload, line):
    monkeypatch.delenv('NSS_TOOLS', raising=False)
    server.try_connect(PORT)

    assert handled(qtbot, logged, payload) == (logging.WARNING, line)
    assert len(logged) == 1


def test_server_prefixes_execution_errors(qtbot: QtBot, server: NssServer, monkeypatch):
    def _raise(_):
        raise RuntimeError('Could not find script editor')

    monkeypatch.setattr(server._editor, 'execute', _raise)
    server.try_connect(PORT)

    client = socket.create_connection(('127.0.0.1', PORT))
    client.settimeout(1)
    client.sendall(json.dumps({'text': 'x = 1'}).encode('utf-8'))
    qtbot.wait(100)

    assert client.recv(1024).decode('utf-8') == (
        'NukeServerSocket error: Could not find script editor'
    )
    client.close()


def test_console_shows_html_as_plain_text(qtbot: QtBot):
    console = NssConsole()
    qtbot.addWidget(console)

    console.write('<b>x</b> & y')

    assert console._console.toPlainText().replace('\xa0', ' ') == '<b>x</b> & y'


TOOLS_MODULE = '''
def publish_shot(comment):
    print('publishing')
    return {'version': 2, 'comment': comment}
'''


@pytest.fixture()
def tool_server(server: NssServer, tmp_path, monkeypatch):
    """A server listening with a tool file that turns code off and adds publish_shot."""
    (tmp_path / 'nss_test_server_tools.py').write_text(TOOLS_MODULE)
    monkeypatch.syspath_prepend(str(tmp_path))
    tool_file = tmp_path / 'nss_tools.json'
    tool_file.write_text(json.dumps({'allow_arbitrary_code': False, 'tools': [{
        'name': 'publish_shot',
        'description': 'Publish the open script.',
        'function': 'nss_test_server_tools:publish_shot',
        'timeout': 600,
        'inputSchema': {'type': 'object', 'properties': {'comment': {'type': 'string'}},
                        'required': ['comment']},
    }]}))
    monkeypatch.setenv('NSS_TOOLS', str(tool_file))
    server._editor.settings.set('mirror_script_editor', False)
    server.try_connect(PORT)
    yield server
    sys.modules.pop('nss_test_server_tools', None)


def request(qtbot: QtBot, payload: dict) -> str:
    client = socket.create_connection(('127.0.0.1', PORT))
    client.settimeout(1)
    client.sendall(json.dumps(payload).encode('utf-8'))
    qtbot.wait(100)
    reply = client.recv(65536).decode('utf-8')
    client.close()
    return reply


def test_server_lists_tools(qtbot: QtBot, tool_server: NssServer):
    assert json.loads(request(qtbot, {'list_tools': True})) == {
        'allow_arbitrary_code': False,
        'tools': [{
            'name': 'publish_shot',
            'description': 'Publish the open script.',
            'inputSchema': {'type': 'object', 'properties': {'comment': {'type': 'string'}},
                            'required': ['comment']},
            'timeout': 600,
            'annotations': None,
        }],
        'skipped': {},
    }


def test_server_calls_tool(qtbot: QtBot, tool_server: NssServer):
    reply = request(qtbot, {'call_tool': 'publish_shot', 'arguments': {'comment': 'v2'}})
    assert json.loads(reply) == {'ok': True, 'output': 'publishing\n{"version": 2, "comment": "v2"}'}


@pytest.mark.parametrize('payload, output', [
    ({'call_tool': 'publish_shot', 'arguments': {}}, 'missing required'),
    ({'call_tool': ['publish_shot']}, '"call_tool" must be a tool name.'),
])
def test_server_reports_bad_tool_calls(qtbot: QtBot, tool_server: NssServer, payload, output):
    reply = json.loads(request(qtbot, payload))
    assert reply['ok'] is False
    assert output in reply['output']


@pytest.mark.parametrize('payload, line', [
    ({'list_tools': True, 'file': 'MCP'}, (logging.INFO, '(MCP) list tools: 1')),
    ({'call_tool': 'publish_shot', 'arguments': {'comment': 'v2'}, 'file': 'MCP'},
     (logging.INFO, '(MCP) publish_shot: ok')),
    ({'call_tool': 'publish_shot', 'arguments': {'comment': 1}, 'file': 'MCP'},
     (logging.WARNING, "(MCP) publish_shot: Invalid arguments: 'comment' must be string, got 1.")),
    ({'text': 'print(1)', 'file': 'MCP'},
     (logging.WARNING, '(MCP) code refused: allow_arbitrary_code is false in nss_tools.json')),
])
def test_server_logs_tool_requests(qtbot: QtBot, tool_server: NssServer, logged, payload, line):
    assert handled(qtbot, logged, payload) == line


def test_server_buffers_chunked_tool_request(qtbot: QtBot, tool_server: NssServer):
    payload = json.dumps({'call_tool': 'publish_shot', 'arguments': {'comment': 'v2'}}).encode()
    client = socket.create_connection(('127.0.0.1', PORT))
    client.settimeout(1)

    for i in range(0, len(payload), 8):
        client.sendall(payload[i:i + 8])
        qtbot.wait(20)

    assert json.loads(client.recv(65536).decode('utf-8'))['ok'] is True
    client.close()


def test_server_logs_the_tool_error(qtbot: QtBot, tool_server: NssServer, monkeypatch, logged):
    def fail(comment):
        raise RuntimeError('no write node')
    monkeypatch.setattr(tool_server.toolset.tools['publish_shot'], 'function', fail)

    assert handled(qtbot, logged, {'call_tool': 'publish_shot', 'arguments': {'comment': 'v2'}}) == (
        logging.WARNING, '(127.0.0.1) publish_shot: RuntimeError: no write node')


def test_server_rejects_code_when_tool_file_turns_it_off(qtbot: QtBot, tool_server: NssServer):
    reply = request(qtbot, {'text': "print('hi')"})
    assert reply == ('NukeServerSocket error: code execution is off '
                     '(allow_arbitrary_code is false in nss_tools.json). '
                     'Use the tools it lists instead.')
    assert tool_server._editor.input_editor.toPlainText() == 'initial input'


def test_server_without_tool_file_still_runs_code(qtbot: QtBot, server: NssServer, monkeypatch):
    monkeypatch.delenv('NSS_TOOLS', raising=False)
    server._editor.settings.set('mirror_script_editor', False)
    server.try_connect(PORT)
    assert request(qtbot, {'text': "print('hi')"}).strip() == 'hi'
    assert json.loads(request(qtbot, {'list_tools': True})) == {
        'allow_arbitrary_code': True, 'tools': [], 'skipped': {}}


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


@pytest.mark.parametrize('vision', [True, False])
def test_server_loads_builtins_only_with_vision(server: NssServer, editor, monkeypatch, vision):
    tool = Tool('nuke_vision', 'See.', {'type': 'object'}, lambda: None)
    monkeypatch.setattr(editor, 'builtin_tools', lambda: {tool.name: tool})

    server.try_connect(PORT, vision=vision)

    assert list(server.toolset.builtins) == (['nuke_vision'] if vision else [])
