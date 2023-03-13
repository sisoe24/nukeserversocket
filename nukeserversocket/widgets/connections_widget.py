"""Module that deals with the ui connection logic."""
# coding: utf-8

from PySide2.QtCore import Qt, QObject
from PySide2.QtWidgets import (QLabel, QWidget, QSpinBox, QLineEdit,
                               QFormLayout, QGridLayout, QHBoxLayout,
                               QPushButton, QToolButton, QVBoxLayout,
                               QRadioButton)

from ..util import get_ip
from ..settings import AppSettings

# TODO: refactor


class ConnectionButtons(QObject):
    """Button section of the connection widgets."""

    def __init__(self, parent=None):
        """Init method for the ConnectionButtons class.

        Args:
            (QWidget | None): QWidget to set as a parent. Defaults to: None.
        """
        QObject.__init__(self, parent)

        self.connect_btn = QPushButton('Connect')
        self.connect_btn.setCheckable(True)
        self.connect_btn.toggled.connect(self.toggle_state)
        self.connect_btn.toggled.connect(self._toggle_buttons_state)

        self.test_btn = QPushButton('Test Receiver')
        self.test_btn.setEnabled(False)
        self.test_btn.clicked.connect(lambda: self.test_btn.setEnabled(False))

        self.send_btn = QPushButton('Send Selected Nodes')
        self.send_btn.setEnabled(False)
        self.send_btn.clicked.connect(lambda: self.send_btn.setEnabled(False))

    def _disconnect(self):
        """Disconnect and uncheck toggle state of button."""
        self.connect_btn.setText('Connect')
        self.connect_btn.setChecked(False)

    def toggle_state(self, state):
        """Toggle state of button.

        When button is toggled (True), text will be changed to Disconnect,
        otherwise when toggled (False) will be changed to Connect.

        Args:
            state (bool): state of the button
        """
        if state:
            self.connect_btn.setText('Disconnect')
        else:
            self.connect_btn.setText('Connect')

    def _toggle_buttons_state(self, state):
        """Switch button state based on the connect button.

        If button is toggled (True) then enable test_btn but disabled send_btn
        and vice versa.

        Args:
            state (bool): state of the connect button
        """
        self._enable_test(state)

    def _enable_test(self, state):
        """Enable or disable test_btn.

        Args:
            state (bool): state of the connect button
        """
        self.test_btn.setEnabled(state)


class TcpPort(QSpinBox):
    """Custom QSpinBox class for the tcp port."""

    def __init__(self, port_id='port'):  # type: (str) -> None
        """Init method for the TcpPort class.

        Args:
            (str): config file id key to be used for the port.
        """
        QSpinBox.__init__(self)

        self.port_id = 'server/%s' % port_id
        self.settings = AppSettings()

        self.setRange(49512, 65535)
        self.setMaximumHeight(100)
        self.setToolTip('Server port for the socket to listen/send.')
        self._setup_port()

    def _setup_port(self):
        """Set up the port entry field widget.

        Method grab the value from the config file if any and assign it to the
        port value. After that will connect the signal `valueChanged` to update
        the config key.
        """
        port = self.settings.value(self.port_id, 54321)

        self.setValue(int(port))
        self.valueChanged.connect(self._write_port)

    def _write_port(self, port):  # type: (int) -> None
        """Write port id to configuration file is port is valid.

        The method will convert the port value into text before writing it.
        This is because when settings are first initialized will read the value
        as a string, so is better to assume that port is always a string.
        """
        if 49152 <= port <= 65535:
            self.settings.setValue(self.port_id, self.textFromValue(port))


class TimeoutLabels(QWidget):
    """Timeout QWidget for the timeout labels."""

    def __init__(self):
        """Initialize the form layout labels."""
        QWidget.__init__(self)
        self.setHidden(True)

        self._server_timeout = QLabel('')
        self._client_timeout = QLabel('')
        self._socket_timeout = QLabel('')

        _layout = QFormLayout()
        _layout.addRow(QLabel('Server Timeout in:'), self._server_timeout)
        _layout.addRow(QLabel('Receiver Timeout in:'), self._client_timeout)
        _layout.addRow(QLabel('Send Nodes Timeout in:'), self._socket_timeout)

        self.setLayout(_layout)


class ConnectionsWidget(QWidget):
    """Class that deals with the ui connection logic."""

    def __init__(self, parent=None):
        """Init method for the ConnectionsWidget class.

        Args:
            (QWidget | None): QWidget to set as a parent. Defaults to: None.
        """
        # ! TODO: Refactor needed.
        QWidget.__init__(self, parent)

        self.settings = AppSettings()

        self._is_connected = QLabel()
        self._is_connected.setObjectName('connection')

        self.server_port = TcpPort()

        self.buttons = ConnectionButtons(self)

        # when button is clicked, update server status label
        self.buttons.connect_btn.toggled.connect(self.update_status_label)

        self.ip_entry = QLineEdit()
        self.ip_entry.textChanged.connect(self._update_send_address)
        self.ip_entry.setMaximumWidth(100)

        self.ip_address_label = QLabel()

        self.receiver_mode = QRadioButton('Receiver')
        self.receiver_mode.toggled.connect(self._state_changed)
        self.receiver_mode.setChecked(True)
        self.receiver_mode.setLayoutDirection(Qt.RightToLeft)

        self.sender_mode = QRadioButton('Sender')
        self.sender_mode.toggled.connect(self.set_label_sender)

        self._timeout = TimeoutLabels()
        self._setup_timeout_btn()

        self._layout = QVBoxLayout()
        self._add_switch_layout()
        self._add_form_layout()
        self._add_grid_layout()
        self._layout.addWidget(self._timeout)

        self.setLayout(self._layout)
        self._set_tooltips()

    def _set_tooltips(self):
        """Set up the various tooltips to clean the init method."""
        self._is_connected.setToolTip(
            'State of the server when listening for incoming requests.'
        )
        self.ip_entry.setToolTip(
            'Local IP address for current host.\n'
            'When on Receiver mode this only serves as a lookup.\n'
            'When on Sender mode, field can be changed to match a different computer address.')
        self.receiver_mode.setToolTip(
            'Receiver Mode.\n'
            'This puts the plugin into listening for incoming request mode.'
        )
        self.sender_mode.setToolTip(
            'Sender Mode.\nThis puts the plugin into the sending nodes mode.'
        )

    def _update_send_address(self, text):
        """Update settings for send port address if mode is on sender."""
        if not self.receiver_mode.isChecked():
            self.settings.setValue('server/send_to_address', text)

    def _state_changed(self, state):
        """When mode changes, update the UI accordingly."""
        self.set_label_idle()

        def _update_ip_text(state):
            """Update the ip widgets based on the mode."""
            ip_text = get_ip()

            if state:
                ip_label_text = 'Local IP Address'
                ip_entry_text = ip_text
            else:
                ip_label_text = 'Send To IP Address'
                ip_entry_text = self.settings.value(
                    'server/send_to_address', ip_text
                )

            self.ip_entry.setText(ip_entry_text)
            self.ip_address_label.setText(ip_label_text)

        self.buttons.connect_btn.setEnabled(state)
        self.buttons.send_btn.setEnabled(not state)
        self.ip_entry.setReadOnly(state)

        _update_ip_text(state)

    def _add_switch_layout(self):
        """Set up the radiobuttons layout."""
        switch_layout = QHBoxLayout()
        switch_layout.addWidget(self.receiver_mode)
        switch_layout.addWidget(self.sender_mode)

        self._layout.addLayout(switch_layout)

    def _add_form_layout(self):
        """Set up the form layout for the labels."""
        _form_layout = QFormLayout()
        _form_layout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)
        _form_layout.addRow(QLabel('Status'), self._is_connected)
        _form_layout.addRow(self.ip_address_label, self.ip_entry)
        _form_layout.addRow(QLabel('Port'), self.server_port)

        self._layout.addLayout(_form_layout)

    def _setup_timeout_btn(self):
        """Set up the show timeout button.

        Set a QToolButton that will hide/unhide the timeouts label widgets.
        """
        def _hide_timeouts(state):
            """Update the state of the widget and arrow type."""
            state = not state
            self._timeout.setHidden(state)
            self._timeout_btn.setArrowType(
                Qt.DownArrow if state else Qt.UpArrow)

        self._timeout_btn = QToolButton()
        self._timeout_btn.setToolTip('Show timeout timers')
        self._timeout_btn.setArrowType(Qt.DownArrow)
        self._timeout_btn.setCheckable(True)
        self._timeout_btn.setChecked(False)
        self._timeout_btn.toggled.connect(_hide_timeouts)

    def _add_grid_layout(self):
        """Set up the grid layout for the buttons."""
        _grid_layout = QGridLayout()
        _grid_layout.addWidget(self.buttons.connect_btn, 0, 0, 1, 3)
        _grid_layout.addWidget(self._timeout_btn, 1, 0)
        _grid_layout.addWidget(self.buttons.test_btn, 1, 1)
        _grid_layout.addWidget(self.buttons.send_btn, 1, 2)
        self._layout.addLayout(_grid_layout)

    def set_label_sender(self):
        """Set idle status."""
        self._is_connected.setText('Ready to send')
        self.setStyleSheet('QLabel#connection { color: CornflowerBlue;}')

    def set_label_idle(self):
        """Set idle status."""
        self._is_connected.setText('Idle')
        self.setStyleSheet('QLabel#connection { color: orange;}')

    def set_label_disconnected(self):
        """Set disconnected status."""
        self._is_connected.setText('Not Connected')
        self.setStyleSheet('QLabel#connection { color: red;}')

    def set_label_connected(self):
        """Set connected status."""
        self._is_connected.setText('Connected')
        self.setStyleSheet('QLabel#connection { color: green;}')

    def _disconnect(self):
        """Set label disconnect at toggle the connection button."""
        self.set_label_disconnected()
        self.buttons._disconnect()

    def update_status_label(self, status):  # type (bool) -> None
        """Update status label.

        Args:
            status (bool): bool representation of the connection status
        """
        if status is True:
            self.set_label_connected()
        elif status is False:
            self.set_label_idle()
