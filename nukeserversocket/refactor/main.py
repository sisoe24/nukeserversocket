
from __future__ import annotations

import os
import sys

from PySide2.QtCore import Slot, QObject
from PySide2.QtNetwork import QTcpSocket
from PySide2.QtWidgets import (QLabel, QWidget, QSpinBox, QLineEdit,
                               QFormLayout, QMainWindow, QPushButton,
                               QVBoxLayout, QApplication)

from .api import get_ip
from .server import NssServer
from .settings import get_settings
from .widgets.loggers import LogWidgets


class MainModel:
    def get_ip(self):
        return get_ip()

    def get_port(self):
        return get_settings().get('port', 54321)

    def set_port(self, port: int):
        return get_settings().set('port', port)


class MainView(QWidget):
    def __init__(self, parent=None):
        """Init method for MainWindowWidget."""
        super().__init__(parent)

        self.connect_btn = QPushButton('Connect')
        self.connect_btn.setCheckable(True)

        self.logs = LogWidgets()

        self.status_label = QLabel('Idle')
        self.status_label.setStyleSheet('color: orange')

        self.ip_label = QLabel()
        self.ip_label.setText(get_ip())

        self.port_input = QSpinBox()
        self.port_input.setRange(49512, 65535)

        form_layout = QFormLayout()
        form_layout.addRow('Status:', self.status_label)
        form_layout.addRow('IP:', self.ip_label)
        form_layout.addRow('Port:', self.port_input)

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.connect_btn)
        layout.addWidget(self.logs)
        self.setLayout(layout)

    def _update_status_connection(self, label: str, style: str, button_txt: str):
        self.status_label.setText(label)
        self.status_label.setStyleSheet(style)
        self.connect_btn.setText(button_txt)

    def set_connected(self):
        self._update_status_connection('Connected', 'color: green', 'Disconnect')

    def set_disconnected(self):
        self._update_status_connection('Idle', 'color: orange', 'Connect')

    def set_failed(self):
        self._update_status_connection('Failed', 'color: red', 'Connect')

    def set_connecting(self):
        self._update_status_connection('Connecting...', 'color: orange', 'Connecting...')
        self.connect_btn.setEnabled(False)


class MainController:
    def __init__(self, view: MainView, model: MainModel):
        """Init method for MainWindowWidget."""
        self._view = view
        self._model = model

        self._view.ip_label.setText(self._model.get_ip())
        self._view.port_input.setValue(self._model.get_port())
        self._view.port_input.valueChanged.connect(self._on_port_change)
        self._view.connect_btn.clicked.connect(self._on_connect)

        self.server = NssServer()
        self.server.on_data_received.connect(self._on_data_received)
        self.server.on_data_written.connect(self._on_data_written)

    @Slot(str)
    def _on_data_received(self, data: str):
        self._view.logs.received_widget.write(data)

    @Slot(str)
    def _on_data_written(self, data: str):
        self._view.logs.output_widget.write(data)

    @Slot(int)
    def _on_port_change(self):
        self._model.set_port(self._view.port_input.value())

    @Slot(bool)
    def _on_connect(self, should_connect: bool):
        if should_connect and not self.server.is_listening():
            status = self.server.listen(self._view.port_input.value())
            if status:
                self._view.set_connected()
                self._view.port_input.setEnabled(False)
            else:
                self._view.set_failed()
        else:
            self._view.set_disconnected()
            self.server.close()
            self._view.port_input.setEnabled(True)


class NukeServerSocket(QMainWindow):

    def __init__(self, parent=None):
        """Init method for NukeServerSocket."""
        super().__init__(parent)

        os.environ['NUKE_SERVER_SOCKET_PORT'] = '54321'

        self.view = MainView()
        self.model = MainModel()
        self.controller = MainController(self.view, self.model)
        self.setCentralWidget(self.view)


def main():
    """Main function for NukeServerSocket."""
    app = QApplication(sys.argv)
    window = NukeServerSocket()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
