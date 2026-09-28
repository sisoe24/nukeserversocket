from __future__ import annotations

import sys
import json
import socket
import threading
import subprocess
from pathlib import Path

import pytest

from nss_mcp.server import (TOOLS, PARSE_ERROR, INVALID_PARAMS, METHOD_NOT_FOUND,
                            PROTOCOL_VERSION, send_to_nuke, handle_message)

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


def _lan_ip() -> str | None:
    """Best-effort non-loopback IP of this machine (no packets are actually sent)."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(('10.255.255.255', 1))
        ip = sock.getsockname()[0]
    except OSError:
        return None
    finally:
        sock.close()
    return None if ip.startswith('127.') else ip


def _request(method: str, params: dict | None = None, msg_id: int = 1) -> dict:
    msg: dict = {'jsonrpc': '2.0', 'id': msg_id, 'method': method}
    if params is not None:
        msg['params'] = params
    return msg


def test_initialize_echoes_client_protocol_version():
    """Initialize replies with the protocol version requested by the client."""
    response = handle_message(_request('initialize', {'protocolVersion': '2024-11-05'}))
    assert response['id'] == 1
    assert response['result']['protocolVersion'] == '2024-11-05'
    assert response['result']['capabilities'] == {'tools': {}}
    assert response['result']['serverInfo']['name'] == 'nukeserversocket-mcp'


def test_initialize_defaults_protocol_version():
    """Initialize without a client version falls back to the server's version."""
    response = handle_message(_request('initialize'))
    assert response['result']['protocolVersion'] == PROTOCOL_VERSION


def test_initialized_notification_gets_no_response():
    """Notifications must never receive a response."""
    assert handle_message({'jsonrpc': '2.0', 'method': 'notifications/initialized'}) is None


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
    assert response['error']['code'] == -32600


def test_tools_call_unknown_tool_returns_invalid_params():
    """Calling a tool that does not exist gets a -32602 error."""
    response = handle_message(_request('tools/call', {'name': 'bogus', 'arguments': {}}))
    assert response['error']['code'] == INVALID_PARAMS


def test_tools_call_missing_code_returns_invalid_params():
    """Calling nuke_execute_code without code gets a -32602 error."""
    response = handle_message(
        _request('tools/call', {'name': 'nuke_execute_code', 'arguments': {}}))
    assert response['error']['code'] == INVALID_PARAMS


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
    assert received['payload'] == {'text': 'print("hi")', 'formatText': '0'}


def test_tools_call_unreachable_nuke_returns_is_error(free_port):
    """When nothing listens on the port, the tool result flags isError with a hint."""
    response = handle_message(
        _request('tools/call', {'name': 'nuke_execute_code',
                                'arguments': {'code': 'print(1)'}}),
        port=free_port,
    )
    assert response['result']['isError'] is True
    assert 'Is Nuke running' in response['result']['content'][0]['text']


def test_send_to_nuke_round_trip(fake_nuke_server):
    """send_to_nuke writes the nukeserversocket payload and reads the reply until EOF."""
    port, received = fake_nuke_server
    output = send_to_nuke('print("hi")', '127.0.0.1', port)
    assert output == 'hello world\n'
    assert received['payload'] == {'text': 'print("hi")', 'formatText': '0'}


def test_send_to_nuke_over_lan_interface():
    """The bridge reaches a server bound on all interfaces (like nukeserversocket)
    through the machine's LAN IP — same path as a remote agent machine."""
    ip = _lan_ip()
    if ip is None:
        pytest.skip('No non-loopback interface available.')

    server = socket.socket()
    server.bind(('0.0.0.0', 0))
    server.listen(1)
    port = server.getsockname()[1]

    def _serve():
        conn, _ = server.accept()
        conn.recv(4096)
        conn.sendall(b'remote ok')
        conn.close()

    threading.Thread(target=_serve, daemon=True).start()

    assert send_to_nuke('print(1)', ip, port) == 'remote ok'
    server.close()


def test_stdio_end_to_end():
    """The server answers initialize, tools/list and bad JSON over real stdio."""
    lines = [
        json.dumps(_request('initialize', {'protocolVersion': PROTOCOL_VERSION})),
        json.dumps({'jsonrpc': '2.0', 'method': 'notifications/initialized'}),
        'not json',
        json.dumps(_request('tools/list', msg_id=2)),
    ]
    process = subprocess.run(
        [sys.executable, '-m', 'nss_mcp'],
        input='\n'.join(lines) + '\n',
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
    )

    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert len(responses) == 3
    assert responses[0]['result']['serverInfo']['name'] == 'nukeserversocket-mcp'
    assert responses[1]['error']['code'] == PARSE_ERROR
    assert responses[2]['result']['tools'][0]['name'] == 'nuke_execute_code'
