# coding: utf-8
from __future__ import print_function

import os
import logging

from PySide2.QtWidgets import (
    QMainWindow,
    QStatusBar,
    QVBoxLayout,
    QWidget
)

from .utils import AppSettings
from .connection import Server, SendTestClient, SendNodesClient
from .widgets import (
    LogWidgets,
    ConnectionsWidget,
    ErrorDialog,
    ToolBar
)

LOGGER = logging.getLogger('NukeServerSocket.main')
LOGGER.debug(' -*- START APPLICATION -*-')


def init_settings():
    """Setup settings file."""
    # TODO: need to think this better

    tmp_folder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '.tmp'
    )

    if not os.path.exists(tmp_folder):
        os.mkdir(tmp_folder)

    settings = AppSettings()
    LOGGER.debug('Main :: settings file : %s', settings.fileName())
    settings.validate_port_settings()
    settings.setValue('path/transfer_file',
                      os.path.join(tmp_folder, 'transfer_nodes.tmp'))


class MainWindowWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self)
        LOGGER.debug('Main :: init')

        init_settings()

        self.connections = ConnectionsWidget(parent=self)

        self.connect_btn = self.connections.buttons.connect_btn
        self.connect_btn.toggled.connect(self.toggle_connection)

        self.send_btn = self.connections.buttons.send_btn
        self.send_btn.clicked.connect(self._send_nodes)

        self.test_btn = self.connections.buttons.test_btn
        self.test_btn.clicked.connect(self._send_test)

        self.log_widgets = LogWidgets()

        _layout = QVBoxLayout()
        _layout.addWidget(self.connections)
        _layout.addWidget(self.log_widgets)

        self.setLayout(_layout)

        self._server = None
        self._test_client = None
        self._node_client = None


    def _enable_connection_mod(self, state):  # type: (bool) -> None
        """Enable/disable connection widgets modification.

        When connected the port and the sender mode will be disabled.

        Args:
            state (bool): state of the widget.
        """
        self.connections.server_port.setEnabled(state)
        self.connections.sender_mode.setEnabled(state)

    def _disconnect(self):
        """If server connection gets timeout then close it and reset UI."""
        self.connect_btn.setChecked(False)

    def setup_server(self):
        """Setup server class and log signals.

        Returns:
            Server: the server object.
        """
        def _setup_socket_log(socket):
            """Setup socket log signals."""
            socket.state_changed.connect(self.log_widgets.set_status_text)
            socket.received_text.connect(self.log_widgets.set_received_text)
            socket.output_text.connect(self.log_widgets.set_output_text)

        _server = Server()

        _server.timeout.connect(self._disconnect)
        _server.state_changed.connect(self.log_widgets.set_status_text)
        _server.socket_ready.connect(_setup_socket_log)

        return _server

    def toggle_connection(self, state):  # type: (bool) -> None
        """When connect button is toggled start connection, otherwise close it."""

        def _start_connection():
            """Setup connection to server."""
            self._server = self.setup_server()

            try:
                status = self._server.start_server()
            except RuntimeError as err:
                LOGGER.error('server did not connect: %s', err)
                self.connect_btn.disconnect()
                self.connections.set_disconnected()
                return False
            else:
                LOGGER.debug('server is connected: %s', status)
                self._enable_connection_mod(False)

            return bool(status)

        if state:
            return _start_connection()
        try:
            self._server.close_server()
        except AttributeError:
            # connection has never started but function could receive a False argument
            # causing a AttributeError because _server hasn't been declared yet
            pass

        self._enable_connection_mod(True)

    def _send_nodes(self):
        """Send the selected Nuke Nodes using the internal client."""
        self._node_client = SendNodesClient()
        self._node_client.state_changed.connect(
            self.log_widgets.set_status_text)
        self._node_client.connect_to_host()

    def _send_test(self):
        """Send a test message using the internal client."""
        self._test_client = SendTestClient()
        self._test_client.state_changed.connect(
            self.log_widgets.set_status_text)
        self._test_client.connect_to_host()


class MainWindow(QMainWindow):
    def __init__(self, main_widget=MainWindowWidget):
        QMainWindow.__init__(self)
        self.setWindowTitle("NukeServerSocket")

        toolbar = ToolBar()
        self.addToolBar(toolbar)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        try:
            main_widgets = main_widget(self)
        except Exception as err:
            ErrorDialog(err, self).show()
            LOGGER.critical(err, exc_info=True)
        else:
            self.setCentralWidget(main_widgets)


try:
    import nukescripts
except ImportError as error:
    pass
else:
    nukescripts.panels.registerWidgetAsPanel(
        'NukeServerSocket.src.main.MainWindow', 'NukeServerSocket',
        'NukeServerSocket.MainWindow')
