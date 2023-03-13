"""Socket modules that deals with the incoming data."""
# coding: utf-8
from __future__ import print_function

import abc
import logging

from PySide2.QtCore import QUrl, Signal, QObject
from PySide2.QtNetwork import QTcpSocket

from ..util import validate_output
from ..widgets import Timer
from ..settings import AppSettings
from ..controllers import CodeEditor
from .data_to_code import DataCode, InvalidData

LOGGER = logging.getLogger('nukeserversocket')


class _AbstractSocketInterface(object):
    """Abstract socket interface class.

    This mimics the functionality of a QWebSocket or a QTcpSocket.
    """

    __metaclass__ = abc.ABCMeta

    def __init__(self, socket):  # type: (QWebSocket | QTcpSocket) -> None
        socket.connected.connect(self.on_connected)
        socket.disconnected.connect(self.on_disconnected)
        socket.error.connect(self.on_error)

    @abc.abstractmethod
    def write(self, text):
        """Write socket data."""
        raise NotImplementedError

    @abc.abstractmethod
    def socket_connect(self, host, port):
        raise NotImplementedError

    @abc.abstractmethod
    def close(self):
        """Close socket connection."""
        raise NotImplementedError

    @staticmethod
    def on_connected():
        """Connect event."""
        LOGGER.debug('QSocket :: Connected.')

    @staticmethod
    def on_disconnected():
        """Disconnect event."""
        LOGGER.debug('QSocket :: Disconnected.')

    @staticmethod
    def on_error(error):
        """Disconnect event."""
        LOGGER.debug('QSocket :: Error: %s', error)


class _TcpSocket(_AbstractSocketInterface, QObject):
    """Abstract QTcpSocket class.

    Signal:
        (str): messageReceived: emits when socket receives the data.
    """

    messageReceived = Signal(str)

    def __init__(self, socket):  # type:(QTcpSocket) -> None
        """Init method for the _TcpSocket class."""
        QObject.__init__(self)
        _AbstractSocketInterface.__init__(self, socket)
        self._socket = socket
        self._socket.readyRead.connect(self._set_tcp_message)

    def _set_tcp_message(self):
        """Emit a message to the tcp socket client."""
        self.messageReceived.emit(self._socket.readAll().data().decode('utf-8'))

    def write(self, text):
        """Write socket data."""
        self._socket.write(validate_output(text))

    def socket_connect(self, host, port):
        """Initialize socket connection."""
        self._socket.connectToHost(host, port)

    def close(self):
        """Close connection."""
        self._socket.flush()
        self._socket.disconnectFromHost()

    def abort(self):
        """Abort connection."""
        self._socket.abort()


class _WebSocket(_AbstractSocketInterface, QObject):
    """Abstract QWebSocket class.

    Signal:
        (str): messageReceived: emits when socket receives the data.
    """

    messageReceived = Signal(str)

    def __init__(self, socket):  # type:(QWebSocket) -> None
        """Init method for the _WebSocket class."""
        QObject.__init__(self)
        _AbstractSocketInterface.__init__(self, socket)
        self._socket = socket
        self._socket.textMessageReceived.connect(self.messageReceived.emit)

    def write(self, text):
        """Write socket data."""
        self._socket.sendTextMessage(text)

    def socket_connect(self, host, port):
        """Initialize connection."""
        self._socket.open(QUrl('ws://%s:%s' % (host, port)))

    def close(self):
        """Close connection."""
        self._socket.flush()
        self._socket.close()

    def abort(self):
        """Abort connection."""
        self._socket.abort()


def socket_factory(socket):
    """Create an abstract socket object.

    Args:
        socket (QTcpSocket | QWebSocket)

    Returns:
        _QTcpSocket | _WebSocket
    """
    return _TcpSocket(socket) if isinstance(socket, QTcpSocket) else _WebSocket(socket)


class QSocket(QObject):
    """QObject Socket class that deals with the incoming data.

    Custom signals will emit when connection status has changed.

    Signal:
        (str) execution_error: emits when there is an execution error.
        (str) state_changed: emits when the connection state has changed.
        (str) received_text: emits the received text when ready.
        (str) output_text: emits the output text after code executing happened.
        (str) socket_timeout: emits every second to indicate the timeout status
    """

    execution_error = Signal(str)
    state_changed = Signal(str)
    received_text = Signal(str)
    output_text = Signal(str)
    socket_timeout = Signal(str)

    def __init__(self, socket):
        """Init method for the socket class."""
        QObject.__init__(self)
        LOGGER.debug('QSocket :: Listening...')

        self.socket = socket_factory(socket)
        self.socket.messageReceived.connect(self.on_readyRead)

        self.timer = Timer(int(AppSettings().value('timeout/socket', 30)))
        self.timer._timer.timeout.connect(self.close_socket)
        self.timer.time.connect(self.socket_timeout.emit)
        self.timer.start()

    def close_socket(self):
        """Close the socket and stop the timeout timer."""
        self.socket.close()
        self.timer.stop()

    def on_readyRead(self, message):
        """Execute the received data.

        When data received is ready, pass the job to the CodeEditor class that
        executes the received data.
        """
        LOGGER.debug('QSocket :: Message received')
        self.state_changed.emit('Message received.')
        self.timer.start()

        try:
            msg_data = DataCode(message)
        except InvalidData as err:
            self._invalid_data(err)
            return

        editor = CodeEditor(msg_data)
        editor.controller.execution_error.connect(self.execution_error.emit)
        editor.controller.execution_error.connect(self.state_changed.emit)
        output_text = editor.execute()

        LOGGER.debug('QSocket :: sending message back.')
        self.socket.write(output_text)

        self.close_socket()

        self.received_text.emit(msg_data.text)
        self.output_text.emit(output_text)

    def _invalid_data(self, err):
        """Close socket when data is invalid.

        If data is invalid, the socket connection will be stop and the signal
        `state_changed` will emit a message: 'Error. Invalid data:...'

        Args:
            err (Any): exception message.
        """
        msg = 'Error. Invalid data: %s' % err

        LOGGER.warning('QSocket :: %s', msg)
        self.state_changed.emit(msg)

        self.close_socket()
