# coding: utf-8
from __future__ import print_function

import json
import logging

from PySide2.QtCore import QObject

from VscodeServerSocket.src.utils import ScriptEditor, validate_output

LOGGER = logging.getLogger('VscodeServerSocket.socket')


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
        LOGGER.debug('Client disconnect event')
        self.status_widget.set_status_text("Client socket closed.")

    def on_readyRead(self):
        LOGGER.debug('Socket message ready')

        msg = self.socket.readAll()

        msg_data = json.loads(msg.data())

        msg_to_string = msg_data['text']
        LOGGER.debug('msg data type: %s', type(msg))

        script_editor = ScriptEditor(file=msg_data['file'])
        script_editor.set_text(msg_to_string)
        script_editor.execute()

        output_text = script_editor.set_status_output()

        script_editor.restore_state()

        LOGGER.debug('Sending message back')
        self.socket.write(validate_output(output_text))

        self.socket.close()
        LOGGER.debug('Closing socket')

        self.status_widget.set_input_text(msg_to_string)
        self.status_widget.set_output_text(output_text)
