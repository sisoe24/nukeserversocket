# coding: utf-8
from __future__ import print_function

import logging

from PySide2.QtCore import QObject
from PySide2.QtNetwork import QTcpServer, QHostAddress

from .socket import Socket
from ..utils import SettingsState

LOGGER = logging.getLogger('NukeServerSocket.server')


class Server(QObject):

    def __init__(self, log_widgets):
        QObject.__init__(self)
        self.settings = SettingsState()

        self.log_widgets = log_widgets

        self.tcp_port = int(self.settings.value('server/port', '54321'))
        LOGGER.debug('server tcp port: %s', self.tcp_port)

        self.server = QTcpServer()
        self.server.newConnection.connect(self._create_connection)
        self.server.acceptError.connect(
            lambda err: LOGGER.error('Server error: %s', err)
        )

        self.socket = None

    def close_server(self):
        """Close server connection."""
        self.server.close()
        self.log_widgets.set_status_text('Disconnected\n----')

    def _create_connection(self):
        while self.server.hasPendingConnections():
            self.socket = Socket(
                self.server.nextPendingConnection(), self.log_widgets
            )
            LOGGER.debug('socket: %s', self.socket)

    def start_server(self):
        """Start server connection.

        Raises:
            ValueError: if connection cannot be made.

        """
        if self.server.listen(QHostAddress.Any, self.tcp_port):
            self.log_widgets.set_status_text(
                "Connected. Server listening to port: %s..." % self.tcp_port)
            return True

        msg = "Server did not initiate. Error: %s." % self.server.errorString()
        self.log_widgets.set_status_text(msg)
        raise ValueError(msg)
