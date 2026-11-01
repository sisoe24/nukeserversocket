from __future__ import annotations

from typing import TYPE_CHECKING, Union, Optional

from nukeserversocket._qt.QtCore import Signal
from nukeserversocket._qt.QtNetwork import QTcpServer, QTcpSocket, QHostAddress
from nukeserversocket._qt.QtWidgets import QWidget

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

        self.newConnection.connect(self._on_new_connection)
        self.acceptError.connect(lambda err: LOGGER.error('Server error: %s', self.errorString()))

    def _on_socket_ready(self, socket: QTcpSocket):
        LOGGER.info('Received data from client.')
        LOGGER.debug('Socket ready.')

        # parse the incoming data
        data = ReceivedData(socket.readAll().data())

        output = self._editor.execute(data)

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

            LOGGER.debug('Socket connected.')
            # bind each socket to its own handler, so replies go to the right client
            socket.readyRead.connect(lambda socket=socket: self._on_socket_ready(socket))

    def try_connect(self, port: int) -> bool:
        LOGGER.debug('Trying to connect to port %s...', port)
        return self.listen(QHostAddress.Any, port)
