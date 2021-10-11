# coding: utf-8
from __future__ import print_function

import json
import logging

from PySide2.QtCore import QObject, Signal

from ..utils import validate_output
from ..script_editor import CodeEditor

LOGGER = logging.getLogger('NukeServerSocket.socket')


class Socket(QObject):
    state_changed = Signal(str)
    received_text = Signal(str)
    output_text = Signal(str)

    def __init__(self, socket):
        QObject.__init__(self)

        self.socket = socket
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.readyRead.connect(self.on_readyRead)

    def on_connected(self):
        LOGGER.debug('Client connect event')
        self.state_changed.emit("Client Connected Event")

    def on_disconnected(self):
        LOGGER.debug('-*- Client disconnect event -*-')
        self.state_changed.emit("Message received.")

    def _get_message(self):
        """Get the socket message.

        If the message is a simple string then add it to a dictionary,
        else return deserialized array.

        Returns:
            dict - dictionary data with the following keys:
                'text': code to execute
                'file': optional file name

        Raises:
            ValueError: if fails to deserialize json data.
        """
        msg = self.socket.readAll()

        # startsWith is a method of QByteArray
        if not msg.startsWith('{'):
            LOGGER.debug('Message is simple string. Converting into dict')
            return {'text': msg.data().decode('utf-8')}

        try:
            LOGGER.debug('Message is stringified array.')
            msg_data = json.loads(msg.data())
        except Exception as err:
            LOGGER.critical("Invalid Json Deserialization: %s",
                            err, exc_info=True)
            raise ValueError('Json Deserialization error')
        else:
            LOGGER.debug('msg_data: %s', msg_data)
            return msg_data

    def on_readyRead(self):
        LOGGER.debug('Socket message ready')

        try:
            msg_data = self._get_message()
        except ValueError:
            return

        msg_text = msg_data.get('text')
        if not msg_text:
            LOGGER.warning("no text data to execute")
            return

        editor = CodeEditor(msg_data.get('file', ''))
        editor.controller.set_input(msg_text)
        editor.controller.execute()

        output_text = editor.controller.output()

        editor.controller.restore_state()

        LOGGER.debug('Sending message back')
        self.socket.write(validate_output(output_text))

        self.socket.close()
        LOGGER.debug('Closing socket')

        self.received_text.emit(msg_text)
        self.output_text.emit(output_text)
