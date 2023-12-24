from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from PySide2.QtCore import Slot, Signal
from PySide2.QtNetwork import QTcpServer, QTcpSocket, QHostAddress

from .logger import get_logger
from .received_data import ReceivedData

if TYPE_CHECKING:
    from .editor_controller import EditorController

LOGGER = get_logger()


class NssServer(QTcpServer):
    """NukeServerSocket server.

    This class is responsible for receiving data from the client, and sending the output back.

    Signals:
        on_data_written (): Signal emitted when data is written to the client.

    """
    on_data_received = Signal()

    def __init__(self, editor: EditorController, parent=None):
        super().__init__(parent)

        self._editor = editor
        self._socket: Optional[QTcpSocket] = None

        self.newConnection.connect(self._on_new_connection)
        self.acceptError.connect(lambda err: LOGGER.error('Server error: %s', self.errorString()))

    @Slot()
    def _on_socket_ready(self):
        LOGGER.info('Received data from client.')
        LOGGER.debug('Socket ready.')

        if not self._socket:
            LOGGER.error('Socket is not set.')
            raise RuntimeError('Socket is not set.')

        # parse the incoming data
        data = ReceivedData(self._socket.readAll().data())

        output = self._editor.run(data)

        self.on_data_received.emit()

        LOGGER.info('Writing output to back socket...')
        self._socket.write(output.encode('utf-8'))
        LOGGER.debug('Output: %s', output.replace('\n', '\\n'))

        self._socket.close()
        LOGGER.debug('Socket closed.')

    def _on_new_connection(self) -> None:
        LOGGER.debug('New connection.')
        while self.hasPendingConnections():

            LOGGER.debug('Pending connection.')
            self._socket = self.nextPendingConnection()
            self._socket.error.connect(lambda err: LOGGER.error('Socket error: %s', err))

            LOGGER.debug('Socket connected.')
            self._socket.readyRead.connect(self._on_socket_ready)

    def try_connect(self, port: int) -> bool:
        LOGGER.debug('Trying to connect to port %s...', port)
        return self.listen(QHostAddress.Any, port)
