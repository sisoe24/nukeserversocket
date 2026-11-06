from __future__ import annotations

import sys
import json
import socket
import threading
import subprocess
from pathlib import Path

import pytest

from nss_mcp.server import (PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS,
                            TOOLS, SUPPORTED_VERSIONS, _is_error, send_to_nuke, handle_message)

REPO_ROOT = Path(__file__).parents[1]


@pytest.fixture()
def fake_nuke_server():
    """Threaded stdlib TCP server mimicking nukeserversocket: one request, reply, close."""
    received: dict = {}

    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(1)
    port = server.getsockname()[1]

    def _serve():
        conn, _ = server.accept()
        received['payload'] = json.loads(conn.recv(4096).decode('utf-8'))
        conn.sendall(b'hello world\n')
        conn.close()

    thread = threading.Thread(target=_serve, daemon=True)
    thread.start()

    yield port, received

    server.close()


@pytest.fixture()
def free_port():
    """A localhost port with nothing listening on it."""
    sock = socket.socket()
    sock.bind(('127.0.0.1', 0))
    port = sock.getsockname()[1]
    sock.close()
    return port


def _request(method: str, params: dict | None = None, msg_id: int = 1) -> dict:
    msg: dict = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
    if params is not None:
        msg['params'] = params
    return msg


def test_initialize_echoes_supported_protocol_version():
    """Initialize echoes the client's version when the server supports it."""
    response = handle_message(_request('initialize', {'protocolVersion': '2024-11-05'}))
    assert response['id'] == 1
    assert response['result']['protocolVersion'] == '2024-11-05'
    assert response['result']['capabilities'] == {'tools': {}}
    assert response['result']['serverInfo']['name'] == 'nukeserversocket-mcp'


def test_initialize_unsupported_version_returns_latest():
    """An unsupported client version gets the server's latest supported version back."""
    response = handle_message(_request('initialize', {'protocolVersion': '9999-01-01'}))
    assert response['result']['protocolVersion'] == SUPPORTED_VERSIONS[0]


def test_initialize_defaults_protocol_version():
    """Initialize without a client version falls back to the server's latest version."""
    response = handle_message(_request('initialize'))
    assert response['result']['protocolVersion'] == SUPPORTED_VERSIONS[0]


def test_initialized_notification_gets_no_response():
    """Notifications must never receive a response."""
    assert handle_message({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) is None


def test_notification_method_with_id_is_answered():
    """A message with an id is a request, even with a notifications/* method."""
    response = handle_message({'jsonrpc': '2.0', 'id': 5, 'method': 'notifications/initialized'})
    assert response['id'] == 5
    assert response['error']['code'] == METHOD_NOT_FOUND


def test_null_id_request_returns_invalid_request():
    """An explicit null id is a malformed request, not a notification."""
    response = handle_message({'jsonrpc': '2.0', 'id': None, 'method': 'tools/list'})
    assert response['error']['code'] == INVALID_REQUEST


def test_ping_returns_empty_result():
    """Ping replies with an empty result object."""
    assert handle_message(_request('ping'))['result'] == {}


def test_tools_list_returns_the_execute_tool():
    """tools/list exposes the single nuke_execute_code tool."""
    response = handle_message(_request('tools/list'))
    assert response['result']['tools'] == TOOLS
    assert response['result']['tools'][0]['name'] == 'nuke_execute_code'


def test_unknown_method_returns_method_not_found():
    """A request with an unknown method gets a -32601 error."""
    response = handle_message(_request('bogus/method'))
    assert response['error']['code'] == METHOD_NOT_FOUND


def test_unknown_method_notification_is_ignored():
    """An unknown method without an id is a notification and gets no response."""
    assert handle_message({'jsonrpc': '2.0', 'method': 'bogus/method'}) is None


def test_missing_method_returns_invalid_request():
    """A request without a method gets an error, not a crash."""
    response = handle_message({'jsonrpc': '2.0', 'id': 1})
    assert response['error']['code'] == INVALID_REQUEST


@pytest.mark.parametrize('params', [[1, 2], 'text', 42])
def test_non_dict_params_do_not_crash(params):
    """A non-object params field is tolerated, never an AttributeError."""
    response = handle_message({'jsonrpc': '2.0', 'id': 1, 'method': 'initialize',
                               'params': params})
    assert response['result']['protocolVersion'] == SUPPORTED_VERSIONS[0]


def test_tools_call_unknown_tool_returns_invalid_params():
    """Calling a tool that does not exist gets a -32602 protocol error."""
    response = handle_message(_request('tools/call', {'name': 'bogus', 'arguments': {}}))
    assert response['error']['code'] == INVALID_PARAMS


@pytest.mark.parametrize('arguments', [{}, {'code': ''}, {'code': 1}, [1, 2], None])
def test_tools_call_invalid_code_returns_execution_error(arguments):
    """Invalid tool arguments are execution errors (isError), not protocol errors."""
    response = handle_message(
        _request('tools/call', {'name': 'nuke_execute_code', 'arguments': arguments}))
    assert response['result']['isError'] is True
    assert "'code'" in response['result']['content'][0]['text']


def test_tools_call_executes_code(fake_nuke_server):
    """tools/call forwards the code over TCP and returns the output as text content."""
    port, received = fake_nuke_server
    response = handle_message(
        _request('tools/call', {'name': 'nuke_execute_code',
                                'arguments': {'code': 'print("hi")'}}),
        port=port,
    )
    assert response['result']['isError'] is False
    assert response['result']['content'] == [{'type': 'text', 'text': 'hello world\n'}]
    assert received['payload'] == {'text': 'print("hi")', 'file': 'MCP', 'formatText': '0'}


@pytest.mark.parametrize('output, expected', [
    ('hello\n', False),
    ('', False),
    ('the word Traceback\n', False),
    ('NukeServerSocket error: no code received.', True),
    ('Traceback (most recent call last):\n  File "x"\nValueError: boom\n', True),
    ('printed first\nTraceback (most recent call last):\nValueError: boom\n', True),
    ('  File "<string>", line 1\n    def (\n        ^\nSyntaxError: invalid syntax\n', True),
    ('  File "<string>", line 2\n    x\nIndentationError: unexpected indent\n', True),
    ('SyntaxError: mentioned first\nthen normal output\n', False),
])
def test_is_error_recognizes_failed_replies(output, expected):
    """Server errors and tracebacks are flagged; ordinary output is not."""
    assert _is_error(output) is expected


@pytest.mark.parametrize('error', [BrokenPipeError('pipe'), ConnectionResetError('reset')])
def test_tools_call_dropped_connection_suggests_smaller_code(monkeypatch, error):
    """A connection dropped mid-request blames the code size, not a missing Nuke."""
    def _raise(*_):
        raise error

    monkeypatch.setattr('nss_mcp.server.send_to_nuke', _raise)
    response = handle_message(
        _request('tools/call', {'name': 'nuke_execute_code', 'arguments': {'code': 'x'}}))
    assert response['result']['isError'] is True
    assert 'smaller pieces' in response['result']['content'][0]['text']


def test_tools_call_unreachable_nuke_returns_is_error(free_port):
    """When nothing listens on the port, the tool result flags isError with a hint."""
    response = handle_message(
        _request('tools/call', {'name': 'nuke_execute_code',
                                'arguments': {'code': 'print(1)'}}),
        port=free_port,
    )
    assert response['result']['isError'] is True
    assert 'Is Nuke running' in response['result']['content'][0]['text']


def test_tools_call_timeout_returns_is_error():
    """A peer that accepts but never replies produces a timeout isError result."""
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(1)
    port = server.getsockname()[1]

    response = handle_message(
        _request('tools/call', {'name': 'nuke_execute_code', 'arguments': {'code': 'x'}}),
        port=port, timeout=0.2,
    )
    server.close()

    assert response['result']['isError'] is True
    assert 'Timed out' in response['result']['content'][0]['text']


def test_send_to_nuke_round_trip(fake_nuke_server):
    """send_to_nuke writes the nukeserversocket payload and reads the reply until EOF."""
    port, received = fake_nuke_server
    output = send_to_nuke('print("hi")', '127.0.0.1', port)
    assert output == 'hello world\n'
    assert received['payload'] == {'text': 'print("hi")', 'file': 'MCP', 'formatText': '0'}


def test_stdio_end_to_end():
    """The server answers initialize, bad JSON, non-object JSON and tools/list,
    and survives the malformed lines."""
    lines = [
        json.dumps(_request('initialize', {'protocolVersion': SUPPORTED_VERSIONS[0]})),
        json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}),
        'not json',
        '[1, 2]',
        json.dumps(_request('tools/list', msg_id=2)),
    ]
    process = subprocess.run(
        [sys.executable, '-m', 'nss_mcp'],
        input='\n'.join(lines) + '\n',
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
    )

    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert len(responses) == 4
    assert responses[0]['result']['serverInfo']['name'] == 'nukeserversocket-mcp'
    assert responses[1]['error']['code'] == PARSE_ERROR
    assert responses[2]['error']['code'] == INVALID_REQUEST
    assert responses[3]['result']['tools'][0]['name'] == 'nuke_execute_code'
