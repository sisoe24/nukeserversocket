from __future__ import annotations

import time
import logging
from typing import TYPE_CHECKING, Tuple, Optional

from ._qt import Signal, QWidget, QTcpServer, QTcpSocket, QHostAddress

from .tools import ToolSet, load_tools, parse_tool_request, handle_tool_request
from .logger import get_logger
from .received_data import ReceivedData

if TYPE_CHECKING:
    from .controllers.base import BaseController

LOGGER = get_logger()

# the mark the MCP bridge sends as its "file"
MCP_CLIENT = 'MCP'


def _source(address: QHostAddress, file: str) -> str:
    """Name the client the way the Logs show it, e.g. "(MCP)" or "(127.0.0.1 main.py)"."""
    if file == MCP_CLIENT:
        return f'({MCP_CLIENT})' if address.isLoopback() else f'({MCP_CLIENT} at {address.toString()})'
    return f'({address.toString()} {file})' if file else f'({address.toString()})'


class NssServer(QTcpServer):
    """NukeServerSocket server.

    This class is responsible for receiving data from the client, and sending the output back.

    Signals:
        on_data_received (): Signal emitted when data is received from the client.

    """
    on_data_received = Signal()

    def __init__(self, editor: BaseController, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._editor = editor
        self.toolset = ToolSet()

        self.newConnection.connect(self._on_new_connection)
        self.acceptError.connect(lambda err: LOGGER.error('Server error: %s', self.errorString()))

    def _on_socket_ready(self, socket: QTcpSocket):
        LOGGER.debug('Socket ready.')

        started = time.perf_counter()
        raw = socket.readAll().data()

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
        if not self.toolset.allow_code:
            reason = self.toolset.code_off_reason
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
            socket.disconnected.connect(socket.deleteLater)

            LOGGER.debug('Socket connected.')
            # bind each socket to its own handler, so replies go to the right client
            socket.readyRead.connect(lambda socket=socket: self._on_socket_ready(socket))

    def try_connect(self, port: int, allow_lan: bool = False,
                    tools_file: Optional[str] = None) -> bool:
        """Load `tools_file` (NSS_TOOLS when None) and listen on `port`."""
        LOGGER.debug('Trying to connect to port %s...', port)
        # reload on each connect, so a changed tool file applies without restarting Nuke
        self.toolset = load_tools(tools_file)
        # no authentication
        address = QHostAddress.Any if allow_lan else QHostAddress.LocalHost
        return self.listen(address, port)
