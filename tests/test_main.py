import pytest

from PySide2 import QtCore
from PySide2.QtWidgets import (
    QGroupBox
)

from src.main import MainWindowWidget
from tests.run_app import _MainWindow


class TestAppIsIdle:

    def test_is_idle(self,  connection_widgets):
        """Test if connection text status is Idle"""
        assert connection_widgets._is_connected.text() == 'Idle'

    def test_port_is_enabled(self, connection_widgets):
        """Test if port widget modification are enabled."""
        assert connection_widgets.server_port.isEnabled() is True

    def test_port_is_changed(self, connection_widgets):
        """Test if port widget can be changed to a different value."""
        port = connection_widgets.server_port

        port_value = port.value()
        port.setValue(port_value + 1)

        assert port.value() != port_value

    def test_ip_entry_readonly(self, connection_widgets):
        """Test if qlinedit widget is readonly."""
        local_ip = connection_widgets.ip_entry
        assert local_ip.isReadOnly() is True

    def test_sender_mode_enabled(self, connection_widgets):
        """Test if sender radio button widget is enabled."""
        sender_mode = connection_widgets.sender_mode
        assert sender_mode.isEnabled() is True

    def test_receive_mode_active(self, connection_widgets):
        """Test if receive radio button widget is toggled."""
        receiver = connection_widgets.receiver_mode
        assert receiver.isChecked() is True

    def test_log_widgets(self, main_app):
        """Test if logs widgets are empty."""
        log_widgets = main_app.log_widgets
        for widget in log_widgets.findChildren(QGroupBox):
            widget_text = widget.text_box.toPlainText()
            assert widget_text == ''


def test_is_connected(qtbot):
    widget = _MainWindow()
    widget.show()
    qtbot.addWidget(widget)

    main = widget.main_window.main_app
    connections = main.connections

    qtbot.mouseClick(main.connect_btn, QtCore.Qt.LeftButton)

    assert connections._is_connected.text() == 'Connected'


def test_enable_test_btn(qtbot):
    widget = _MainWindow()
    widget.show()
    qtbot.addWidget(widget)

    main = widget.main_window.main_app
    qtbot.mouseClick(main.connect_btn, QtCore.Qt.LeftButton)

    assert main.test_btn.isEnabled() is True


def test_disable_send_btn(qtbot):
    widget = _MainWindow()
    widget.show()
    qtbot.addWidget(widget)

    main = widget.main_window.main_app
    qtbot.mouseClick(main.connect_btn, QtCore.Qt.LeftButton)

    assert main.send_btn.isEnabled() is False


def test_port_is_disable(qtbot):
    widget = _MainWindow()
    widget.show()
    qtbot.addWidget(widget)

    main = widget.main_window.main_app
    qtbot.mouseClick(main.connect_btn, QtCore.Qt.LeftButton)

    assert main.send_btn.isEnabled() is False
