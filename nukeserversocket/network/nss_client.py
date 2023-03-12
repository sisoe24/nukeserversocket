"""Client code that deals with send nodes and send test functionality."""
# coding: utf-8

import json
import random
import logging

from PySide2.QtCore import Signal, QObject
from PySide2.QtNetwork import QTcpSocket, QAbstractSocket

from ..widgets import Timer
from ..settings import AppSettings
from .nss_socket import socket_factory
from ..local.mock import nuke

if nuke.env.get('NukeVersionMajor') < 14:
    from PySide2.QtWebSockets import QWebSocket

LOGGER = logging.getLogger('nukeserversocket')


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
    def send_to_address(self):  # type: () -> str
        """Get host address data from the configuration.ini file."""
        return self.settings.value('server/send_to_address', self._local_host)

    @property
    def local_host(self):  # type: () -> str
        """Get the local host address: 127.0.0.1."""
        return self._local_host

# TODO: Refactor QBaseCLient: revisit how the socket is coupled with the class


class QBaseClient(QObject):
    """QObject class that sets up a base client-socket logic.

    Signals:
        () timeout: emits when connection timeout has been triggered.
        (str) state_changed: emits when connection state has changed.
        (bool) client_ready: emits when client is ready to connect again.
        (str) client_timeout: emits every second to indicate the timeout status
    """

    timeout = Signal()
    state_changed = Signal(str)
    client_ready = Signal(bool)
    client_timeout = Signal(str)

    def __init__(self, hostname, port):  # type: (str, int) -> None
        """Init method for the QBaseClient class.

        Create a QTcpSocket that listens for incoming connection from a client.
        It also starts a timer of 10 seconds for client timeout.

        Args:
            hostname (str): hostname to connect.
            port (int): port to connect.
        """
        QObject.__init__(self)

        self.tcp_host = hostname
        self.tcp_port = port

        self.socket = socket_factory(
            QTcpSocket() if AppSettings().get_bool('connection_type/tcp') else QWebSocket()
        )

        LOGGER.debug('Initialize QBaseClient socket: %s', type(self.socket))

        self.socket._socket.connected.connect(self.on_connected)
        self.socket._socket.error.connect(self.on_error)
        self.socket._socket.stateChanged.connect(self.connection_state)

        self.timer = Timer(int(AppSettings().value('timeout/client', 10)))
        self.timer.time.connect(self.client_timeout.emit)
        self.timer._timer.timeout.connect(self._connection_timeout)

    def on_connected(self):
        """When connection is establish do stuff.

        This should be considered as an abstract method that a child class
        needs to implement.
        """
        raise NotImplementedError('Child class must implement method.')

    def on_error(self, error):
        """Error connection event.

        When an error occurs, stop the timer and emit a `state_changed` signal.
        """
        self.timer.stop()
        self.state_changed.emit('Error: %s\n---' % self.socket._socket.errorString())
        LOGGER.error('QBaseClient Error: %s', error)

    def connection_state(self, socket_state):
        """Check che socket connection state and emit a signal."""
        if socket_state == QAbstractSocket.ConnectingState:
            self.state_changed.emit('Establishing connection...')

        if socket_state == QAbstractSocket.ConnectedState:
            self.timer.stop()
            self.state_changed.emit(
                'Connection successful %s:%s' % (self.tcp_host, self.tcp_port)
            )

        if socket_state == QAbstractSocket.UnconnectedState:
            self.client_ready.emit(True)

    def _disconnect(self):
        """Abort socket connection."""
        self.timer.stop()
        self.socket.abort()

    def _connection_timeout(self):
        """Trigger connection timeout event.

        When connection timeout has been triggered, emit a `state_changed`
        signal and close the socket.
        """
        self.state_changed.emit('Connection timeout.\n----')
        LOGGER.debug('QBaseClient :: Connection Timeout')
        self._disconnect()

    def write_data(self, data):  # type: (dict) -> None
        """Write the data to the socket and disconnect from host.

        Args:
            data (dict): valid dict type that is used from the socket class to
            initialize the code execution.
        """
        self.socket.write(json.dumps(data))  # skipcq: PY-W0079
        self.socket.close()

    def connect_to_host(self):
        """Connect to host and start the timeout timer."""
        LOGGER.debug('QBaseClient :: Connecting to host: %s %s',
                     self.tcp_host, self.tcp_port)
        self.socket.socket_connect(self.tcp_host, self.tcp_port)
        self.timer.start()


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
        hostname = hostname or NetworkAddresses().local_host
        port = port or NetworkAddresses().port

        QBaseClient.__init__(self, hostname, port)

    def on_connected(self):
        """Override parent method.

        When connection is establish write data to socket.
        """
        LOGGER.debug('SendTestClient :: Handshake successful.')
        r = random.randint(1, 50)

        client = type(self.socket).__name__
        code = ('from __future__ import print_function\n'
                "print('Hello from Test %s Client', %s)") % (client, r)

        output_text = {
            'text': code,
            'file': 'path/to/tmp_file.py'
        }

        self.write_data(output_text)


class NodesNotSelectedError(BaseException):
    """No nodes selected."""


class SendNodesClient(QBaseClient):
    """Send nuke nodes between instances."""

    def __init__(self, hostname=None, port=None):
        """Init method for the SendNodesClient.

        If arguments are omitted, Client will connect to default configuration
        found inside the NetworkAddresses class.

        Args:
            hostname (str, optional): hostname to connect. Defaults to None.
            port (int, optional): port to connect. Defaults to None.
        """
        LOGGER.debug('SendNodesClient :: Sending nodes...')

        hostname = hostname or NetworkAddresses().send_to_address
        port = port or NetworkAddresses().port

        QBaseClient.__init__(self, hostname, port)

    def on_connected(self):
        """Override parent method.

        When connection is establish write the content of the transfer file to
        the socket.
        """
        LOGGER.debug('SendNodesClient :: Handshake successful.')
        try:
            self.write_data(self.transfer_file_content())
        except NodesNotSelectedError:
            pass

    def transfer_file_content(self):
        """Get the transfer file contents to use in the nuke node copy command.

        Returns:
            (dict): a dict to be sent to the socket.

        Raises:
            NodesNotSelectedError: when nodes are not selected inside nuke but
            user tries to send something.
        """
        settings = AppSettings()
        transfer_file = settings.value('path/transfer_file')

        try:
            # this will also create the file if it doesn't exists already
            nuke.nodeCopy(transfer_file)
        except RuntimeError:
            self.state_changed.emit('No nodes selected.')
            LOGGER.error('SendNodesClient :: NodesNotSelected error.')
            raise NodesNotSelectedError
        else:
            with open(transfer_file) as file:
                return {'text': file.read(), 'file': transfer_file}
