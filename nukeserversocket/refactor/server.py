from __future__ import annotations

import os
import json
from typing import Optional
from dataclasses import field, dataclass

from PySide2.QtCore import Slot, Signal, QObject
from PySide2.QtNetwork import QTcpServer, QTcpSocket, QHostAddress


def server_factory() -> QTcpServer:
    """Factory function to create a new server object.

    Returns:
        NssServer: NssServer object.
    """
    if os.getenv('NUKE_SERVER_SOCKET_CONNECTION_TYPE', 'tcp') == 'websocket':
        raise NotImplementedError('Websocket not implemented yet.')
    return QTcpServer()


@dataclass
class ReceivedData:
    data: str
    file: str = field(init=False)
    text: str = field(init=False)

    def __post_init__(self):

        try:
            d = json.loads(self.data)
        except json.JSONDecodeError as e:
            raise ValueError('Data is not a valid json.') from e

        self.text = d.get('text')
        if not self.text:
            raise ValueError('Data does not contain a text field.')

        # file is optional as is only used to show the file name in the output
        self.file = d.get('file')


class NssServer(QObject):
    on_new_connection = Signal()
    on_data_received = Signal(str)
    on_data_written = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.server = server_factory()
        self.server.newConnection.connect(self._on_new_connection)

        self._socket: Optional[QTcpSocket] = None

    @Slot()
    def _on_socket_ready(self):

        data = ReceivedData(self._socket.readAll().data())

        output = f'File: {data.file}\nText: {data.text}'

        self.on_data_received.emit(data.text)
        self.on_data_written.emit(output)

        self._socket.write(output.encode('utf-8'))
        self._socket.close()

    def _on_new_connection(self) -> None:
        while self.server.hasPendingConnections():
            self._socket = self.server.nextPendingConnection()

            self._socket.readyRead.connect(self._on_socket_ready)
            self._socket.connected.connect(lambda: print('connected'))
            self._socket.disconnected.connect(lambda: print('disconnected'))
            self._socket.error.connect(lambda err: print('error', err))

    def is_listening(self) -> bool:
        return self.server.isListening()

    def close(self) -> None:
        self.server.close()

    def listen(self, port: int) -> bool:
        return bool(self.server.listen(QHostAddress.Any, port))
