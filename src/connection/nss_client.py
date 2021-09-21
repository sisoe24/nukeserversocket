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
    def __init__(self):
        self.settings = AppSettings()

    @property
    def port(self):
        return int(self.settings.value('server/port', 54321))

    @property
    def hostname(self):
        return self.settings.value('server/send_to_address', '127.0.0.1')

    @property
    def local_host(self):
        return QHostAddress.LocalHost


class Client(object):
    __metaclass__ = ABCMeta

    def __init__(self, hostname, port):  # type: (str, int) -> None

        self.tcp_host = hostname
        self.settings = AppSettings()

        # BUG: Nuke 11 host like: 192.168.1.44 will fail so for now fallback on local
        # if nuke.env['NukeVersionMajor'] == 11:
        #     self.tcp_host = '127.0.0.1'

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
        self.socket.write(validate_output(data))
        LOGGER.debug('message sent: %s', data)

        self.socket.flush()
        self.socket.disconnectFromHost()

    def on_disconnect(self):
        LOGGER.debug('Disconnected from host')

    def send_data(self):
        LOGGER.debug('Sending message to host: %s %s',
                     self.tcp_host, self.tcp_port)
        self.socket.connectToHost(self.tcp_host, self.tcp_port)

    def on_error(self, error):
        LOGGER.error("Client Error: %s", error)

    def read_data(self):
        LOGGER.debug('Reading data: %s', self.socket.readAll())


class TestClient(Client):
    """Test Socket by send a sample text to the local host port."""

    def __init__(self, addresses=NetworkAddresses()):  # type: (NetworkAddresses) -> None
        Client.__init__(self, addresses.local_host, addresses.port)

    def on_connected(self):
        LOGGER.debug('TestClient -> Connected to host')
        r = random.randint(1, 50)

        output_text = {
            "text": "from __future__ import print_function; print('Hello from Test Client', %s)" % r,
            "file": "path/to/tmp_file.py"
        }

        self.write_data(json.dumps(output_text))


class QtSendNodesClient(Client):
    def __init__(self, addresses, transfer_file):  # type: (NetworkAddresses, str) -> None
        Client.__init__(self, addresses.hostname, addresses.port)

        self.transfer_file = transfer_file

    def on_connected(self):
        """When connected, send the content of the transfer file as data to the socket."""
        LOGGER.debug('SendNodesClient -> Connected to host')

        nuke.nodeCopy(self.transfer_file)

        with open(self.transfer_file) as file:
            output_text = {
                "text": file.read(),
                "file": self.transfer_file
            }

        self.write_data(json.dumps(output_text))


class PySendNodesClient(object):
    def __init__(self, addresses, transfer_file):  # type: (NetworkAddresses, str) -> None

        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((addresses.hostname, addresses.port))

        self.transfer_file = transfer_file

    def send_data(self):

        with open(self.transfer_file) as file:
            output_text = {
                "text": file.read(),
                "file": self.transfer_file
            }

        self.socket.sendall(bytearray(json.dumps(output_text)))
        data = self.socket.recv(1024)
        print("➡ data :", data)
        self.socket.close()


class SendNodesClient(object):
    def __init__(self):
        settings = AppSettings()

        transfer_file = settings.value('path/transfer_file')

        if nuke.env['NukeVersionMajor'] == 13:
            print('nuke11')
            self.client = PySendNodesClient(NetworkAddresses(), transfer_file)
        else:
            print('nuke12/13')
            self.client = QtSendNodesClient(NetworkAddresses(), transfer_file)

    def send_data(self):
        self.client.send_data()
