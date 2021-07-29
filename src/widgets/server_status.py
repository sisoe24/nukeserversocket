# -*- coding: utf-8 -*-
from __future__ import print_function


import logging

from PySide2.QtCore import QRegExp, Qt
from PySide2.QtNetwork import QHostInfo
from PySide2.QtGui import QRegExpValidator

from PySide2.QtWidgets import (
    QFormLayout,
    QLabel,
    QWidget,
    QLineEdit
)

from VscodeServerSocket.src.utils import Settings, get_ip

LOGGER = logging.getLogger('VscodeServerSocket.server_status')


class ServerStatus(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.settings = Settings()

        self.is_connected = QLabel()
        self.is_connected.setObjectName('connection')
        self.update_status('Idle')

        self.server_port = QLineEdit()
        self.server_port.setMaximumWidth(100)
        self.server_port.setToolTip('Server port for vscode to listen')
        self.server_port.setObjectName('port')
        self._set_server_port()

        _layout = QFormLayout()
        _layout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        _layout.addRow(QLabel('Status'), self.is_connected)
        _layout.addRow(QLabel('Local Host Address'),
                       QLabel(QHostInfo().localHostName()))
        _layout.addRow(QLabel('Local IP Address'), QLabel(get_ip()))
        _layout.addRow(QLabel('Port'), self.server_port)

        self.setLayout(_layout)

    def port_state(self, value):
        self.server_port.setEnabled(value)

    def _set_server_port(self):

        port = self.settings.value('server/port', '54321')
        self.server_port.setText(port)
        self.server_port.setValidator(QRegExpValidator(QRegExp('\d{5}')))

        self.server_port.textChanged.connect(
            self._update_port
        )

    @ staticmethod
    def _check_port_range(port):
        port = 0 if not port else port
        return 49152 <= int(port) <= 65535

    def valid_port_range(self):
        return self._check_port_range(self.server_port.text())

    def _update_port(self, text):
        style = self.styleSheet()

        if self._check_port_range(text):
            style += '''QLineEdit#port {background-color: none;}'''
            self.settings.setValue('server/port', text)
        else:
            style += '''QLineEdit#port {background-color: rgba(255, 0, 0, 150);}'''

        self.setStyleSheet(style)

    def update_status(self, status):
        style = self.styleSheet()

        if status is True:
            self.is_connected.setText('Connected')
            style += '''QLabel#connection { color: green;}'''
        elif status == 'Idle':
            self.is_connected.setText('Idle')
            style += '''QLabel#connection { color: orange;}'''
        elif status is False:
            self.is_connected.setText('Not Connected')
            style += '''QLabel#connection { color: red;}'''
        else:
            LOGGER.debug('Unkown status: %s', status)

        self.setStyleSheet(style)
