import os
import json
from typing import Optional

from PySide2.QtCore import Signal, QObject
from PySide2.QtNetwork import QTcpServer, QTcpSocket, QHostAddress


def server_factory() -> QTcpServer:
    """Factory function to create a new server object.

    Returns:
        NssServer: NssServer object.
    """
    if os.getenv('NUKE_SERVER_SOCKET_CONNECTION_TYPE', 'tcp') == 'websocket':
        raise NotImplementedError('Websocket not implemented yet.')
    return QTcpServer()


class NssServer(QObject):
    on_new_connection = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.server = server_factory()
        self.server.newConnection.connect(self._on_new_connection)

        self._socket: Optional[QTcpSocket] = None

    def _on_socket_ready(self):
        print('➡ data :', self._socket.readAll())
        self._socket.write(b'hello')
        self._socket.close()

    def _on_new_connection(self):
        while self.server.hasPendingConnections():
            self._socket = self.server.nextPendingConnection()
            self._socket.readyRead.connect(self._on_socket_ready)

            self._socket.connected.connect(lambda: print('connected'))
            self._socket.disconnected.connect(lambda: print('disconnected'))
            self._socket.error.connect(lambda err: print('error', err))

    def is_listening(self):
        return self.server.isListening()

    def close(self):
        self.server.close()

    def listen(self, port: int):
        if self.server.listen(QHostAddress.Any, port):
            return True
        return False
