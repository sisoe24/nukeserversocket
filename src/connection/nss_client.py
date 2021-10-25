"""Client code that deals with send nodes and send test functionality."""
# coding: utf-8
from __future__ import print_function, with_statement

import json
import random
import logging

from PySide2.QtCore import QObject, Signal
from PySide2.QtNetwork import QAbstractSocket, QTcpSocket

from .. import nuke
from ..utils import AppSettings, validate_output, connection_timer


LOGGER = logging.getLogger('NukeServerSocket.client')


class NetworkAddresses(object):
    """Data class with network addresses."""

    def __init__(self):
        """Init method for the NetworkAddresses class."""
        self.settings = AppSettings()
        self._local_host = '127.0.0.1'

    @property
    def port(self):  # type: () -> int
        """Get port data from the configuration.ini file."""
        return int(self.settings.value('server/port', 54321))

    @property
    def send_address(self):  # type: () -> str
        """Get host address data from the configuration.ini file."""
        return self.settings.value('server/send_to_address', self._local_host)

    @property
    def local_host(self):  # type: () -> str
        """Get the local host address: 127.0.0.1."""
        return self._local_host


class QBaseClient(QObject):
    """QObject class that sets up a base client-socket logic.

    Signals:
        () timeout: emits when connection timeout has been triggered.
        (str) state_changed: emits when connection state has changed.
    """

    timeout = Signal()
    state_changed = Signal(str)

    def __init__(self, hostname, port):  # type: (str, int) -> None
        """Init method for the QBaseClient class.

        Method creates a QTcpSocket that will listen for incoming connection
        from a client. A timeout timer of 10 seconds will also be created when
        client is not able to connect to the socket.

        Args:
            hostname (str): hostname to connect.
            port (int): port to connect.
        """
        QObject.__init__(self)

        self.tcp_host = hostname
        self.tcp_port = port

        # TODO should make a custom tcp class
        self.socket = QTcpSocket()

        self.socket.readyRead.connect(self.read_data)
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnect)
        self.socket.error.connect(self.on_error)
        self.socket.stateChanged.connect(self.connection_state)

        self.timer = connection_timer(10)
        self.timer.timeout.connect(self._connection_timeout)

    def on_connected(self):
        """When connection is establish do stuff.

        This should be considered as an abstract method that child class
        needs to implement.
        """
        raise NotImplementedError

    def connection_state(self, socket_state):
        """Check che socket connection state.

        If connection state is `ConnectingState`, emits a state_changed:
        'Establishing connection...'. If connection state is `ConnectedState`,
        emits a state_changed: 'Connection successful...' and stops the timer.
        """
        if socket_state == QAbstractSocket.ConnectingState:
            self.state_changed.emit('Establishing connection...')

        if socket_state == QAbstractSocket.ConnectedState:
            self.timer.stop()
            self.state_changed.emit(
                'Connection successful %s:%s' % (self.tcp_host, self.tcp_port)
            )

    def _disconnect(self):
        """Abort socket connection."""
        self.timer.stop()
        self.socket.abort()

    def _connection_timeout(self):
        """Trigger connection timeout event.

        When connection timeout has been triggered emit a `state_changed`:
        'Connection timeout' and close the socket.
        """
        self.state_changed.emit('Connection timeout.\n----')
        LOGGER.debug('Connection Timeout')
        self._disconnect()

    def write_data(self, data):  # type: (dict) -> None
        """Write the data to the socket and disconnected from host.

        Args:
            data (dict): valid dict type that is used from the socket class to
            initialize the code execution.
        """
        self.socket.write(validate_output(json.dumps(data)))

        self.socket.flush()
        self.socket.disconnectFromHost()

    @staticmethod
    def on_disconnect():
        """Disconnect event."""
        LOGGER.debug('Client :: Disconnected from host')

    def connect_to_host(self):
        """Connect to host and start the timeout timer."""
        LOGGER.debug('Client :: Connecting to host: %s %s',
                     self.tcp_host, self.tcp_port)
        self.socket.connectToHost(self.tcp_host, self.tcp_port)
        self.timer.start()

    def on_error(self, error):
        """Error connection event.

        When error occurs, stop the timeout timer and emit a `state_changed`:
        'Error...'.
        """
        self.timer.stop()
        self.state_changed.emit('Error: %s\n----' % self.socket.errorString())
        LOGGER.error("QBaseClient Error: %s", error)

    def read_data(self):
        """Read data ready event."""
        LOGGER.debug('Reading data: %s', self.socket.readAll())


class SendTestClient(QBaseClient):
    """Test connection by sending a sample text to the local host port."""

    def __init__(self, hostname=None, port=None):
        """Init method for the SendTestClient.

        If arguments are omitted, Client will connect to default configuration
        found inside the NetworkAddresses class.

        Args:
            hostname (str, optional): hostname to connect. Defaults to None.
            port (int, optional): port to connect. Defaults to None.
        """
        addresses = NetworkAddresses()
        hostname = hostname or addresses.local_host
        port = port or addresses.port

        QBaseClient.__init__(self, hostname, port)

    def on_connected(self):
        """Override parent method.

        When connection is establish write data to socket.
        """
        LOGGER.debug('SendTestClient :: Connection successful.')
        r = random.randint(1, 50)

        output_text = {
            "text": "from __future__ import print_function; print('Hello from Test Client', %s)" % r,
            "file": "path/to/tmp_file.py"
        }

        self.write_data(output_text)


class SendNodesClient(QBaseClient):
    """Send nuke nodes using between ."""

    def __init__(self, hostname=None, port=None):
        """Init method for the SendNodesClient.

        If arguments are omitted, Client will connect to default configuration
        found inside the NetworkAddresses class.

        Args:
            hostname (str, optional): hostname to connect. Defaults to None.
            port (int, optional): port to connect. Defaults to None.
        """
        LOGGER.debug('Client :: Sending nodes...')

        addresses = NetworkAddresses()
        hostname = hostname or addresses.send_address
        port = port or addresses.port

        QBaseClient.__init__(self, hostname, port)

        self.transfer_data = self.transfer_file_content()

    def on_connected(self):
        """Override parent method.

        When connection is establish write the content of the transfer file to
        the socket.
        """
        LOGGER.debug('Client :: Send nodes connection successful.')
        self.write_data(self.transfer_data)

    @staticmethod
    def transfer_file_content():
        """Get the transfer file content to be sent.

        Returns:
            (dict): a dict to be sent to the socket.
        """
        settings = AppSettings()
        transfer_file = settings.value('path/transfer_file')

        # this will also create the file if it doesn't exists already
        nuke.nodeCopy(transfer_file)

        with open(transfer_file) as file:
            return {"text": file.read(), "file": transfer_file}
