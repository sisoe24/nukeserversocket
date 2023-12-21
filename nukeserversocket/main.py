
from __future__ import annotations

import socket
import logging
from datetime import datetime

from PySide2.QtCore import Slot, QTimer
from PySide2.QtWidgets import (QLabel, QWidget, QSpinBox, QFormLayout,
                               QMainWindow, QPushButton, QVBoxLayout,
                               QPlainTextEdit)

from nukeserversocket.editor_controller import EditorController

from .about import about
from .server import NssServer
from .toolbar import ToolBar
from .settings import _NssSettings, get_settings

logging.basicConfig(level=logging.DEBUG)


class MainModel:
    def __init__(self, settings: _NssSettings):
        self._settings = settings

    def get_ip(self):
        """Get the IP address of the current machine."""
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


class MainView(QWidget):
    def __init__(self, parent=None):
        """Init method for MainWindowWidget."""
        super().__init__(parent)

        self.connect_btn = QPushButton('Connect')
        self.connect_btn.setCheckable(True)

        self.logs = QPlainTextEdit()
        self.logs.setReadOnly(True)

        self.clear_logs = QPushButton('Clear logs')

        self.status_label = QLabel('Idle')
        self.set_disconnected()

        self.ip_label = QLabel()

        self.port_input = QSpinBox()
        self.port_input.setRange(49512, 65535)

        form_layout = QFormLayout()
        form_layout.addRow('Status:', self.status_label)
        form_layout.addRow('IP:', self.ip_label)
        form_layout.addRow('Port:', self.port_input)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.connect_btn)
        layout.addWidget(QLabel('Logs'))
        layout.addWidget(self.logs)
        layout.addWidget(self.clear_logs)

        self.setLayout(layout)

    def _update_status_connection(self, label: str, style: str, button_txt: str):
        self.status_label.setText(label)
        self.status_label.setStyleSheet(style)
        self.connect_btn.setText(button_txt)

    def set_connected(self):
        self._update_status_connection('Connected', 'color: green', 'Disconnect')

    def set_disconnected(self):
        self._update_status_connection('Idle', 'color: orange', 'Connect')


class MainController:
    def __init__(self, view: MainView, model: MainModel, server: NssServer):
        """Init method for MainWindowWidget."""
        self._view = view
        self._model = model

        self._server = server
        self._server.on_data_received.connect(self._on_data_received)
        self._server.on_data_written.connect(self._on_data_written)

        self._view.ip_label.setText(self._model.get_ip())
        self._view.port_input.setValue(self._model.get_port())
        self._view.port_input.valueChanged.connect(self._on_port_change)
        self._view.connect_btn.clicked.connect(self._on_connect)
        self._view.clear_logs.clicked.connect(self._view.logs.clear)

        self._timer = QTimer()
        self._timer.timeout.connect(self._on_timeout)
        self._timer.setSingleShot(True)

    def _write_log(self, text: str):
        time = datetime.now().strftime('%H:%M:%S')
        self._view.logs.appendPlainText(f'[{time}] {text}')
        self._view.logs.verticalScrollBar().setValue(
            self._view.logs.verticalScrollBar().maximum())

    @Slot()
    def _on_timeout(self):
        self._write_log('Server Timeout.')
        self._close_connection()

    @Slot(str)
    def _on_data_received(self, data: str):
        self._write_log(f'Received data:\n {data}')
        self._timer.start(self._model.get_server_timeout())

    @Slot(str)
    def _on_data_written(self, data: str):
        self._write_log(f'Data written:\n {data}')

    @Slot(int)
    def _on_port_change(self):
        self._model.set_port(self._view.port_input.value())

    @Slot(bool)
    def _on_connect(self, should_connect: bool):
        port = self._view.port_input.value()
        if should_connect and not self._server.isListening():
            if self._server.try_connect(port):
                self._timer.start(self._model.get_server_timeout())
                self._write_log(f'Listening on {port}...')
                self._view.port_input.setEnabled(False)
                self._view.set_connected()
            else:
                self._write_log(f'Failed to establish connection on port {port}.')
                self._close_connection()
        else:
            self._close_connection()

    def _close_connection(self):
        self._server.close()
        self._view.set_disconnected()
        self._view.port_input.setEnabled(True)
        self._view.connect_btn.setChecked(False)
        self._write_log('Closing connection...')


class NukeServerSocket(QMainWindow):

    def __init__(self, parent=None):
        """Init method for NukeServerSocket."""
        super().__init__(parent)
        self.setWindowTitle('NukeServerSocket')
        print(f'\nNukeServerSocket: {about()["version"]}')

        editor_instance = EditorController.get_instance()
        if not editor_instance:
            raise RuntimeError('Controller is not set.')

        server = NssServer(editor_instance())

        self.view = MainView()
        self.model = MainModel(get_settings())
        self.controller = MainController(self.view, self.model, server)

        self.toolbar = ToolBar(self.view)

        self.addToolBar(self.toolbar)
        self.setCentralWidget(self.view)
