"""Hand-rolled MCP server bridging an MCP client (stdio) to a running nukeserversocket.

Protocol notes (stdio transport, spec revision 2025-11-25):

- Framing: one JSON-RPC 2.0 message per line, UTF-8, no embedded newlines.
- Lifecycle: client sends ``initialize`` -> server replies with its capabilities ->
  client sends ``notifications/initialized`` -> normal traffic (``tools/list``,
  ``tools/call``, ``ping``).
- Notifications carry no ``id`` and must never receive a response.
- Responses echo the request ``id`` verbatim; a request id must not be null.
- Version negotiation: echo the client's version only if supported, otherwise
  answer with the latest version this server supports.
- Tool execution failures (including argument validation) are tool results with
  ``isError: true`` so the model can self-correct; protocol errors are reserved
  for malformed requests and unknown tools/methods.
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

__version__ = '0.2.0'

# Newest first; the features used here (initialize, tools, ping) exist in all of them.
SUPPORTED_VERSIONS = ('2025-11-25', '2025-06-18', '2025-03-26', '2024-11-05')

DEFAULT_HOST = '127.0.0.1'
DEFAULT_PORT = 54321
DEFAULT_TIMEOUT = 60.0

PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

INSTRUCTIONS = (
    'Executes Python inside a running Nuke session. Nuke must be running with the '
    'nukeserversocket panel connected; the `nuke` module is available to the code.'
)

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
    # shortcut: nukeserversocket reads a single readyRead burst, so a payload split
    # across TCP segments (>~64KB or slow LAN) is parsed as empty; fix in the Qt
    # server if large scripts become a real use case.
    payload = json.dumps({'text': code, 'formatText': '0'}).encode('utf-8')

    with socket.create_connection((host, port), timeout=timeout) as sock:
        sock.sendall(payload)

        chunks = []
        while True:
            data = sock.recv(4096)
            if not data:
                break
            chunks.append(data)

    return b''.join(chunks).decode('utf-8', errors='replace')


def _result(msg_id: Any, result: dict[str, Any]) -> dict[str, Any]:
    return {'jsonrpc': '2.0', 'id': msg_id, 'result': result}


def _error(msg_id: Any, code: int, message: str) -> dict[str, Any]:
    return {'jsonrpc': '2.0', 'id': msg_id, 'error': {'code': code, 'message': message}}


def _tool_error(msg_id: Any, text: str) -> dict[str, Any]:
    return _result(msg_id, {'content': [{'type': 'text', 'text': text}], 'isError': True})


def _initialize(params: dict[str, Any]) -> dict[str, Any]:
    client_version = params.get('protocolVersion')
    version = client_version if client_version in SUPPORTED_VERSIONS else SUPPORTED_VERSIONS[0]
    return {
        'protocolVersion': version,
        'capabilities': {'tools': {}},
        'serverInfo': {'name': 'nukeserversocket-mcp', 'version': __version__},
        'instructions': INSTRUCTIONS,
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

    arguments = params.get('arguments')
    code = arguments.get('code') if isinstance(arguments, dict) else None
    if not isinstance(code, str) or not code:
        return _tool_error(msg_id, "'code' must be a non-empty string.")

    try:
        output = send_to_nuke(code, host, port, timeout)
    except socket.timeout:
        LOGGER.error('Timed out waiting for nukeserversocket output.')
        return _tool_error(
            msg_id, f'Timed out after {timeout:g}s waiting for Nuke output. '
            'Long-running code may need a higher --timeout.'
        )
    except OSError as e:
        LOGGER.error('Could not reach nukeserversocket: %s', e)
        return _tool_error(
            msg_id, f'Could not reach nukeserversocket at {host}:{port} ({e}). '
            'Is Nuke running with the nukeserversocket panel connected on that port?'
        )

    return _result(msg_id, {'content': [{'type': 'text', 'text': output}], 'isError': False})


def handle_message(
    msg: dict[str, Any],
    host: str = DEFAULT_HOST,
    port: int = DEFAULT_PORT,
    timeout: float = DEFAULT_TIMEOUT,
) -> dict[str, Any] | None:
    """Dispatch one JSON-RPC message and return the response, or None for notifications."""
    if 'id' in msg and msg['id'] is None:
        return _error(None, INVALID_REQUEST, 'Request id must not be null.')

    # No id = notification: never answered, whatever the method.
    if 'id' not in msg:
        return None

    msg_id = msg['id']
    method = msg.get('method')
    params = msg.get('params')
    if not isinstance(params, dict):
        params = {}

    if method == 'initialize':
        return _result(msg_id, _initialize(params))

    if method == 'ping':
        return _result(msg_id, {})

    if method == 'tools/list':
        return _result(msg_id, {'tools': TOOLS})

    if method == 'tools/call':
        return _tools_call(msg_id, params, host, port, timeout)

    if not isinstance(method, str):
        return _error(msg_id, INVALID_REQUEST, 'Missing method.')

    LOGGER.warning('Unknown method: %s', method)
    return _error(msg_id, METHOD_NOT_FOUND, f'Unknown method: {method}')


def _write(msg: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(msg) + '\n')
    sys.stdout.flush()


def serve(host: str, port: int, timeout: float = DEFAULT_TIMEOUT) -> None:
    """Run the stdio loop until the client closes stdin."""
    # The platform may default stdio to a locale codepage (cp1252 on Windows);
    # the transport mandates UTF-8 and '\n' framing.
    sys.stdin.reconfigure(encoding='utf-8', errors='replace')
    sys.stdout.reconfigure(encoding='utf-8', newline='\n')

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

        if not isinstance(msg, dict):
            _write(_error(None, INVALID_REQUEST, 'Message must be a JSON object.'))
            continue

        try:
            response = handle_message(msg, host, port, timeout)
        except Exception:
            LOGGER.exception('Unhandled error while handling message.')
            response = _error(msg['id'], INTERNAL_ERROR, 'Internal error.') if 'id' in msg else None

        if response is not None:
            _write(response)


def main() -> None:
    parser = argparse.ArgumentParser(description='MCP stdio bridge to nukeserversocket.')
    parser.add_argument('--host', default=os.getenv('NSS_MCP_HOST', DEFAULT_HOST))
    # String defaults so argparse applies `type` to env values too, turning a bad
    # NSS_MCP_PORT into a usage error instead of a startup traceback.
    parser.add_argument('--port', type=int, default=os.getenv('NSS_MCP_PORT', str(DEFAULT_PORT)))
    parser.add_argument('--timeout', type=float,
                        default=os.getenv('NSS_MCP_TIMEOUT', str(DEFAULT_TIMEOUT)))
    args = parser.parse_args()

    logging.basicConfig(stream=sys.stderr, level=logging.INFO,
                        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    try:
        serve(args.host, args.port, args.timeout)
    except (BrokenPipeError, KeyboardInterrupt):
        pass


if __name__ == '__main__':
    main()
