"""Socket modules that deals with the incoming data."""
# coding: utf-8
from __future__ import print_function

import logging

from PySide2.QtCore import QObject, Signal, QByteArray

from .data_to_code import DataCode, InvalidData
from ..utils import validate_output, connection_timer, pyEncoder
from ..script_editor import CodeEditor

LOGGER = logging.getLogger('NukeServerSocket.socket')


class Socket(QObject):
    """QObject Socket class that deals with the incoming data.

    Class will also verify its type before calling a CodeEditor to execute it.
    Custom signals will emit when connection status has changed.

    Signal:
        (str) state_changed: emits when the connection state has changed.
        (str) received_text: emits the received text when ready.
        (str) output_text: emits the output text after code executing happened.
    """

    state_changed = Signal(str)
    received_text = Signal(str)
    output_text = Signal(str)

    def __init__(self, socket):
        """Init method for the socket class."""
        QObject.__init__(self)
        LOGGER.debug('Socket :: Listening...')

        self.socket = socket
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.readyRead.connect(self.on_readyRead)

        self.timer = connection_timer(30)
        self.timer.timeout.connect(self.close_socket)
        self.timer.start()

    def on_connected(self):
        """Connect event."""
        LOGGER.debug('Socket :: Connected.')

    def on_disconnected(self):
        """Disconnect event."""
        LOGGER.debug('Socket :: Disconnected.')

    def close_socket(self):
        """Close the socket and stop the timeout timer."""
        self.socket.close()
        self.timer.stop()

    def _invalid_data(self, err):
        """Close socket when data is invalid.

        If data is invalid the socket connection will be blocked and the signal
        `state_changed` will emit a message: 'Error. Invalid data:...'

        Args:
            err (DataCode): err obj to be shown in log status.
        """
        msg = 'Error. Invalid data: %s' % err

        LOGGER.warning('Socket :: %s', msg)
        self.state_changed.emit(msg)

        self.close_socket()

    def on_readyRead(self):
        """Execute the received data.

        When data received is ready, method will pass the job to the CodeEditor
        class that will execute the received code.
        """
        self.state_changed.emit("Message received.")
        LOGGER.debug('Socket :: Message ready')
        self.timer.start()

        try:
            data = self.socket.readAll().data().decode('utf-8')
            msg_data = DataCode(data)
        except InvalidData as err:
            self._invalid_data(err)
            return

        editor = CodeEditor(msg_data)
        output_text = editor.execute()

        LOGGER.debug('Socket :: sending message back.')
        self.socket.write(validate_output(output_text))

        self.close_socket()

        self.received_text.emit(msg_data.text)
        self.output_text.emit(output_text)
