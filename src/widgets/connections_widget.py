# coding: utf-8
from __future__ import print_function

import logging

from PySide2.QtCore import QObject, Qt, Signal
from PySide2.QtNetwork import QHostInfo

from PySide2.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QSpinBox
)

from ..utils import SettingsState, get_ip

LOGGER = logging.getLogger('NukeServerSocket.connections_widget')


class ConnectButton(QPushButton):
    """Custom QPushButton class for quick Connect/Disconnect setup."""

    def __init__(self, parent=None):
        QPushButton.__init__(self, parent)
        self.setText('Connect')
        self.setCheckable(True)

        self.toggled.connect(self.toggle_state)

    def disconnect(self):
        """Force disconnect and uncheck toggle state of button."""
        self.setText('Connect')
        self.setChecked(False)

    def toggle_state(self, state):
        """Toggle state of button.

        When a button is toggled (True) the button text will be changed to Disconnect,
        otherwise when the button not toggled (False) will be changed to Connect.

        Args:
            state (bool): state of the button
        """
        if state:
            self.setText('Disconnect')
        else:
            self.setText('Connect')


class ConnectionButtons(QObject):
    """Button section of the connection widgets"""

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        self.connect_btn = ConnectButton(parent)
        self.connect_btn.toggled.connect(self._toggle_buttons_state)

        self.test_btn = QPushButton('Test Receiver')
        self.test_btn.setEnabled(False)

        self.send_btn = QPushButton('Send Selected Nodes')

    def _toggle_buttons_state(self, state):
        """Switch button state based on the connect button.

        If button is toggled (True) then enable test_btn but disabled send_btn
        and vice versa.

        Args:
            state (bool): state of the connect button
        """
        self._enable_send(state)
        self._enable_test(state)

    def _enable_send(self, state):
        """Enable or disable send_btn.

        The state will always be mutually exclusive with the connect_btn.

        Args:
            state (bool): state of the connect button
        """
        self.send_btn.setEnabled(not state)

    def _enable_test(self, state):
        """Enable or disable test_btn.

        Args:
            state (bool): state of the connect button
        """
        self.test_btn.setEnabled(state)


class TcpPort(QObject):
    """Tcp port object"""

    def __init__(self, port_id):  # type: (str) -> None
        QObject.__init__(self)

        self.port_id = port_id
        self.settings = SettingsState()

        self._server_port = QSpinBox()
        self._server_port.setRange(49512, 65535)
        self._server_port.setMaximumWidth(100)
        self._server_port.setToolTip('Server port for the socket to listen')
        self._setup_port()

    def _setup_port(self):
        """Setup the port entry field widget."""
        port = self.settings.value(self.port_id, 54321)

        self._server_port.setValue(int(port))
        self._server_port.valueChanged.connect(self._write_port)

    @property
    def widget(self):  # type: () -> QSpinBox
        """The entry widget port Qt object."""
        return self._server_port

    def _write_port(self, port):
        """Write port id to configuration file is port is valid."""
        if 49152 <= port <= 65535:
            self.settings.setValue(self.port_id, port)


class ConnectionsWidget(QWidget):

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)

        self.settings = SettingsState()

        self._is_connected = QLabel()
        self._is_connected.setObjectName('connection')
        self.set_idle()

        self.server_port = TcpPort(port_id='server/port')
        self.port_widget = self.server_port.widget

        self.buttons = ConnectionButtons(self)

        # when button is clicked, update server status label
        self.buttons.connect_btn.clicked.connect(self.update_status_label)

        self._layout = QVBoxLayout()
        self._add_form_layout()
        self._add_grid_layout()

        self.setLayout(self._layout)

    def _add_form_layout(self):
        """Setup the form layout for the labels."""
        _form_layout = QFormLayout()
        _form_layout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        _form_layout.addRow(QLabel('Status'), self._is_connected)
        _form_layout.addRow(QLabel('Local IP Address'), QLabel(get_ip()))
        _form_layout.addRow(
            QLabel('Local Host Address'), QLabel(QHostInfo().localHostName()))
        _form_layout.addRow(QLabel('Port'), self.port_widget)

        self._layout.addLayout(_form_layout)

    def _add_grid_layout(self):
        """Setup the grid layout for the buttons."""

        _grid_layout = QGridLayout()
        _grid_layout.addWidget(self.buttons.connect_btn, 0, 0, 1, 2)
        _grid_layout.addWidget(self.buttons.test_btn, 1, 0)
        _grid_layout.addWidget(self.buttons.send_btn, 1, 1)

        self._layout.addLayout(_grid_layout)

    def set_idle(self):
        """Set idle status."""
        self._is_connected.setText('Idle')
        self.setStyleSheet('QLabel#connection { color: orange;}')

    def set_disconnected(self):
        """Set disconnected status."""
        self._is_connected.setText('Not Connected')
        self.setStyleSheet('QLabel#connection { color: red;}')

    def set_connected(self):
        """Set connected status."""
        # XXX: when testing internally will not color
        self._is_connected.setText('Connected')
        self.setStyleSheet('QLabel#connection { color: green;}')

    def update_status_label(self, status):  # type (bool) -> None
        """Update status label and port widget modification.

        Args:
            status (bool): bool representation of the connection status
        """
        self.server_port.widget.setEnabled(not status)

        if status is True:
            self.set_connected()
        elif status is False:
            self.set_idle()
