from __future__ import annotations

import json
from typing import TYPE_CHECKING, Dict, Optional

from ._qt import QTimer, Signal, QWidget, QTcpServer, QTcpSocket, QHostAddress

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

    MAX_REQUEST_BYTES = 10 * 1024 * 1024
    REQUEST_IDLE_MS = 3000

    def __init__(self, editor: BaseController, parent: Optional[QWidget] = None):
        super().__init__(parent)

        self._editor = editor
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
        LOGGER.info('Received data from client.')
        LOGGER.debug('Socket ready.')

        # TCP can split a request across several reads
        buffer = self._buffers.setdefault(socket, bytearray())
        buffer.extend(socket.readAll().data())

        if self._is_incomplete(buffer):
            LOGGER.debug('Incomplete request (%s bytes). Waiting for more data.', len(buffer))
            idle_timer.start()
            return

        idle_timer.stop()
        self._reply(socket)

    def _reply(self, socket: QTcpSocket):
        data = ReceivedData(bytes(self._buffers.pop(socket)))

        if not data.text:
            # invalid JSON or empty text: running it would only echo the editor's old output
            output = 'NukeServerSocket error: no code received. Expected JSON with a non-empty "text" field.'
        else:
            try:
                output = self._editor.execute(data)
            except RuntimeError as err:
                # e.g. the Nuke Script Editor is not open; reply so the client does not hang
                LOGGER.error('Execution failed: %s', err)
                output = str(err)

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

            # malformed JSON never completes, so stop waiting once the data stops
            idle_timer = QTimer(socket)
            idle_timer.setSingleShot(True)
            idle_timer.setInterval(self.REQUEST_IDLE_MS)
            idle_timer.timeout.connect(lambda socket=socket: self._reply(socket))

            socket.disconnected.connect(idle_timer.stop)
            socket.disconnected.connect(lambda socket=socket: self._buffers.pop(socket, None))
            socket.disconnected.connect(socket.deleteLater)

            LOGGER.debug('Socket connected.')
            # bind each socket to its own handler, so replies go to the right client
            socket.readyRead.connect(
                lambda socket=socket, idle_timer=idle_timer: self._on_socket_ready(
                    socket, idle_timer)
            )

    def try_connect(self, port: int, allow_lan: bool = False) -> bool:
        LOGGER.debug('Trying to connect to port %s...', port)
        # no authentication
        address = QHostAddress.Any if allow_lan else QHostAddress.LocalHost
        return self.listen(address, port)
