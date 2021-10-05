import pytest

from PySide2.QtWidgets import (
    QGroupBox
)

from src.main import MainWindowWidget


class TestAppIsIdle:
    """Test UI app when is in idle state."""

    def test_is_idle(self, connection_widgets):
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
        """Test if QLineEdit widget is readonly."""
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

    @pytest.mark.skip(reason='check better')
    def test_log_widgets(self, main_window):
        """Test if logs widgets are empty."""
        log_widgets = main_window.log_widgets
        for widget in log_widgets.findChildren(QGroupBox):
            widget_text = widget.text_box.toPlainText()
            assert widget_text == ''

    def test_receiver_btn(self, main_window: MainWindowWidget):
        """Test if receiver button is disabled"""
        test_btn = main_window.test_btn
        assert test_btn.isEnabled() is False

    def test_send_btn(self, main_window: MainWindowWidget):
        """Test if send button is disabled"""
        send_btn = main_window.send_btn
        assert send_btn.isEnabled() is False

    def test_connect_btn(self, main_window: MainWindowWidget):
        """Test if connect button is enabled"""
        connect_btn = main_window.connect_btn
        assert connect_btn.isEnabled() is True

    def test_connect_btn_text(self, main_window: MainWindowWidget):
        """Test if connect button is enabled"""
        connect_btn = main_window.connect_btn
        assert connect_btn.text() == 'Connect'

