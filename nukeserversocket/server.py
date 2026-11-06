from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from ._qt import Signal, QWidget, QTcpServer, QTcpSocket, QHostAddress

from .tools import ToolSet, load_tools, parse_tool_request, handle_tool_request
from .logger import get_logger
from .received_data import ReceivedData

if TYPE_CHECKING:
    from .controllers.base import BaseController

LOGGER = get_logger()


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

        raw = socket.readAll().data()
        client = socket.peerAddress().toString()

        request = parse_tool_request(raw)
        if request is not None:
            if request.get('file'):
                client += f' ({request["file"]})'
            LOGGER.info('Tool request from %s: %s', client, request.get('call_tool', 'list_tools'))
            self._reply(socket, handle_tool_request(self.toolset, request))
            return

        data = ReceivedData(raw)
        if data.file:
            client += f' ({data.file})'

        if not self.toolset.allow_code:
            LOGGER.warning('Rejected code from %s: code execution is off.', client)
            output = ('NukeServerSocket error: code execution is turned off by the tool file. '
                      'Use the tools it lists instead.')
        elif not data.text:
            # invalid JSON or empty text: running it would only echo the editor's old output
            LOGGER.warning('Rejected request from %s: no code received.', client)
            output = 'NukeServerSocket error: no code received. Expected JSON with a non-empty "text" field.'
        else:
            LOGGER.info('Running code from %s: %s', client, data.text.strip().partition('\n')[0][:80])
            try:
                output = self._editor.execute(data)
            except RuntimeError as err:
                # e.g. the Nuke Script Editor is not open; reply so the client does not hang
                LOGGER.error('Execution failed: %s', err)
                output = f'NukeServerSocket error: {err}'

        self._reply(socket, output)

    def _reply(self, socket: QTcpSocket, output: str) -> None:
        self.on_data_received.emit()

        LOGGER.info('Writing output to back socket...')

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

    def try_connect(self, port: int, allow_lan: bool = False) -> bool:
        LOGGER.debug('Trying to connect to port %s...', port)
        # reload on each connect, so a changed tool file applies without restarting Nuke
        self.toolset = load_tools()
        # no authentication
        address = QHostAddress.Any if allow_lan else QHostAddress.LocalHost
        return self.listen(address, port)
