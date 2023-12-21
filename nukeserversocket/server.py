from __future__ import annotations

from typing import Optional

from PySide2.QtCore import Slot, Signal
from PySide2.QtNetwork import QTcpServer, QTcpSocket, QHostAddress

from .received_data import ReceivedData
from .editor_controller import BaseEditorController


class NssServer(QTcpServer):
    """NukeServerSocket server.

    This class is responsible for receiving data from the client, and sending the output back.

    Signals:
        on_data_received (str): Signal emitted when data is received from the client.
        on_data_written (str): Signal emitted when data is written to the client.

    """
    on_data_received = Signal(str)
    on_data_written = Signal(str)

    def __init__(self, editor: BaseEditorController, parent=None):
        super().__init__(parent)

        self._editor = editor
        self._socket: Optional[QTcpSocket] = None

        self.newConnection.connect(self._on_new_connection)

    @Slot()
    def _on_socket_ready(self):
        if not self._socket:
            raise RuntimeError('Socket is not set.')

        # parse the incoming data
        data = ReceivedData(self._socket.readAll().data())

        output = self._editor.run(data)
        self.on_data_received.emit(data.text)
        self.on_data_written.emit(output)

        self._socket.write(output.encode('utf-8'))
        self._socket.close()

    def _on_new_connection(self) -> None:
        while self.hasPendingConnections():
            self._socket = self.nextPendingConnection()
            self._socket.readyRead.connect(self._on_socket_ready)

    def try_connect(self, port: int) -> bool:
        return self.listen(QHostAddress.Any, port)
