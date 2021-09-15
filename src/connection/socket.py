# coding: utf-8
from __future__ import print_function

import json
import logging

from PySide2.QtCore import QObject

from ..utils import CodeEditor, validate_output

LOGGER = logging.getLogger('NukeServerSocket.socket')


class Socket(QObject):
    def __init__(self, socket, status_widget):
        QObject.__init__(self)
        self.status_widget = status_widget

        self.socket = socket
        self.socket.connected.connect(self.on_connected)
        self.socket.disconnected.connect(self.on_disconnected)
        self.socket.readyRead.connect(self.on_readyRead)

    def on_connected(self):
        LOGGER.debug('Client connect event')
        self.status_widget.set_status_text("Client Connected Event")

    def on_disconnected(self):
        LOGGER.debug('-*- Client disconnect event -*-')
        self.status_widget.set_status_text("Client socket closed.")

    def _get_message(self):
        """Get the socket message.

        If the message is a simple string then return it into a dictionary,
        else return deserialized array.

        Will raise a ValueError exception if can not convert the stringified array.

        Returns:
            dict - dictionary data with the following keys:
                'text': code to execute
                'file': optional file name
        """
        msg = self.socket.readAll()

        # startsWith is a method of QByteArray
        if not msg.startsWith('{'):
            LOGGER.debug('Message is simple string. Converting into dict')
            return {'text': msg.data()}

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

        editor = CodeEditor(msg_data.get('file', None))
        editor.controller.set_input(msg_text)
        editor.controller.execute()

        output_text = editor.controller.output()

        LOGGER.debug('Sending message back')
        self.socket.write(validate_output(output_text))

        self.socket.close()
        LOGGER.debug('Closing socket')

        self.status_widget.set_input_text(msg_text)
        self.status_widget.set_output_text(output_text)
