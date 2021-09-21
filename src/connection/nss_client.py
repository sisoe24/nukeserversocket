# coding: utf-8
from __future__ import print_function, with_statement

import json
import socket
import random
import logging

from abc import abstractmethod, ABCMeta

from PySide2.QtNetwork import QHostAddress, QTcpSocket

from .. import nuke
from ..utils import AppSettings, validate_output


LOGGER = logging.getLogger('NukeServerSocket.client')


class NetworkAddresses(object):
    """Convenient class with network addresses"""

    def __init__(self):
        self.settings = AppSettings()

    @property
    def port(self):  # type: () -> int
        """Get port data from the configuration.ini file"""
        return int(self.settings.value('server/port', 54321))

    @property
    def hostname(self):  # type: () -> str
        """Get host address data from the configuration.ini file"""
        return self.settings.value('server/send_to_address', '127.0.0.1')

    @property
    def local_host(self):  # type: () -> QHostAddress
        """Get host address data from the configuration.ini file"""
        return QHostAddress.LocalHost


class QBaseClient(object):
    __metaclass__ = ABCMeta

    def __init__(self, hostname, port):  # type: (str, int) -> None

        self.tcp_host = hostname
        LOGGER.debug('client host: %s', self.tcp_host)

        self.tcp_port = port
        LOGGER.debug('client port: %s', self.tcp_port)

        self.socket = QTcpSocket()
        LOGGER.debug('creating socket: %s', self.socket)

        self.socket.readyRead.connect(self.read_data)
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnect)
        self.socket.error.connect(self.on_error)

    @abstractmethod
    def on_connected(self):
        # TODO: docstring not accurate anymore
        """Method needs to return a string with the text to send write"""

    def write_data(self, data):
        self.socket.write(validate_output(json.dumps(data)))
        LOGGER.debug('message sent: %s', data)

        self.socket.flush()
        self.socket.disconnectFromHost()

    def on_disconnect(self):
        LOGGER.debug('Disconnected from host')

    def connect(self):
        LOGGER.debug('Connecting to host: %s %s', self.tcp_host, self.tcp_port)
        self.socket.connectToHost(self.tcp_host, self.tcp_port)

    def on_error(self, error):
        LOGGER.error("QBaseClient Error: %s", error)

    def read_data(self):
        LOGGER.debug('Reading data: %s', self.socket.readAll())


class TestClient(QBaseClient):
    """Test Socket by send a sample text to the local host port."""

    def __init__(self, addresses=NetworkAddresses()):  # type: (NetworkAddresses) -> None
        QBaseClient.__init__(self, addresses.local_host, addresses.port)

    def on_connected(self):
        LOGGER.debug('TestClient -> Connected to host')
        r = random.randint(1, 50)

        output_text = {
            "text": "from __future__ import print_function; print('Hello from Test Client', %s)" % r,
            "file": "path/to/tmp_file.py"
        }

        self.write_data(output_text)


class QtSendNodesClient(QBaseClient):
    """Send nuke nodes using the Qt client socket."""

    def __init__(self, addresses, transfer_data):  # type: (NetworkAddresses, dict) -> None
        QBaseClient.__init__(self, addresses.hostname, addresses.port)
        self.transfer_data = transfer_data

    def on_connected(self):
        """When connected, send the content of the transfer file as data to the socket."""
        LOGGER.debug('SendNodesClient -> Connected to host')
        self.write_data(self.transfer_data)


class PySendNodesClient(object):
    """Send nuke nodes using the python client socket.

    This class is needed because in nuke 11 there seems to be a bug when sending
    to a different hostname. For now nuke 11 will fallback on python socket module.
    """

    def __init__(self, addresses, transfer_data):  # type: (NetworkAddresses, dict) -> None
        self.tcp_host = addresses.hostname
        self.tcp_port = addresses.port

        self.socket = socket.socket()

        self.transfer_data = transfer_data

    def connect(self):
        try:
            self.socket.connect((self.tcp_host, self.tcp_port))
        except Exception as err:
            LOGGER.error('py.socket connection problem: %s', err)
        else:
            self.on_connected()

    def on_connected(self):
        self.socket.sendall(bytearray(json.dumps(self.transfer_data)))
        self.socket.close()


class SendNodesClient(object):
    """Abstract facade to establish the proper client based on nuke version."""

    def __init__(self):

        transfer_file = self.transfer_file_content()

        addresses = NetworkAddresses()

        if nuke.env['NukeVersionMajor'] == 13:
            self.client = PySendNodesClient(addresses, transfer_file)
        else:
            self.client = QtSendNodesClient(addresses, transfer_file)

    def connect(self):
        self.client.connect()

    def transfer_file_content(self):
        settings = AppSettings()
        transfer_file = settings.value('path/transfer_file')
        nuke.nodeCopy(transfer_file)

        with open(transfer_file) as file:
            return {"text": file.read(), "file": transfer_file}
