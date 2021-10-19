"""Socket modules that deals with the incoming data."""
# coding: utf-8
from __future__ import print_function

import json
import logging

from PySide2.QtCore import QObject, Signal

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

    def _get_message(self):
        """Get the socket message.

        If the message is a simple string then add it to a dictionary,
        else return deserialized array.

        Returns:
            dict - dictionary data with the following keys:
                'text': code to execute
                'file': optional file name

        Raises:
            RuntimeError: if fails to deserialize json data.
        """
        msg = self.socket.readAll()
        self.state_changed.emit("Message received.")

        # startsWith is a method of QByteArray
        if not msg.startsWith('{'):
            LOGGER.debug('Socket :: Message is simple string.')
            return {'text': msg.data().decode('utf-8')}

        try:
            LOGGER.debug('Socket :: Message is stringified array.')
            msg_data = json.loads(msg.data())

        # could raise json.decoder.JSONDecodeError when decoding problems
        # but if other errors happens will break the script, and I would like
        # to just "ignore" and not execute any code
        except Exception as err:
            msg = "Error json deserialization. %s: %s" % (err, msg.data())

            LOGGER.critical(msg)
            self.state_changed.emit(msg)

            raise RuntimeError('Json Deserialization error')

        else:
            LOGGER.debug('Socket :: Message received: %s', msg_data)
            return msg_data

    @staticmethod
    def _is_valid_data(msg_text):
        """Check if data received is a valid string."""
        msg_text = pyEncoder(msg_text)
        return bool(msg_text and isinstance(msg_text, str) and not msg_text.isspace())

    def on_readyRead(self):
        """Execute the received data.

        When data received is ready, method will pass the job to the CodeEditor
        class that will execute the received code.
        """
        LOGGER.debug('Socket :: Message ready')
        self.timer.start()

        try:
            msg_data = self._get_message()
        except RuntimeError:
            self.close_socket()
            return

        msg_text = msg_data.get('text')  # type: str

        if not self._is_valid_data(msg_text):
            msg = 'Error. Invalid data: %s' % msg_data

            LOGGER.warning('Socket :: %s', msg)
            self.state_changed.emit(msg)

            self.close_socket()
            return

        # TODO: refactor the message logic into the code editor class
        editor = CodeEditor(msg_data.get('file', ''))
        editor.controller.set_input(msg_text)
        editor.controller.execute()

        output_text = editor.controller.output()

        editor.controller.restore_state()

        LOGGER.debug('Socket :: sending message back.')
        self.socket.write(validate_output(output_text))

        self.close_socket()

        self.received_text.emit(msg_text)
        self.output_text.emit(output_text)
