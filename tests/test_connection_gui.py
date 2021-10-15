import random

import pytest

from src.main import MainWindowWidget
from src.connection import Server

RANDOM_IP = '192.168.1.%s' % random.randint(10, 99)


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

    status_text = None
    received_text = None
    output_text = None

    def test_label(self, ui):
        """Test if UI label is properly set."""
        assert ui.connections._is_connected.text() == self.label

    def test_port_is_enabled(self, ui):
        """Test if port widget modification are enabled."""
        assert ui.connections.server_port.isEnabled() is self.port_is_enabled

    def test_ip_entry_readonly(self, ui):
        """Test if QLineEdit widget is readonly."""
        local_ip = ui.connections.ip_entry
        assert local_ip.isReadOnly() is self.ip_entry_readonly

    def test_sender_mode_enabled(self, ui):
        """Test if sender radio button widget is enabled."""
        sender_mode = ui.connections.sender_mode
        assert sender_mode.isEnabled() is self.sender_mode_enabled

    def test_receive_mode_active(self, ui):
        """Test if receive radio button widget is toggled."""
        receiver = ui.connections.receiver_mode
        assert receiver.isChecked() is self.receiver_mode_active

    def test_receiver_btn(self, ui):
        """Test if receiver button is disabled"""
        test_btn = ui.test_btn
        assert test_btn.isEnabled() is self.test_btn_enabled

    def test_send_btn(self, ui):
        """Test if send button is disabled"""
        send_btn = ui.send_btn
        assert send_btn.isEnabled() is self.send_btn_enabled

    def test_connect_btn(self, ui):
        """Test if connect button is enabled"""
        connect_btn = ui.connect_btn
        assert connect_btn.isEnabled() is self.connect_btn_enabled

    def test_connect_btn_text(self, ui):
        """Test if connect button is enabled"""
        connect_btn = ui.connect_btn
        assert connect_btn.text() == self.connect_btn_text

    def test_log_widgets(self, ui):
        """Test if logs widgets are empty."""
        # TODO: maybe this is not necessary at this point
        # also should test clear log button
        log_widgets = ui.log_widgets

        status = log_widgets.status_widget.text_box
        received = log_widgets.received_widget.text_box
        output = log_widgets.output_widget.text_box

        assert self.status_text in status.toPlainText()
        assert self.received_text in received.toPlainText()
        assert self.output_text in output.toPlainText()


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

        cls.status_text = ''
        cls.received_text = ''
        cls.output_text = ''


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

        cls.status_text = 'Connected. Server listening to port'
        cls.received_text = ''
        cls.output_text = ''

    def test_raise_error_if_connected(self, ui):
        """Check if RuntimeError is raised when address is already connected."""
        with pytest.raises(RuntimeError, match='.+The bound address is already in use'):
            s = Server()
            s.start_server()


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

        cls.status_text = ''
        cls.received_text = ''
        cls.output_text = ''

    def test_change_ip_entry(self, ui):
        """Check if ip entry can be changed."""
        # TODO: this doesnt need to a be a test but it help writing the setting file
        # TODO: when changing port to the same default port will not write to config file
        ip_entry = ui.connections.ip_entry
        ip_entry.setText(RANDOM_IP)
        assert ip_entry.text() == RANDOM_IP

    def test_send_local_ip(self, ui, config_file):
        """Check if `local_ip` is saved correctly in settings.ini when changed."""
        settings_values = config_file['server']['send_to_address']
        assert settings_values == RANDOM_IP


def test_not_connected_label(ui):
    """Check if RuntimeError is raised when address is already connected."""
    s = Server()
    s.start_server()

    ui.toggle_connection(True)
    assert ui.connections._is_connected.text() == 'Not Connected'
