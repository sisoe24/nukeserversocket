# coding: utf-8
from __future__ import print_function

import logging

from PySide2.QtCore import QObject
from PySide2.QtNetwork import QTcpServer, QHostAddress

from .socket import Socket
from ..utils import SettingsState

LOGGER = logging.getLogger('NukeServerSocket.server')


class Server(QObject):
    def __init__(self, status_widget):
        QObject.__init__(self)
        self.settings = SettingsState()
        self.settings.verify_port_config()

        self.status_widget = status_widget

        self.tcp_port = int(self.settings.value('server/port', '54321'))
        LOGGER.debug('server tcp port: %s', self.tcp_port)

        self.server = QTcpServer()
        self.server.newConnection.connect(self._create_connection)
        self.server.acceptError.connect(
            lambda err: LOGGER.error('Server error: %s', err)
        )

        self.socket = None

    def _create_connection(self):
        while self.server.hasPendingConnections():
            self.socket = Socket(
                self.server.nextPendingConnection(), self.status_widget)
            LOGGER.debug('socket: %s', self.socket)

    def start_server(self):
        if self.server.listen(QHostAddress.Any, self.tcp_port):
            self.status_widget.set_status_text(
                "Server listening to port: %s " % self.tcp_port)
            return True

        self.status_widget.set_status_text(
            "Server did not initiate. Error: %s." % self.server.errorString()
        )

        return False
