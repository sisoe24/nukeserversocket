"""Hand-rolled MCP server bridging an MCP client (stdio) to a running nukeserversocket.

Protocol notes (stdio transport):

- Framing: one JSON-RPC 2.0 message per line, UTF-8, newline-delimited.
- Lifecycle: client sends ``initialize`` -> server replies with its capabilities ->
  client sends ``notifications/initialized`` -> normal traffic (``tools/list``,
  ``tools/call``, ``ping``).
- Notifications carry no ``id`` and must never receive a response.
- Responses echo the request ``id`` verbatim.
- stdout is the transport: anything human-readable goes to stderr.

Stdlib-only and self-contained on purpose, so it can be launched by absolute path
(``python /path/to/server.py``), as a module (``python -m nss_mcp``) or via the
``nss-mcp`` console script.
"""
from __future__ import annotations

import os
import sys
import json
import socket
import logging
import argparse
from typing import Any

LOGGER = logging.getLogger('nss_mcp')

__version__ = '0.1.0'

PROTOCOL_VERSION = '2025-06-18'

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 54321
DEFAULT_TIMEOUT = 60.0

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602

TOOLS = [
    {
        'name': 'nuke_execute_code',
        'description': (
            'Execute Python code inside a running Nuke session via nukeserversocket '
            'and return its output. The code runs in Nuke\'s script editor, so the '
            '`nuke` module is available.'
        ),
        'inputSchema': {
            'type': 'object',
            'properties': {
                'code': {
                    'type': 'string',
                    'description': 'Python code to execute in Nuke.',
                },
            },
            'required': ['code'],
        },
    },
]


def send_to_nuke(code: str, host: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> str:
    """Forward code to nukeserversocket over TCP and return its output.

    nukeserversocket serves one request per connection and closes the socket
    after writing the output, so the response is read until EOF.
    """
    payload = json.dumps({'text': code, 'formatText': '0'}).encode('utf-8')

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(payload)

        chunks = []
        while True:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)

    return b''.join(chunks).decode('utf-8')


def _result(msg_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {'jsonrpc': '2.0', 'id': msg_id, 'result': result}


def _error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': code, 'message': message}}


def _initialize(params: dict[str, Any]) -> dict[str, Any]:
    return {
        'protocolVersion': params.get('protocolVersion', PROTOCOL_VERSION),
        'capabilities': {'tools': {}},
        'serverInfo': {'name': 'nukeserversocket-mcp', 'version': __version__},
    }


def _tools_call(
    msg_id: Any,
    params: dict[str, Any],
    host: str,
    port: int,
    timeout: float,
) -> dict[str, Any]:
    name = params.get('name')
    if name != 'nuke_execute_code':
        return _error(msg_id, INVALID_PARAMS, f'Unknown tool: {name!r}')

    code = (params.get('arguments') or {}).get('code')
    if not isinstance(code, str) or not code:
        return _error(msg_id, INVALID_PARAMS, "'code' must be a non-empty string.")

    # Execution failures are tool results (isError), not JSON-RPC errors:
    # the model is meant to see them and react.
    try:
        output = send_to_nuke(code, host, port, timeout)
    except OSError as e:
        LOGGER.error('Could not reach nukeserversocket: %s', e)
        return _result(msg_id, {
            'content': [{
                'type': 'text',
                'text': (
                    f'Could not reach nukeserversocket at {host}:{port} ({e}). '
                    'Is Nuke running with the nukeserversocket panel connected on that port?'
                ),
            }],
            'isError': True,
        })

    return _result(msg_id, {'content': [{'type': 'text', 'text': output}], 'isError': False})


def handle_message(
    msg: dict[str, Any],
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any] | None:
    """Dispatch one JSON-RPC message and return the response, or None for notifications."""
    msg_id = msg.get('id')
    method = msg.get('method')
    params = msg.get('params') or {}

    is_notification = msg_id is None
    if not isinstance(method, str):
        return None if is_notification else _error(msg_id, INVALID_REQUEST, 'Missing method.')

    if method.startswith('notifications/'):
        return None

    if method == 'initialize':
        return _result(msg_id, _initialize(params))

    if method == 'ping':
        return _result(msg_id, {})

    if method == 'tools/list':
        return _result(msg_id, {'tools': TOOLS})

    if method == 'tools/call':
        return _tools_call(msg_id, params, host, port, timeout)

    LOGGER.warning('Unknown method: %s', method)
    return None if is_notification else _error(msg_id, METHOD_NOT_FOUND, f'Unknown method: {method}')


def _write(msg: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg) + '\n')
    sys.stdout.flush()


def serve(host: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> None:
    """Run the stdio loop until the client closes stdin."""
    LOGGER.info('Serving MCP on stdio. Forwarding code to %s:%s', host, port)

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        try:
            msg = json.loads(line)
        except json.JSONDecodeError as e:
            _write(_error(None, PARSE_ERROR, f'Invalid JSON: {e}'))
            continue

        response = handle_message(msg, host, port, timeout)
        if response is not None:
            _write(response)


def main() -> None:
    parser = argparse.ArgumentParser(description='MCP stdio bridge to nukeserversocket.')
    parser.add_argument('--host', default=os.getenv('NSS_MCP_HOST', DEFAULT_HOST))
    parser.add_argument('--port', type=int, default=int(os.getenv('NSS_MCP_PORT', DEFAULT_PORT)))
    parser.add_argument('--timeout', type=float,
                        default=float(os.getenv('NSS_MCP_TIMEOUT', DEFAULT_TIMEOUT)))
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    serve(args.host, args.port, args.timeout)


if __name__ == '__main__':
    main()
