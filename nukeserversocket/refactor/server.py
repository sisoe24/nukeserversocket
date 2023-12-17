from __future__ import annotations

from typing import Optional

from PySide2.QtCore import Slot, Signal
from PySide2.QtNetwork import QTcpServer, QTcpSocket, QHostAddress

from .controller import EditorController
from .received_data import ReceivedData


class NssServer(QTcpServer):
    on_new_connection = Signal()
    on_data_received = Signal(str)
    on_data_written = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.newConnection.connect(self._on_new_connection)

        self._socket: Optional[QTcpSocket] = None

        controller = EditorController.get_instance()
        if not controller:
            raise RuntimeError('Controller is not set.')
        self._controller = controller()

    @Slot()
    def _on_socket_ready(self):
        if not self._socket:
            raise RuntimeError('Socket is not set.')

        data = ReceivedData(self._socket.readAll().data())

        output = self._controller.run(data)

        self.on_data_received.emit(data.text)
        self.on_data_written.emit(output)

        self._socket.write(output.encode('utf-8'))
        self._socket.close()

    def _on_new_connection(self) -> None:
        while self.hasPendingConnections():
            self._socket = self.nextPendingConnection()
            self._socket.readyRead.connect(self._on_socket_ready)

    def try_connect(self, port: int) -> bool:
        return bool(self.listen(QHostAddress.Any, port))
