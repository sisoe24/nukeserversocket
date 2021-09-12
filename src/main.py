# coding: utf-8
from __future__ import print_function

import logging

from PySide2.QtWidgets import (
    QErrorMessage,
    QMainWindow,
    QPushButton,
    QStatusBar,
    QVBoxLayout,
    QWidget
)

from .utils import NSE, SettingsState
from .connection import Server, ClientTest
from .widgets import (
    TextWidgets, ServerStatus, ErrorDialog, ToolBar
)

LOGGER = logging.getLogger('NukeServerSocket.main')
LOGGER.debug('\nSTART APPLICATION')


class MainWindowWidget(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)
        self.settings = SettingsState()
        self.settings.verify_port_config()

        self.main_window = parent

        self.connect_btn = QPushButton("Connect")
        self.connect_btn.setCheckable(True)
        self.connect_btn.toggled.connect(self._validate_connection)

        self.test_btn = QPushButton("Test Server Receiver")
        self.test_btn.setToolTip('Set server by sending a simple message')
        self.test_btn.setEnabled(False)
        self.test_btn.clicked.connect(self._test_send)

        # TODO: don't like the text widget ping pong between classes
        self.text_widgets = TextWidgets()
        self.server_status = ServerStatus()

        _layout = QVBoxLayout()
        _layout.addWidget(self.server_status)
        _layout.addWidget(self.connect_btn)
        _layout.addWidget(self.test_btn)
        _layout.addWidget(self.text_widgets)

        self.setLayout(_layout)

        self.server = None
        self.tcp_test = None

        # Initialize NSE when plugin gets created from Nuke
        NSE()

    def _test_send(self):
        """Test connection internally from Qt."""
        self.tcp_test = ClientTest()
        self.tcp_test.send_message()

    def _show_port_error(self):
        """Error message when port is not in the correct range."""
        err_msg = QErrorMessage(self)
        err_msg.setWindowTitle('NukeServerSocket')
        err_msg.showMessage('Port should be between 49152 and 65535')
        err_msg.show()

    def _update_port(self):
        """Update port on the ini file from the text entry field widget.

        If port is changed manually on the .ini file, then app will pick the one
        from the file, but it will show the old on inside the widget.
        """
        self.settings.setValue(
            'server/port', self.server_status.port_entry.text())

    def _validate_connection(self, state):
        if not self.server_status.is_valid_port():
            self._show_port_error()
            return

        self._update_port()

        self.test_btn.setEnabled(state)
        self.server_status.port_entry.setEnabled(not state)

        if state:
            is_connected = self._setup_connection()

            if is_connected:
                self._update_ui_connect()
            else:
                self._update_ui_problems()
        else:
            self._update_ui_disconnect()

    def _update_ui_connect(self):
        """Update ui when connected."""
        _cs = 'Connected'
        self.main_window.status_bar.showMessage(_cs)
        self.text_widgets.set_status_text(_cs)
        self.connect_btn.setText('Disconnect')

    def _update_ui_problems(self):
        """Update ui when connection problem.

        This will call _validate_connection() back and execute the disconnect_event
        """
        self.connect_btn.setChecked(False)
        self.main_window.status_bar.showMessage(
            'The specified port might be already in use.')

    def _update_ui_disconnect(self):
        """Update ui when disconnected."""
        _ds = 'Disconnected'
        self.text_widgets.set_status_text(_ds + '\n----')
        self.main_window.status_bar.showMessage(_ds)
        self.connect_btn.setText('Connect')
        self.server_status.set_idle()

        self.server.server.close()

    def _setup_connection(self):
        """Setup connection to server.

        Returns:
            str: status of the connection: True if successful False otherwise
        """
        self.server = Server(self.text_widgets)
        status = self.server.start_server()
        self.server_status.update_status(status)

        LOGGER.debug('server is connected: %s', status)

        return status


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)
        self.setWindowTitle("NukeServerSocket")

        toolbar = ToolBar()
        self.addToolBar(toolbar)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        try:
            main_window = MainWindowWidget(self)
        except Exception as err:
            ErrorDialog(err, self).show()
            LOGGER.critical(err, exc_info=True)
        else:
            self.setCentralWidget(main_window)


try:
    import nukescripts
except ImportError as error:
    pass
else:
    nukescripts.panels.registerWidgetAsPanel(
        'NukeServerSocket.src.main.MainWindow', 'NukeServerSocket',
        'NukeServerSocket.MainWindow')
