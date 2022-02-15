"""Server module that deals with creates a socket when connection is valid."""
# coding: utf-8
from __future__ import print_function

import logging

from PySide2.QtCore import QObject, Signal
from PySide2.QtNetwork import QAbstractSocket, QTcpServer, QHostAddress

from .nss_socket import QSocket
from ..utils import AppSettings, connection_timer

LOGGER = logging.getLogger('NukeServerSocket.server')


class QServer(QObject):
    """QObject Server class that deals with the connection.

    Class will also emit signal when connection status has changed.

    Signal:
        (None) timeout: emit when the timeout event has been triggered.
        (str) state_changed: emits when the connection state has changed
        (QSocket) socket_ready: emits the socket class that has been created
        when connection is successful.
    """

    timeout = Signal()
    state_changed = Signal(str)
    socket_ready = Signal(object)

    def __init__(self):
        """Init method for the QServer class."""
        QObject.__init__(self)
        LOGGER.debug('-> QServer :: Starting...')
        self.settings = AppSettings()

        self.tcp_port = int(self.settings.value('server/port', '54321'))

        self.server = QTcpServer()
        self.server.newConnection.connect(self._create_connection)
        self.server.acceptError.connect(
            lambda err: LOGGER.error('QServer error: %s', err)
        )

        self.socket = None

        # multiple time by 60 to get seconds
        self.timer = connection_timer(
            int(AppSettings().value('timeout/server', 6)) * 60
        )
        self.timer.timeout.connect(self.timeout.emit)

    def connection_state(self, state):
        """Check if connection state.

        If connection state is unconnected, start the timeout timer.
        """
        if state == QAbstractSocket.UnconnectedState:
            self.timer.start()

    def close_server(self):
        """Close server connection.

        Method will also stop the timer and emit the 'Disconnected' state.
        """
        self.server.close()
        self.timer.stop()
        self.state_changed.emit('Disconnected\n----')
        LOGGER.debug('QServer :: Closing <-')

    def _create_connection(self):
        """Establish connection and create a new socket.

        When connection is successful, will create a socket and emit
        `socket_ready` signal.
        """
        while self.server.hasPendingConnections():
            socket = self.server.nextPendingConnection()
            socket.stateChanged.connect(self.connection_state)

            self.socket = QSocket(socket)
            self.socket_ready.emit(self.socket)

    def start_server(self):
        """Start server connection.

        QServer will listen on Any host address and the tcp port specified in
        the config file.

        Raises:
            RuntimeError: if connection cannot be made.

        """
        if self.server.listen(QHostAddress.Any, self.tcp_port):
            self.timer.start()
            self.state_changed.emit(
                "Connected. Server listening to port: %s..." % self.tcp_port)
            return True

        msg = "Server did not initiate. Error: %s." % self.server.errorString()
        self.state_changed.emit(msg)

        raise RuntimeError(msg)
