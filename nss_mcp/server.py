"""MCP stdio server (spec 2025-11-25) that forwards code to a running nukeserversocket.

Stdlib only and self-contained, so MCP clients can launch it by absolute path.
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

# newest first
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
            'Execute Python code inside a running Nuke session and return its output. '
            'The `nuke` module is available. Use print() to return values.'
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
    """Send code to nukeserversocket over TCP and return its output.

    The server closes the socket after replying, so the reply is read until EOF.
    """
    # shortcut: the server parses only its first read, so code over about 100 KB or split
    # across TCP segments fails; add server framing when remote Nuke or large code is in use.
    payload = json.dumps({'text': code, 'file': 'MCP', 'formatText': '0'}).encode('utf-8')

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


def _is_error(output: str) -> bool:
    # shortcut: replies are plain text with no status, so code that prints a traceback is
    # flagged too; add a status to the wire protocol if that misleads clients.
    return (
        output.startswith('NukeServerSocket error:')
        or '\nTraceback (most recent call last):' in f'\n{output}'
        # Nuke prints syntax errors without the Traceback header
        or output.rstrip().rpartition('\n')[2].startswith(
            ('SyntaxError:', 'IndentationError:', 'TabError:'))
    )


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
            msg_id, f'Timed out after {timeout:g}s waiting for Nuke. The code may have run or '
            'may still be running, so check before retrying. Raise --timeout for long runs.'
        )
    except (BrokenPipeError, ConnectionResetError) as e:
        LOGGER.error('Connection to nukeserversocket dropped: %s', e)
        return _tool_error(
            msg_id, f'Connection to nukeserversocket dropped ({e}). '
            'Code over about 100 KB can cause this, so send smaller pieces.'
        )
    except OSError as e:
        LOGGER.error('Could not reach nukeserversocket: %s', e)
        return _tool_error(
            msg_id, f'Could not reach nukeserversocket at {host}:{port} ({e}). '
            'Is Nuke running with the nukeserversocket panel connected on that port? '
            'A Nuke on another machine also needs Allow LAN Connections turned on.'
        )

    return _result(msg_id, {'content': [{'type': 'text', 'text': output}],
                            'isError': _is_error(output)})


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
    # stdio defaults to the locale codepage on Windows; MCP requires UTF-8
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
    # string defaults: argparse then reports a bad env value as a usage error
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
