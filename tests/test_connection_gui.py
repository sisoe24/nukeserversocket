import pytest

from PySide2.QtWidgets import (
    QGroupBox
)

from src.main import MainWindowWidget


class GuiApp:
    label = None
    port_is_enabled = None
    ip_entry_readonly = None

    sender_mode_enabled = None
    receiver_mode_active = None

    send_btn_enabled = None
    test_btn_enabled = None
    connect_btn_enabled = None

    connect_btn_text = None

    status_widget = None
    received_widget = None
    output_widget = None

    def test_label(self, connection_widgets):
        assert connection_widgets._is_connected.text() == self.label

    def test_port_is_enabled(self, connection_widgets):
        """Test if port widget modification are enabled."""
        assert connection_widgets.server_port.isEnabled() is self.port_is_enabled

    def test_ip_entry_readonly(self, connection_widgets):
        """Test if QLineEdit widget is readonly."""
        local_ip = connection_widgets.ip_entry
        assert local_ip.isReadOnly() is self.ip_entry_readonly

    def test_sender_mode_enabled(self, connection_widgets):
        """Test if sender radio button widget is enabled."""
        sender_mode = connection_widgets.sender_mode
        assert sender_mode.isEnabled() is self.sender_mode_enabled

    def test_receive_mode_active(self, connection_widgets):
        """Test if receive radio button widget is toggled."""
        receiver = connection_widgets.receiver_mode
        assert receiver.isChecked() is self.receiver_mode_active

    def test_receiver_btn(self, main_window: MainWindowWidget):
        """Test if receiver button is disabled"""
        test_btn = main_window.test_btn
        assert test_btn.isEnabled() is self.test_btn_enabled

    def test_send_btn(self, main_window: MainWindowWidget):
        """Test if send button is disabled"""
        send_btn = main_window.send_btn
        assert send_btn.isEnabled() is self.send_btn_enabled

    def test_connect_btn(self, main_window: MainWindowWidget):
        """Test if connect button is enabled"""
        connect_btn = main_window.connect_btn
        assert connect_btn.isEnabled() is self.connect_btn_enabled

    def test_connect_btn_text(self, main_window: MainWindowWidget):
        """Test if connect button is enabled"""
        connect_btn = main_window.connect_btn
        assert connect_btn.text() == self.connect_btn_text

    def test_log_widgets(self, main_window: MainWindowWidget):
        """Test if logs widgets are empty."""
        log_widgets = main_window.log_widgets

        status = log_widgets.status_widget.text_box
        received = log_widgets.received_widget.text_box
        output = log_widgets.output_widget.text_box

        assert self.status_widget in status.toPlainText()
        assert self.received_widget in received.toPlainText()
        assert self.output_widget in output.toPlainText()


class TestGuiIsIdle(GuiApp):
    """Test UI app when is in idle state."""

    @classmethod
    def setup_class(cls):
        cls.label = "Idle"
        cls.port_is_enabled = True
        cls.ip_entry_readonly = True

        cls.sender_mode_enabled = True
        cls.receiver_mode_active = True

        cls.send_btn_enabled = False
        cls.test_btn_enabled = False
        cls.connect_btn_enabled = True

        cls.connect_btn_text = 'Connect'

        cls.status_widget = ''
        cls.received_widget = ''
        cls.output_widget = ''


@pytest.mark.usefixtures('start_connection')
class TestGuiIsConnected(GuiApp):

    @classmethod
    def setup_class(cls):
        cls.label = "Connected"
        cls.port_is_enabled = False
        cls.ip_entry_readonly = True

        cls.sender_mode_enabled = False
        cls.receiver_mode_active = True

        cls.send_btn_enabled = False
        cls.test_btn_enabled = True
        cls.connect_btn_enabled = True

        cls.connect_btn_text = 'Disconnect'

        cls.status_widget = 'Connected. Server listening to port'
        cls.received_widget = ''
        cls.output_widget = ''


@pytest.mark.usefixtures('activate_sender_mode')
class TestGuiIsSenderMode(GuiApp):

    @classmethod
    def setup_class(cls):
        cls.label = "Ready to send"
        cls.port_is_enabled = True
        cls.ip_entry_readonly = False

        cls.sender_mode_enabled = True
        cls.receiver_mode_active = False

        cls.send_btn_enabled = True
        cls.test_btn_enabled = False
        cls.connect_btn_enabled = False

        cls.connect_btn_text = 'Connect'

        cls.status_widget = 'Disconnected'
        cls.received_widget = ''
        cls.output_widget = ''


@pytest.mark.skip('not implemented yet')
class TestGuiIsNotConnected(GuiApp):
    @classmethod
    def setup_class(cls):
        pass
