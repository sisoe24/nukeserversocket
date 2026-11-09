
from __future__ import annotations

import socket
from typing import TYPE_CHECKING, Optional

from ._qt import (Qt, Slot, QLabel, QTimer, QWidget, QSpinBox, QGroupBox,
                  QFormLayout, QHBoxLayout, QMainWindow, QPushButton, QListWidget,
                  QSizePolicy, QVBoxLayout, QListWidgetItem)

from .logger import ConsoleHandler, get_logger
from .tools import BUILTIN_TOOL, ToolSet
from .server import NssServer
from .console import NssConsole
from .toolbar import ToolBar
from .version import __version__
from .settings import get_settings
from .settings_ui import NssSettingsUI

if TYPE_CHECKING:
    from .settings import _NssSettings
    from .controllers.base import BaseController

LOGGER = get_logger()


class MainModel:
    def __init__(self, settings: _NssSettings):
        self._settings = settings

    def get_ip(self):
        """Get the IP address that clients can reach the server on."""
        if not self.get_allow_lan():
            return '127.0.0.1'

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip, _ = s.getsockname()
        except socket.error:
            ip = '127.0.0.1'
        finally:
            s.close()
        return ip

    def get_port(self):
        return self._settings.get('port')

    def set_port(self, port: int):
        return self._settings.set('port', port)

    def get_server_timeout(self):
        return self._settings.get('server_timeout')

    def get_auto_start(self):
        return self._settings.get('auto_start')

    def get_allow_lan(self):
        return self._settings.get('allow_lan')

    def get_tools_file(self):
        return self._settings.tools_file()

    def get_enable_debug(self):
        return self._settings.get('enable_debug')

    def set_enable_debug(self, state: bool):
        return self._settings.set('enable_debug', state)

    def get_wrap_lines(self):
        return self._settings.get('wrap_lines')

    def set_wrap_lines(self, state: bool):
        return self._settings.set('wrap_lines', state)


class MainView(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        """Init method for MainWindowWidget."""
        super().__init__(parent)

        self.connect_btn = QPushButton('Connect')
        self.connect_btn.setCheckable(True)
        self.connect_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        # Reserve width for the longer label, so the form does not shift on toggle.
        self.connect_btn.setMinimumWidth(
            self.connect_btn.fontMetrics().horizontalAdvance('Disconnect') + 24)
        self.connect_btn.setMinimumHeight(40)

        self.console = NssConsole()

        self.status_label = QLabel('Idle')

        self.ip_label = QLabel()

        self.port_input = QSpinBox()
        self.port_input.setRange(49512, 65535)
        self.port_input.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        form_layout = QFormLayout()
        # the macOS style keeps fields at their first size hint, which clips changed text
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.setAlignment(Qt.AlignVCenter)
        form_layout.addRow('Status:', self.status_label)
        form_layout.addRow('IP:', self.ip_label)
        form_layout.addRow('Port:', self.port_input)
        form_layout.addRow(self.connect_btn)

        server_box = QGroupBox('Server')
        server_box.setLayout(form_layout)

        # the tools file loads on connect, so the list stays empty until then
        self.tools_list = QListWidget()
        # the Server box sets the row height; the list fills it and scrolls
        self.tools_list.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Ignored)

        mcp_layout = QVBoxLayout()
        mcp_layout.addWidget(self.tools_list)

        mcp_box = QGroupBox('MCP tools')
        mcp_box.setLayout(mcp_layout)

        top_layout = QHBoxLayout()
        top_layout.addWidget(server_box, 1)
        top_layout.addWidget(mcp_box, 1)

        layout = QVBoxLayout()
        layout.addLayout(top_layout)
        layout.addWidget(self.console, 1)

        self.setLayout(layout)

        self.set_disconnected()

    def _update_status_connection(self, label: str, style: str, button_txt: str):
        self.status_label.setText(label)
        self.status_label.setStyleSheet(style)
        self.connect_btn.setText(button_txt)

    def set_connected(self):
        self._update_status_connection('Connected', 'color: green', 'Disconnect')

    def set_disconnected(self):
        self._update_status_connection('Idle', 'color: orange', 'Connect')
        # the tools load again on the next connect
        self.tools_list.clear()

    def set_tools(self, toolset: ToolSet, tools_file: str):
        self.tools_list.clear()
        if toolset.allow_code:
            self.tools_list.addItem(BUILTIN_TOOL)
        for tool in toolset.tools.values():
            item = QListWidgetItem(tool.name)
            item.setToolTip(tool.description)
            self.tools_list.addItem(item)
        for name, reason in toolset.skipped.items():
            item = QListWidgetItem(name)
            item.setToolTip(f'Skipped: {reason}')
            item.setFlags(Qt.NoItemFlags)
            self.tools_list.addItem(item)


class MainController:
    def __init__(self, view: MainView, model: MainModel, server: NssServer):
        """Init method for MainWindowWidget."""
        self._view = view
        self._model = model

        self._server = server
        self._server.on_data_received.connect(self._on_data_received)

        self._view.ip_label.setText(self._model.get_ip())
        self._view.port_input.setValue(self._model.get_port())
        self._view.port_input.valueChanged.connect(self._on_port_change)
        self._view.connect_btn.clicked.connect(self._on_connect)

        console = self._view.console
        console.enable_debug.setChecked(self._model.get_enable_debug())
        console.wrap_lines.setChecked(self._model.get_wrap_lines())
        console.enable_debug.toggled.connect(self._model.set_enable_debug)
        console.wrap_lines.toggled.connect(self._model.set_wrap_lines)

        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timeout)
        self._timer.setSingleShot(True)

        if self._model.get_auto_start():
            # Defer until the event loop runs so the host app finishes building its UI.
            QTimer.singleShot(0, self._view.connect_btn.click)

    def _start_timer(self):
        timeout = self._model.get_server_timeout()
        if timeout > 0:
            self._timer.start(timeout)

    @Slot()
    def _on_timeout(self):
        minutes = self._model.get_server_timeout() // 60000
        self._close_connection(f'no request for {minutes} min (Server Timeout)')

    @Slot()
    def _on_data_received(self):
        self._start_timer()

    @Slot()
    def _on_port_change(self):
        self._model.set_port(self._view.port_input.value())

    @Slot(bool)
    def _on_connect(self, should_connect: bool):
        port = self._view.port_input.value()
        if should_connect and not self._server.isListening():
            tools_file, from_env = self._model.get_tools_file()
            if self._server.try_connect(port, self._model.get_allow_lan(), tools_file):
                toolset = self._server.toolset
                ip = self._model.get_ip()
                LOGGER.info('Listening on %s:%s', ip, port)
                if tools_file:
                    count = len(toolset.tools)
                    skipped = f', {len(toolset.skipped)} skipped' if toolset.skipped else ''
                    LOGGER.info('Tools file %s%s: %s tool%s%s, code %s', tools_file,
                                ' (NSS_TOOLS)' if from_env else '', count,
                                '' if count == 1 else 's', skipped,
                                'on' if toolset.allow_code else 'off')

                self._view.ip_label.setText(ip)
                self._view.set_tools(toolset, tools_file)
                self._start_timer()
                self._view.port_input.setEnabled(False)
                self._view.set_connected()

            else:
                LOGGER.error('Failed to establish connection. %s.', self._server.errorString())
                self._close_connection()
        else:
            self._close_connection()

    def _close_connection(self, reason: str = ''):
        was_listening = self._server.isListening()
        self._server.close()
        self._view.set_disconnected()
        self._view.port_input.setEnabled(True)
        self._view.connect_btn.setChecked(False)
        self._timer.stop()
        if was_listening:
            LOGGER.info('Stopped listening%s', f': {reason}' if reason else '.')


class NukeServerSocket(QMainWindow):
    def __init__(self, editor: BaseController, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setWindowTitle('NukeServerSocket')
        print(f'\nLoading NukeServerSocket: {__version__}')

        # NOTE: Most variables are bound to the class only to avoid garbage collection.

        self.settings = get_settings()

        self.editor = editor
        self.editor.settings = self.settings

        self.view = MainView()
        self.model = MainModel(self.settings)
        self.controller = MainController(self.view, self.model, NssServer(editor))

        # I don't like this but anywheres else I put it, it creates problems with
        # the tests.
        LOGGER.console = ConsoleHandler(self.view.console)
        # the saved Enable Debug state was applied before this handler existed
        self.view.console.sync_log_level()

        self.settings_ui = NssSettingsUI(self.settings)

        self.toolbar = ToolBar(self.view)
        self.toolbar.add_widget(title='Settings', widget=self.settings_ui.view)

        self.addToolBar(self.toolbar)
        self.setCentralWidget(self.view)
