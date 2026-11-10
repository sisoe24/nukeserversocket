from __future__ import annotations

import json
import time
import logging
from typing import TYPE_CHECKING, Dict, Tuple, Iterable, Optional

from ._qt import QTimer, Signal, QWidget, QTcpServer, QTcpSocket, QHostAddress

from .tools import (CODE_TOOL, MCP_CLIENT, ToolSet, load_tools, parse_tool_request,
                     handle_tool_request)
from .logger import get_logger
from .received_data import ReceivedData

if TYPE_CHECKING:
    from .controllers.base import BaseController

LOGGER = get_logger()


def _source(address: QHostAddress, file: str) -> str:
    """Name the client the way the Logs show it, e.g. "(MCP)" or "(127.0.0.1 main.py)"."""
    host = address.toString()
    if file == MCP_CLIENT:
        return f'({MCP_CLIENT})' if address.isLoopback() else f'({MCP_CLIENT} at {host})'
    return f'({host} {file})' if file else f'({host})'


class NssServer(QTcpServer):
    """NukeServerSocket server.

    This class is responsible for receiving data from the client, and sending the output back.

    Signals:
        on_data_received (): Signal emitted when data is received from the client.

    """
    on_data_received = Signal()

    MAX_REQUEST_BYTES = 10 * 1024 * 1024
    REQUEST_IDLE_MS = 3000

    def __init__(self, editor: BaseController, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._editor = editor
        self.toolset = ToolSet()
        self._buffers: Dict[QTcpSocket, bytearray] = {}

        self.newConnection.connect(self._on_new_connection)
        self.acceptError.connect(lambda err: LOGGER.error('Server error: %s', self.errorString()))

    def _is_incomplete(self, buffer: bytearray) -> bool:
        try:
            json.loads(bytes(buffer))
        except (ValueError, RecursionError):
            return buffer.lstrip()[:1] == b'{' and len(buffer) <= self.MAX_REQUEST_BYTES
        return False

    def _on_socket_ready(self, socket: QTcpSocket, idle_timer: QTimer):
        LOGGER.debug('Socket ready.')

        # TCP can split a request across several reads
        buffer = self._buffers.setdefault(socket, bytearray())
        buffer.extend(socket.readAll().data())

        if self._is_incomplete(buffer):
            LOGGER.debug('Incomplete request (%s bytes). Waiting for more data.', len(buffer))
            idle_timer.start()
            return

        idle_timer.stop()
        self._handle_request(socket)

    def _handle_request(self, socket: QTcpSocket):
        started = time.perf_counter()
        raw = bytes(self._buffers.pop(socket))

        request = parse_tool_request(raw)
        if request is not None:
            source = _source(socket.peerAddress(), str(request.get('file') or ''))
            output, ok, summary = handle_tool_request(self.toolset, request)
            level = logging.INFO if ok else logging.WARNING
        else:
            data = ReceivedData(raw)
            source = _source(socket.peerAddress(), data.file)
            level, summary, output = self._run_code(data)

        elapsed = time.perf_counter() - started
        # only slow requests show their time: (0.0 s) on every line is noise
        if elapsed >= 1:
            summary += f' ({elapsed:.1f} s)'
        LOGGER.log(level, '%s %s', source, summary)
        self._reply(socket, output)

    def _run_code(self, data: ReceivedData) -> Tuple[int, str, str]:
        """Return the log level, what to log, and the reply."""
        if not self.toolset.code_allowed(data.file):
            reason = self.toolset.code_off_reason or f'{CODE_TOOL} is turned off in the panel'
            return (logging.WARNING, f'code refused: {reason}',
                    f'NukeServerSocket error: code execution is off ({reason}). '
                    'Use the tools it lists instead.')

        if not data.text:
            # invalid JSON or empty text: running it would only echo the editor's old output
            return (logging.WARNING, 'request has no code',
                    'NukeServerSocket error: no code received. '
                    'Expected JSON with a non-empty "text" field.')

        try:
            return logging.INFO, 'code executed', self._editor.execute(data)
        except RuntimeError as err:
            # e.g. the Nuke Script Editor is not open; reply so the client does not hang
            return logging.ERROR, f'code: {err}', f'NukeServerSocket error: {err}'

    def _reply(self, socket: QTcpSocket, output: str) -> None:
        self.on_data_received.emit()

        socket.write(output.encode('utf-8'))
        LOGGER.debug('Output: %s', output.replace('\n', '\\n'))

        socket.close()
        LOGGER.debug('Socket closed.')

    def _on_new_connection(self) -> None:
        LOGGER.debug('New connection.')
        while self.hasPendingConnections():

            LOGGER.debug('Pending connection.')
            socket = self.nextPendingConnection()
            socket.errorOccurred.connect(lambda err: LOGGER.error('Socket error: %s', err))

            # malformed JSON never completes, so stop waiting once the data stops
            idle_timer = QTimer(socket)
            idle_timer.setSingleShot(True)
            idle_timer.setInterval(self.REQUEST_IDLE_MS)
            idle_timer.timeout.connect(lambda socket=socket: self._handle_request(socket))

            socket.disconnected.connect(idle_timer.stop)
            socket.disconnected.connect(lambda socket=socket: self._buffers.pop(socket, None))
            socket.disconnected.connect(socket.deleteLater)

            LOGGER.debug('Socket connected.')
            # bind each socket to its own handler, so replies go to the right client
            socket.readyRead.connect(
                lambda socket=socket, idle_timer=idle_timer: self._on_socket_ready(
                    socket, idle_timer)
            )

    def try_connect(
        self,
        port: int,
        allow_lan: bool = False,
        tools_file: Optional[str] = None,
        disabled_tools: Iterable[str] = (),
    ) -> bool:
        """Load `tools_file` (NSS_TOOLS when None) and listen on `port`.

        `disabled_tools` are the names turned off in the panel.
        """
        LOGGER.debug('Trying to connect to port %s...', port)
        # reload on each connect, so a changed tools file applies without restarting Nuke;
        # Python keeps the adapter module it imported first
        self.toolset = load_tools(tools_file, self._editor.builtin_tools())
        self.toolset.disabled = set(disabled_tools)
        # no authentication
        address = QHostAddress.Any if allow_lan else QHostAddress.LocalHost
        return self.listen(address, port)
