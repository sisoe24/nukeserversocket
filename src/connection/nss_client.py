# coding: utf-8
from __future__ import print_function, with_statement

import json
import random
import logging

from abc import abstractmethod, ABCMeta

from PySide2.QtCore import QObject, Signal
from PySide2.QtNetwork import QAbstractSocket, QTcpSocket

from .. import nuke
from ..utils import AppSettings, validate_output, connection_timer


LOGGER = logging.getLogger('NukeServerSocket.client')


class NetworkAddresses(object):
    """Convenient class with network addresses"""

    def __init__(self):
        self.settings = AppSettings()
        self._local_host = '127.0.0.1'

    @property
    def port(self):  # type: () -> int
        """Get port data from the configuration.ini file"""
        return int(self.settings.value('server/port', 54321))

    @property
    def send_address(self):  # type: () -> str
        """Get host address data from the configuration.ini file"""
        return self.settings.value('server/send_to_address', self._local_host)

    @property
    def local_host(self):  # type: () -> str
        """Get local host address QHostAddress object"""
        return self._local_host


class QBaseClient(QObject):
    # TODO: would have liked to have this class as an abstract class but
    # will complain in python 2 because its not a base object

    timeout = Signal()
    state_changed = Signal(str)

    def __init__(self, hostname, port):  # type: (str, int) -> None
        QObject.__init__(self)

        self.tcp_host = hostname
        self.tcp_port = port

        self.socket = QTcpSocket()

        self.socket.readyRead.connect(self.read_data)
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnect)
        self.socket.error.connect(self.on_error)
        self.socket.stateChanged.connect(self.connection_state)

        self.timer = connection_timer(10)
        self.timer.timeout.connect(self._connection_timeout)

    def on_connected(self):
        """This should be considered as an abstract method that child class needs
        to implement.
        """

    def connection_state(self, socket_state):
        if socket_state == QAbstractSocket.ConnectingState:
            self.state_changed.emit('Establishing connection...')

        if socket_state == QAbstractSocket.ConnectedState:
            self.timer.stop()
            self.state_changed.emit(
                'Connection successful %s:%s' % (self.tcp_host, self.tcp_port)
            )

    def _connection_timeout(self):
        self.state_changed.emit('Connection timeout.\n----')
        LOGGER.debug('Connection Timeout')
        self.socket.abort()

    def write_data(self, data):
        self.socket.write(validate_output(json.dumps(data)))

        self.socket.flush()
        self.socket.disconnectFromHost()

    def on_disconnect(self):
        LOGGER.debug('Client :: Disconnected from host')

    def connect_to_host(self):
        LOGGER.debug('Client :: Connecting to host: %s %s',
                     self.tcp_host, self.tcp_port)
        self.socket.connectToHost(self.tcp_host, self.tcp_port)
        self.timer.start()

    def on_error(self, error):
        self.timer.stop()
        self.state_changed.emit('Error: %s\n----' % self.socket.errorString())
        LOGGER.error("QBaseClient Error: %s", error)

    def read_data(self):
        LOGGER.debug('Reading data: %s', self.socket.readAll())


class SendTestClient(QBaseClient):
    """Test Socket by send a sample text to the local host port."""

    def __init__(self, hostname=None, port=None):

        addresses = NetworkAddresses()
        hostname = hostname or addresses.local_host
        port = port or addresses.port

        QBaseClient.__init__(self, hostname, port)

    def on_connected(self):
        LOGGER.debug('SendTestClient :: Connection successful.')
        r = random.randint(1, 50)

        output_text = {
            "text": "from __future__ import print_function; print('Hello from Test Client', %s)" % r,
            "file": "path/to/tmp_file.py"
        }

        self.write_data(output_text)


class SendNodesClient(QBaseClient):
    """Send nuke nodes using the Qt client socket."""

    def __init__(self, hostname=None, port=None):
        LOGGER.debug('Client :: Sending nodes...')

        addresses = NetworkAddresses()
        hostname = hostname or addresses.send_address
        port = port or addresses.port

        QBaseClient.__init__(self, hostname, port)

        self.transfer_data = self.transfer_file_content()

    def on_connected(self):
        """When connected, send the content of the transfer file as data to the socket."""
        LOGGER.debug('Client :: Send nodes connection successful.')
        self.write_data(self.transfer_data)

    def transfer_file_content(self):
        """Get the transfer file content to be sent to socket."""
        settings = AppSettings()
        transfer_file = settings.value('path/transfer_file')

        # this will also create the file if it doesn't exists already
        nuke.nodeCopy(transfer_file)

        with open(transfer_file) as file:
            return {"text": file.read(), "file": transfer_file}
