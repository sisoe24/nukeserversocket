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
from .script_editor import NukeScriptEditor
from .connection import Server, TestClient, SendNodesClient
from .widgets import (
    LogWidgets,
    ConnectionsWidget,
    ErrorDialog,
    ToolBar
)

LOGGER = logging.getLogger('NukeServerSocket.main')
LOGGER.debug('\nSTART APPLICATION')


def init_settings():
    """Setup settings file."""
    # TODO: need to think this better

    tmp_folder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '.tmp'
    )

    if not os.path.exists(tmp_folder):
        os.mkdir(tmp_folder)

    settings = AppSettings()
    settings.validate_port_settings()
    settings.setValue('path/transfer_file',
                      os.path.join(tmp_folder, 'transfer_nodes.tmp'))


class MainWindowWidget(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self)

        init_settings()

        self.connections = ConnectionsWidget(parent=self)

        self.connect_btn = self.connections.buttons.connect_btn
        self.connect_btn.toggled.connect(self._connection)

        self.send_btn = self.connections.buttons.send_btn
        self.send_btn.clicked.connect(self._send_nodes)

        self.test_btn = self.connections.buttons.test_btn
        self.test_btn.clicked.connect(self._test_receiver)

        self.log_widgets = LogWidgets()

        _layout = QVBoxLayout()
        _layout.addWidget(self.connections)
        _layout.addWidget(self.log_widgets)

        self.setLayout(_layout)

        self._server = None
        self._test_client = None
        self._node_client = None

        NukeScriptEditor.init_editor()

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

    def _connection(self, state):  # type: (bool) -> None
        """When connect button is toggled start connection, otherwise close it."""

        def _start_connection():
            """Setup connection to server."""
            self._server = self.setup_server()

            try:
                status = self._server.start_server()
            except ValueError as err:
                LOGGER.error('server did not connect: %s', err)
                self.connect_btn.disconnect()
                self.connections.set_disconnected()
            else:
                LOGGER.debug('server is connected: %s', status)
                self._enable_connection_mod(False)

        if state:
            _start_connection()
        else:
            self._server.close_server()
            self._enable_connection_mod(True)

    def _send_nodes(self):
        """Send the selected Nuke Nodes using the internal client."""
        self._node_client = SendNodesClient()
        self._node_client.state_changed.connect(
            self.log_widgets.set_status_text)
        self._node_client.connect_to_host()

    def _test_receiver(self):
        """Send a test message using the internal client."""
        self._test_client = TestClient()
        self._test_client.state_changed.connect(
            self.log_widgets.set_status_text)
        self._test_client.connect_to_host()


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.setWindowTitle("NukeServerSocket")

        toolbar = ToolBar()
        self.addToolBar(toolbar)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        try:
            main_widgets = MainWindowWidget(self)
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
