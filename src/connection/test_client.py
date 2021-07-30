# coding: utf-8
from __future__ import print_function, with_statement

import json
import random
import logging

from PySide2.QtNetwork import QTcpSocket

from NukeServerSocket.src.utils import Settings, validate_output


LOGGER = logging.getLogger('NukeServerSocket.client')


class ClientTest:
    def __init__(self):
        self.settings = Settings()

        self.tcp_host = "127.0.0.1"
        LOGGER.debug('client host: %s', self.tcp_host)

        self.tcp_port = int(self.settings.value('server/port', '54321'))
        LOGGER.debug('client port: %s', self.tcp_port)

        self.socket = QTcpSocket()
        LOGGER.debug('creating socket: %s', self.socket)

        self.socket.readyRead.connect(self.read_data)
        self.socket.connected.connect(self.on_connected)
        self.socket.error.connect(self.on_error)

    def send_message(self):
        LOGGER.debug('Sending message to host: %s %s',
                     self.tcp_host, self.tcp_port)
        self.socket.connectToHost(self.tcp_host, self.tcp_port)

    def on_error(self, error):
        LOGGER.error("Client Error: %s", error)

    def on_connected(self):
        LOGGER.debug('Connected to host')
        r = random.randint(1, 50)

        output_text = {
            "text": "from __future__ import print_function; print('Hello from Test Client', %s)" % r,
            "file": "path/to/tmp_file.py"
        }
        output_text = json.dumps(output_text)

        self.socket.write(validate_output(output_text))
        LOGGER.debug('message sent: %s', output_text)

        self.socket.flush()
        self.socket.disconnectFromHost()
        LOGGER.debug('Disconnected from host')

    def read_data(self):
        LOGGER.debug('Reading data: %s', self.socket.readAll())
