# coding: utf-8
from __future__ import print_function, with_statement

import json
import random
import logging

from abc import abstractmethod, ABCMeta

from PySide2.QtCore import QObject, Qt, Signal
from PySide2.QtNetwork import QTcpSocket

from ..utils import SettingsState, validate_output


LOGGER = logging.getLogger('NukeServerSocket.client')


class Client(object):
    __metaclass__ = ABCMeta

    def __init__(self):

        self.settings = SettingsState()

        self.tcp_host = "127.0.0.1"
        LOGGER.debug('client host: %s', self.tcp_host)

        self.tcp_port = int(self.settings.value('server/port', '54321'))
        LOGGER.debug('client port: %s', self.tcp_port)

        self.socket = QTcpSocket()
        LOGGER.debug('creating socket: %s', self.socket)

        self.socket.readyRead.connect(self.read_data)
        self.socket.connected.connect(self.on_connected)
        self.socket.error.connect(self.on_error)

    @abstractmethod
    def on_connected(self):
        """Method needs to return a string with the text to send write"""

    def write_data(self, data):
        self.socket.write(data)
        LOGGER.debug('message sent: %s', data)

        self.socket.flush()
        self.socket.disconnectFromHost()
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
    def __init__(self):
        Client.__init__(self)

    def on_connected(self):
        LOGGER.debug('TestClient -> Connected to host')
        r = random.randint(1, 50)

        output_text = {
            "text": "from __future__ import print_function; print('Hello from Test Client', %s)" % r,
            "file": "path/to/tmp_file.py"
        }

        self.write_data(json.dumps(output_text))


class NodeClient(Client):
    def __init__(self):
        Client.__init__(self)

    def on_connected(self):
        LOGGER.debug('NodeClient -> Connected to host')

        output_text = {
            "text": "print('SEND NODES %s %s')" % (self.tcp_port, self.tcp_host),
            "file": "path/to/tmp_file.py"
        }

        self.write_data(json.dumps(output_text))
