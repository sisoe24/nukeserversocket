"""Main application logic. This is where main window and widget are created."""
# coding: utf-8

import os
import logging

from PySide2.QtWidgets import (QWidget, QStatusBar, QMainWindow, QPushButton,
                               QVBoxLayout)

from .network import QServer, SendTestClient, SendNodesClient
from .widgets import ToolBar, LogWidgets, ErrorDialog, ConnectionsWidget
from .settings import AppSettings
from .local.mock import nuke

LOGGER = logging.getLogger('nukeserversocket')

# TODO: Refactor


def _init_settings():
    """Set up initial settings for the application.

    When called, will:
      1. Create the src/.tmp folder if doesn't exists.
      2. Set the transfer_nodes.tmp file path in the configuration file.
      3. Validate the server port value in the configuration file.
    """
    tmp_folder = os.path.join(
        os.path.abspath(os.path.dirname(__file__)), '.tmp'
    )

    if not os.path.exists(tmp_folder):
        os.mkdir(tmp_folder)

    settings = AppSettings()
    settings.validate_port_settings()

    if nuke.env.get('NukeVersionMajor') == 14:
        settings.setValue('connection_type/tcp', True)
        settings.setValue('connection_type/websocket', False)

    settings.setValue('path/transfer_file',
                      os.path.join(tmp_folder, 'transfer_nodes.tmp'))

    LOGGER.debug('Settings file: %s', settings.fileName())


class MainWindowWidget(QWidget):
    """Main window widgets and logic.

    This is were all of the main widgets are laid out. Class also deals with
    a higher level logic of user interaction when clicking the various buttons.
    """

    def __init__(self):
        """Init method for MainWindowWidget."""
        QWidget.__init__(self)
        LOGGER.debug('Main :: init')
        _init_settings()

        self.connections = ConnectionsWidget(parent=self)

        self.connect_btn = self.connections.buttons.connect_btn
        self.connect_btn.toggled.connect(self.toggle_connection)

        self.send_btn = self.connections.buttons.send_btn
        self.send_btn.clicked.connect(self.send_nodes)

        self.test_btn = self.connections.buttons.test_btn
        self.test_btn.clicked.connect(self.send_test)

        self.log_widgets = LogWidgets()

        _layout = QVBoxLayout()
        _layout.addWidget(self.connections)
        _layout.addWidget(self.log_widgets)

        self.setLayout(_layout)

        self._server = None
        self._client = None

    def _toggle_widget_modification(self, state):  # type: (bool) -> None
        """Enable/disable connection widgets modification.

        When connected the port and the sender mode will be disabled.

        Args:
            state (bool): state of the widget.
        """
        self.connections.server_port.setEnabled(state)
        self.connections.sender_mode.setEnabled(state)

    def _disconnect(self):
        """Disconnect server.

        Set the connection button state to `False`, which will trigger a signal
        that toggles the connection with a falsy value.
        """
        # Review: why not calling directly toggle_connection(False)?
        self.connect_btn.setChecked(False)

    def setup_server(self):
        """Set up the server class and its custom signals.

        Returns:
            QServer: the server object.
        """
        def _setup_socket_log(socket):
            """Set up socket log signals."""
            socket.state_changed.connect(self.log_widgets.set_status_text)
            socket.received_text.connect(self.log_widgets.set_received_text)
            socket.output_text.connect(self.log_widgets.set_output_text)
            socket.execution_error.connect(
                lambda text: ErrorDialog(text, self).show()
            )

        _server = QServer()
        _server.server_timeout.connect(
            self.connections._timeout._server_timeout.setText)

        _server.timeout.connect(self._disconnect)
        _server.state_changed.connect(self.log_widgets.set_status_text)
        _server.socket_ready.connect(_setup_socket_log)

        return _server

    def toggle_connection(self, state):  # type: (bool) -> None
        """Toggle connection state."""
        def _start_connection():
            """Start connection to server."""
            self._server = self.setup_server()

            try:
                status = self._server.start_server()
            except RuntimeError as err:
                LOGGER.error('server did not connect: %s', err)
                self.connections._disconnect()
                return False
            else:
                LOGGER.debug('server is connected: %s', status)
                self._toggle_widget_modification(False)

            return bool(status)

        if state:
            return _start_connection()
        try:
            self._server.close_server()
        except AttributeError:
            # if function is called with False as an argument when connection
            # has never started, will cause a AttributeError  because _server
            # hasn't been declared yet
            pass

        self._toggle_widget_modification(True)

    def send_nodes(self):
        """Send the selected Nuke Nodes using the internal client.

        Returns:
            SendNodesClient: SendNodesClient object.
        """
        self._client = SendNodesClient()
        self._connect_client(self.send_btn)
        self._client.client_timeout.connect(
            self.connections._timeout._socket_timeout.setText)
        return self._client

    def send_test(self):
        """Send a test message using the internal _client.

        Returns:
            SendTestClient: SendTestClient object.
        """
        self._client = SendTestClient()
        self._connect_client(self.test_btn)
        self._client.client_timeout.connect(
            self.connections._timeout._client_timeout.setText)
        return self._client

    def _connect_client(self, client_btn):  # type: (QPushButton) -> None
        """Connect the client to host and update status log.

        Args:
            client_btn (QPushButton): the client button to enable back when
            client is ready so send new data. This will be emitted from the
            client object signal.
        """
        self._client.client_ready.connect(client_btn.setEnabled)
        self._client.state_changed.connect(self.log_widgets.set_status_text)
        self._client.connect_to_host()


class MainWindow(QMainWindow):
    """Custom QMainWindow class.

    The class comes with a statusbar and a toolbar. When an exception happens,
    it will spawn an ErrorDialog widget.
    """

    def __init__(self, main_widget=MainWindowWidget):
        """Init method for main window widget."""
        QMainWindow.__init__(self)
        self.setWindowTitle('NukeServerSocket')

        toolbar = ToolBar()
        self.addToolBar(toolbar)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        try:
            main_widgets = main_widget()
        except Exception as err:  # skipcq: PYL-W0703
            ErrorDialog(err, self).show()
            LOGGER.exception(err)
        else:
            self.setCentralWidget(main_widgets)


try:
    import nukescripts
except ImportError:
    pass
else:
    nukescripts.panels.registerWidgetAsPanel(
        'NukeServerSocket.nukeserversocket.main.MainWindow', 'NukeServerSocket',
        'NukeServerSocket.MainWindow')
