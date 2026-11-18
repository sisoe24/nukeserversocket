
from __future__ import annotations

import socket
import textwrap
from typing import TYPE_CHECKING, Optional

from ._qt import (Qt, Slot, QLabel, QTimer, QWidget, QSpinBox, QGroupBox,
                  QFormLayout, QHBoxLayout, QMainWindow, QPushButton, QListWidget,
                  QSizePolicy, QVBoxLayout, QListWidgetItem)

from .logger import ConsoleHandler, get_logger
from .tools import CODE_TOOL, ToolSet
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


def _tools_summary(toolset: ToolSet, tools_file: str, from_env: bool) -> str:
    """Describe the loaded tools file for the Logs, e.g. "Tools file x.json: 2 tools, code on"."""
    count = len(toolset.tools)
    parts = [f'{count} tool' if count == 1 else f'{count} tools']
    if toolset.skipped:
        parts.append(f'{len(toolset.skipped)} skipped')
    parts.append('code on' if toolset.allow_arbitrary_code else 'code off')

    source = ' (NSS_TOOLS)' if from_env else ''
    return f'Tools file {tools_file}{source}: {", ".join(parts)}'


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

    def get_disabled_tools(self) -> list:
        return self._settings.get('disabled_tools')

    def set_tool_enabled(self, name: str, enabled: bool):
        disabled = [n for n in self.get_disabled_tools() if n != name]
        self._settings.set('disabled_tools', disabled if enabled else [*disabled, name])

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

    def _add_tool(self, name: str, tooltip: str, on: bool, enabled: bool = True):
        # set everything before addItem: a change after it emits itemChanged
        item = QListWidgetItem(name)
        item.setToolTip(tooltip)
        flags = Qt.ItemIsUserCheckable
        if enabled:
            flags |= Qt.ItemIsEnabled
        item.setFlags(flags)
        item.setCheckState(Qt.Checked if on else Qt.Unchecked)
        self.tools_list.addItem(item)

    def set_tools(self, toolset: ToolSet):
        self.tools_list.clear()
        if toolset.allow_arbitrary_code:
            self._add_tool(CODE_TOOL, 'Run any Python code. Clear to refuse code from MCP clients.',
                           CODE_TOOL not in toolset.disabled)
        else:
            # the tools file turned code off; the panel cannot turn it back on
            self._add_tool(CODE_TOOL, f'Code is off: {toolset.code_off_reason}.', False,
                           enabled=False)
        for tool in toolset.available.values():
            # the full description is a prompt for agents: show the first sentence
            summary = tool.description.split('. ')[0].split('\n')[0]
            self._add_tool(tool.name, textwrap.fill(summary, 60), tool.name not in toolset.disabled)
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
        self._view.tools_list.itemChanged.connect(self._on_tool_toggled)

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

    @Slot(QListWidgetItem)
    def _on_tool_toggled(self, item: QListWidgetItem):
        if not item.flags() & Qt.ItemIsEnabled:
            # a skipped tool, or code that the tools file turned off
            return
        name = item.text()
        enabled = item.checkState() == Qt.Checked
        disabled = self._server.toolset.disabled
        if enabled == (name not in disabled):
            return
        if enabled:
            disabled.discard(name)
        else:
            disabled.add(name)
        self._model.set_tool_enabled(name, enabled)
        LOGGER.info('%s %s.', 'Turned on' if enabled else 'Turned off', name)

    @Slot()
    def _on_port_change(self):
        self._model.set_port(self._view.port_input.value())

    @Slot(bool)
    def _on_connect(self, should_connect: bool):
        if not should_connect or self._server.isListening():
            self._close_connection()
            return

        port = self._view.port_input.value()
        tools_file, from_env = self._model.get_tools_file()
        listening = self._server.try_connect(
            port,
            allow_lan=self._model.get_allow_lan(),
            tools_file=tools_file,
            disabled_tools=self._model.get_disabled_tools(),
        )
        if not listening:
            LOGGER.error('Failed to establish connection. %s.', self._server.errorString())
            self._close_connection()
            return

        toolset = self._server.toolset
        ip = self._model.get_ip()
        LOGGER.info('Listening on %s:%s', ip, port)
        if tools_file:
            LOGGER.info('%s', _tools_summary(toolset, tools_file, from_env))

        self._view.ip_label.setText(ip)
        self._view.set_tools(toolset)
        self._start_timer()
        self._view.port_input.setEnabled(False)
        self._view.set_connected()

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
