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

from ..utils import SettingsState, get_ip

LOGGER = logging.getLogger('NukeServerSocket.server_status')


def _set_style_sheet(func):
    """Wrapper that adds styleSheet strings to main styleSheet"""
    def inner_wrapper(*args, **kwargs):
        self = args[0]

        style = self.styleSheet()
        style += func(*args, **kwargs)
        self.setStyleSheet(style)

    return inner_wrapper


class ServerStatus(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.settings = SettingsState()
        self.port_config_id = 'server/port'

        self.is_connected = QLabel()
        self.is_connected.setObjectName('connection')
        self.set_idle()

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

    def port_state(self, value):  # type: (bool) -> None
        """Public method to enable/disable port textual entry."""
        self.server_port.setEnabled(value)

    def valid_port_range(self):  # type: (str) -> bool
        """Public method to che if current port is in valid range.

        Returns:
            (bool): True if is in valid range, False otherwise
        """
        return self._check_port_range(self.server_port.text())

    def _set_server_port(self):
        """Setup the port entry field widget.

        Creates a default port with value 54321 if not already present in the config.
        Otherwise will grab that value.
        """
        port = self.settings.value(self.port_config_id)
        if not port:
            port = '54321'
            self.settings.setValue(self.port_config_id, port)

        self.server_port.setText(port)
        self.server_port.setValidator(QRegExpValidator(QRegExp('\d{5}')))

        self.server_port.textChanged.connect(self._update_port)

    @staticmethod
    def _check_port_range(port):  # type: (str) -> bool
        """Check if port range is valid.

        Args:
            (str) port: port to check.

        Returns:
            (bool): True if is in valid range, False otherwise
        """
        port = 0 if not port else port
        return 49152 <= int(port) <= 65535

    @_set_style_sheet
    def _update_port(self, port):  # type: (str) -> str
        """Update file configuration value.

        If port is out of range widget will be colored with red.

        Returns:
            (str): Qt styleSheet to be added to main styleSheet.
        """
        if self._check_port_range(port):
            style = 'QLineEdit#port {background-color: none;}'
            self.settings.setValue(self.port_config_id, port)
        else:
            style = 'QLineEdit#port {background-color: rgba(255, 0, 0, 150);}'
        return style

    @_set_style_sheet
    def set_idle(self):  # type () -> str
        """Set idle status.

        Returns:
            (str): Qt styleSheet to be added to main styleSheet.
        """
        self.is_connected.setText('Idle')
        return 'QLabel#connection { color: orange;}'

    @_set_style_sheet
    def set_disconnected(self):  # type () -> str
        """Set disconnected status.

        Returns:
            (str): Qt styleSheet to be added to main styleSheet.
        """
        self.is_connected.setText('Not Connected')
        return 'QLabel#connection { color: red;}'

    @_set_style_sheet
    def set_connected(self):  # type () -> str
        """Set connected status.

        Returns:
            (str): Qt styleSheet to be added to main styleSheet.
        """
        self.is_connected.setText('Connected')
        return 'QLabel#connection { color: green;}'

    def update_status(self, status):  # type (bool) -> None
        """Update status switch.

        Args:
            (bool) status: bool representation of the connection status
        """
        if status is True:
            self.set_connected()
        elif status is False:
            self.set_disconnected()
