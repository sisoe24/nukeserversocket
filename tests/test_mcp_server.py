from __future__ import annotations

import sys
import json
import socket
import threading
import subprocess
from pathlib import Path

import pytest

from nss_mcp import server as bridge_module
from nss_mcp.server import (PARSE_ERROR, INVALID_REQUEST, METHOD_NOT_FOUND, INVALID_PARAMS,
                            EXECUTE_TOOL, SUPPORTED_VERSIONS, Bridge, _is_error, send_to_nuke)

REPO_ROOT = Path(__file__).parents[1]


@pytest.fixture(autouse=True)
def no_poll_wait(monkeypatch):
    monkeypatch.setattr(bridge_module, 'POLL_INTERVAL', 0)


def handle_message(msg: dict, **bridge_args):
    return Bridge(**bridge_args).handle(msg)


@pytest.fixture()
def fake_nuke():
    """A fake nukeserversocket that answers each request with reply(payload), until closed."""
    received: list = []
    server = socket.socket()
    server.bind(('127.0.0.1', 0))
    server.listen(5)
    state = {'reply': lambda payload: ''}

    def _serve():
        while True:
            try:
                conn, _ = server.accept()
            except OSError:
                return
            payload = json.loads(conn.recv(65536).decode('utf-8'))
            received.append(payload)
            reply = state['reply'](payload)
            conn.sendall(reply if isinstance(reply, bytes) else json.dumps(reply).encode())
            conn.close()

    threading.Thread(target=_serve, daemon=True).start()

    def start(reply):
        state['reply'] = reply
        return server.getsockname()[1], received

    yield start
    server.close()


PUBLISH_TOOL = {
    'name': 'publish_shot',
    'description': 'Publish the open script.',
    'inputSchema': {'type': 'object', 'properties': {'comment': {'type': 'string'}},
                    'required': ['comment']},
    'timeout': 600,
}


def nuke_with_tools(allow_code: bool, call_reply=None):
    """A reply function for a nukeserversocket with a tool file."""
    def reply(payload):
        if 'list_tools' in payload:
            return {'allow_code': allow_code, 'tools': [PUBLISH_TOOL], 'skipped': {}}
        return call_reply
    return reply


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
    assert response['result']['capabilities'] == {'tools': {'listChanged': True}}
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


def test_tools_list_before_nuke_answers_offers_only_code(free_port):
    """Until Nuke answers, the list is what a Nuke without a tool file allows."""
    response = handle_message(_request('tools/list'), port=free_port)
    assert response['result']['tools'] == [EXECUTE_TOOL]


@pytest.mark.parametrize('allow_code, names', [
    (True, ['nuke_execute_code', 'publish_shot']),
    (False, ['publish_shot']),
])
def test_tools_list_mirrors_nuke(fake_nuke, allow_code, names):
    """The list holds Nuke's tools, and nuke_execute_code only when Nuke allows code."""
    port, received = fake_nuke(nuke_with_tools(allow_code))
    tools = handle_message(_request('tools/list'), port=port)['result']['tools']

    assert [t['name'] for t in tools] == names
    # timeout is for the bridge only, not part of the MCP tool
    assert tools[-1] == {k: PUBLISH_TOOL[k] for k in ('name', 'description', 'inputSchema')}
    assert received == [{'list_tools': True, 'file': 'MCP'}]


def test_tools_list_passes_tool_annotations(fake_nuke):
    hints = {'readOnlyHint': True}
    tool = dict(PUBLISH_TOOL, annotations=hints)
    port, _ = fake_nuke(lambda p: {'allow_code': False, 'tools': [tool], 'skipped': {}})
    tools = handle_message(_request('tools/list'), port=port)['result']['tools']
    assert tools[0]['annotations'] == hints


def test_code_tool_is_marked_destructive_and_not_retried():
    # Codex asks before destructive tools; Claude Code retries idempotent ones
    assert EXECUTE_TOOL['annotations']['destructiveHint'] is True
    assert EXECUTE_TOOL['annotations']['idempotentHint'] is False


@pytest.mark.parametrize('rule', ['nuke.message', 'executeInMainThread', 'nuke.nodes.',
                                  'frame range', 'undo step', 'print'])
def test_code_tool_description_keeps_the_nuke_rules(rule):
    assert rule in EXECUTE_TOOL['description']


@pytest.mark.parametrize('rule', ['studio tool', 'Ask the user before', 'as data'])
def test_instructions_keep_the_session_rules(rule):
    assert rule in bridge_module.INSTRUCTIONS


@pytest.mark.parametrize('reply', [b'NukeServerSocket error: no code received.', b'[]'])
def test_tools_list_with_old_nuke_offers_only_code(fake_nuke, reply):
    """A nukeserversocket without tool support still gets the code tool."""
    port, _ = fake_nuke(lambda payload: reply)
    assert handle_message(_request('tools/list'), port=port)['result']['tools'] == [EXECUTE_TOOL]


def test_nuke_tool_named_like_the_code_tool_is_ignored(fake_nuke):
    """A tools file tool cannot replace nuke_execute_code."""
    shadow = dict(PUBLISH_TOOL, name='nuke_execute_code')
    port, _ = fake_nuke(lambda p: {'allow_code': False, 'tools': [shadow], 'skipped': {}})
    assert handle_message(_request('tools/list'), port=port)['result']['tools'] == []


@pytest.mark.parametrize('call_reply, is_error, text', [
    ({'ok': True, 'output': 'published v2'}, False, 'published v2'),
    ({'ok': False, 'output': 'Invalid arguments'}, True, 'Invalid arguments'),
    (b'not json', True, 'not json'),
])
def test_tools_call_forwards_nuke_tools(fake_nuke, call_reply, is_error, text):
    """A tools file tool call goes to Nuke as call_tool, and ok decides isError."""
    port, received = fake_nuke(nuke_with_tools(False, call_reply))
    response = handle_message(
        _request('tools/call', {'name': 'publish_shot', 'arguments': {'comment': 'v2'}}),
        port=port)

    assert response['result'] == {'content': [{'type': 'text', 'text': text}],
                                  'isError': is_error}
    assert received[-1] == {'call_tool': 'publish_shot', 'arguments': {'comment': 'v2'},
                            'file': 'MCP'}


def test_tools_call_uses_the_tool_timeout(fake_nuke, monkeypatch):
    """A tools file tool's own timeout replaces the bridge default."""
    port, _ = fake_nuke(nuke_with_tools(False, {'ok': True, 'output': ''}))
    timeouts = []
    send = bridge_module._send
    monkeypatch.setattr(bridge_module, '_send',
                        lambda payload, host, port, timeout: timeouts.append(timeout)
                        or send(payload, host, port, timeout))

    handle_message(_request('tools/call', {'name': 'publish_shot', 'arguments': {}}), port=port)
    assert timeouts[-1] == 600


def test_list_changed_is_sent_when_nuke_answers_late(fake_nuke, free_port, monkeypatch):
    """A client that listed before Nuke answered is told to list again."""
    written = []
    monkeypatch.setattr(bridge_module, '_write', written.append)
    port, _ = fake_nuke(nuke_with_tools(False))

    bridge = Bridge(port=free_port)
    bridge.handle(_request('tools/list'))
    bridge.port = port
    bridge.wait_for_nuke()

    assert written == [{'jsonrpc': '2.0', 'method': 'notifications/tools/list_changed'}]
    assert [t['name'] for t in bridge.tools()] == ['publish_shot']


def test_list_changed_is_not_sent_when_the_list_is_the_same(fake_nuke, monkeypatch):
    written = []
    monkeypatch.setattr(bridge_module, '_write', written.append)
    port, _ = fake_nuke(lambda payload: {'allow_code': True, 'tools': [], 'skipped': {}})

    bridge = Bridge(port=port)
    bridge.handle(_request('tools/list'))
    bridge.wait_for_nuke()
    assert written == []


def test_poll_does_not_ask_again_once_nuke_answered(fake_nuke):
    """The startup poll must not repeat the client's own tools/list request."""
    port, received = fake_nuke(nuke_with_tools(False))
    bridge = Bridge(port=port)
    bridge.handle(_request('tools/list'))

    bridge.wait_for_nuke()

    assert len(received) == 1


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


def test_tools_call_unknown_tool_returns_invalid_params(free_port):
    """Calling a tool that does not exist gets a -32602 protocol error."""
    response = handle_message(_request('tools/call', {'name': 'bogus', 'arguments': {}}),
                              port=free_port)
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


def test_stdio_end_to_end(free_port):
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
        [sys.executable, '-m', 'nss_mcp', '--port', str(free_port)],
        input='\n'.join(lines) + '\n',
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=30,
    )

    responses = [json.loads(line) for line in process.stdout.splitlines()]
    assert len(responses) == 4
    assert responses[0]['result']['serverInfo']['name'] == 'nukeserversocket-mcp'
    assert responses[1]['error']['code'] == PARSE_ERROR
    assert responses[2]['error']['code'] == INVALID_REQUEST
    assert responses[3]['result']['tools'][0]['name'] == 'nuke_execute_code'
