# coding: utf-8
from __future__ import print_function

import logging

from PySide2.QtCore import QObject, QTimer, Signal
from PySide2.QtNetwork import QAbstractSocket, QTcpServer, QHostAddress

from .nss_socket import Socket
from ..utils import AppSettings, connection_timer

LOGGER = logging.getLogger('NukeServerSocket.server')


class Server(QObject):
    timeout = Signal()
    state_changed = Signal(str)
    socket_ready = Signal(object)

    def __init__(self):
        QObject.__init__(self)
        self.settings = AppSettings()

        self.tcp_port = int(self.settings.value('server/port', '54321'))
        LOGGER.debug('server tcp port: %s', self.tcp_port)

        self.server = QTcpServer()
        self.server.newConnection.connect(self._create_connection)
        self.server.acceptError.connect(
            lambda err: LOGGER.error('Server error: %s', err)
        )

        self.socket = None

        self.timer = connection_timer(60 * 5)
        self.timer.timeout.connect(self.timeout.emit)

    def connection_state(self, state):
        if state == QAbstractSocket.UnconnectedState:
            self.timer.start()

    def close_server(self):
        """Close server connection."""
        self.server.close()
        self.timer.stop()
        self.state_changed.emit('Disconnected\n----')
        LOGGER.debug('Disconnected')

    def _create_connection(self):
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.stateChanged.connect(self.connection_state)

            self.socket = Socket(socket)
            self.socket_ready.emit(self.socket)
            LOGGER.debug('socket: %s', self.socket)

    def start_server(self):
        """Start server connection.

        Raises:
            ValueError: if connection cannot be made.

        """
        if self.server.listen(QHostAddress.Any, self.tcp_port):
            self.timer.start()
            self.state_changed.emit(
                "Connected. Server listening to port: %s..." % self.tcp_port)
            return True

        msg = "Server did not initiate. Error: %s." % self.server.errorString()
        self.state_changed.emit(msg)

        raise ValueError(msg)
