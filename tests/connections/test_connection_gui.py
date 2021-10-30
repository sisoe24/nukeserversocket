"""Test module for the UI elements when various connection modes happen."""
import random
import configparser

from abc import ABCMeta, abstractmethod

import six
import pytest

from src.connection import QServer

RANDOM_IP = '192.168.1.%s' % random.randint(10, 99)

pytestmark = pytest.mark.connection


@six.add_metaclass(ABCMeta)
class BaseUIElements():
    """Abstract class that implements the elements that should be tested.

    Note: Although this is compatible with py2/3, in python 2 will not raise
    any error if a method is not implemeneted.
    """

    @property
    @abstractmethod
    def label(self):
        """Label of the UI."""

    @property
    @abstractmethod
    def port_is_enabled(self):
        """Port widget state."""

    @property
    @abstractmethod
    def ip_entry_readonly(self):
        """Ip QLineEdit widget state."""

    @property
    @abstractmethod
    def ip_label_text(self):
        """Ip QLabel widget text."""

    @property
    @abstractmethod
    def sender_mode_enabled(self):
        """Sender mode state."""

    @property
    @abstractmethod
    def receiver_mode_active(self):
        """Receiver mode state."""

    @property
    @abstractmethod
    def send_btn_enabled(self):
        """Send button widget state."""

    @property
    @abstractmethod
    def test_btn_enabled(self):
        """Test button widget state."""

    @property
    @abstractmethod
    def connect_btn_enabled(self):
        """Connect button widget state."""

    @property
    @abstractmethod
    def connect_btn_text(self):
        """Connect button widget text."""

    @property
    @abstractmethod
    def status_text(self):
        """Log status widget text."""

    @property
    @abstractmethod
    def received_text(self):
        """Log received widget text."""

    @property
    @abstractmethod
    def output_text(self):
        """Log output widget text."""


class GuiApp:
    """Base class for testing the UI state."""

    def test_label(self, _main_ui):
        """Test if UI label is properly set."""
        assert _main_ui.connections._is_connected.text() == self.label

    def test_port_is_enabled(self, _main_ui):
        """Test if port widget modification are enabled."""
        assert _main_ui.connections.server_port.isEnabled() is self.port_is_enabled

    def test_ip_entry_readonly(self, _main_ui):
        """Test if QLineEdit widget is readonly."""
        local_ip = _main_ui.connections.ip_entry
        assert local_ip.isReadOnly() is self.ip_entry_readonly

    def test_ip_label(self, _main_ui):
        """Test ip QLabel widget text."""
        label_text = _main_ui.connections.ip_address_label.text()
        assert label_text == self.ip_label_text

    def test_sender_mode_enabled(self, _main_ui):
        """Test if sender radio button widget is enabled."""
        sender_mode = _main_ui.connections.sender_mode
        assert sender_mode.isEnabled() is self.sender_mode_enabled

    def test_receive_mode_active(self, _main_ui):
        """Test if receive radio button widget is toggled."""
        receiver = _main_ui.connections.receiver_mode
        assert receiver.isChecked() is self.receiver_mode_active

    def test_receiver_btn(self, _main_ui):
        """Test if receiver button is disabled."""
        test_btn = _main_ui.test_btn
        assert test_btn.isEnabled() is self.test_btn_enabled

    def test_send_btn(self, _main_ui):
        """Test if send button is disabled."""
        send_btn = _main_ui.send_btn
        assert send_btn.isEnabled() is self.send_btn_enabled

    def test_connect_btn(self, _main_ui):
        """Test if connect button is enabled."""
        connect_btn = _main_ui.connect_btn
        assert connect_btn.isEnabled() is self.connect_btn_enabled

    def test_connect_btn_text(self, _main_ui):
        """Test if connect button is enabled."""
        connect_btn = _main_ui.connect_btn
        assert connect_btn.text() == self.connect_btn_text

    def test_log_widgets(self, _main_ui):
        """Test if logs widgets are empty."""
        log_widgets = _main_ui.log_widgets

        status = log_widgets.status_widget.text_box
        received = log_widgets.received_widget.text_box
        output = log_widgets.output_widget.text_box

        assert self.status_text in status.toPlainText()
        assert self.received_text in received.toPlainText()
        assert self.output_text in output.toPlainText()


class TestGuiIsIdle(GuiApp, BaseUIElements):
    """Test UI app when is in idle state."""

    label = "Idle"
    port_is_enabled = True

    ip_entry_readonly = True
    ip_label_text = 'Local IP Address'

    sender_mode_enabled = True
    receiver_mode_active = True

    send_btn_enabled = False
    test_btn_enabled = False
    connect_btn_enabled = True

    connect_btn_text = 'Connect'

    status_text = ''
    received_text = ''
    output_text = ''


@pytest.mark.usefixtures('_start_connection')
class TestGuiIsConnected(GuiApp, BaseUIElements):
    """Test UI when app is connected."""

    label = "Connected"
    port_is_enabled = False

    ip_entry_readonly = True
    ip_label_text = 'Local IP Address'

    sender_mode_enabled = False
    receiver_mode_active = True

    send_btn_enabled = False
    test_btn_enabled = True
    connect_btn_enabled = True

    connect_btn_text = 'Disconnect'

    status_text = 'Connected. Server listening to port'
    received_text = ''
    output_text = ''

    def test_raise_error_if_connected(self, _main_ui):
        """Check if RuntimeError is raised when address is in use.

        Because each method will call _start_connection, server will be already
        listening for connection when try to create a new one.
        """
        with pytest.raises(RuntimeError, match='.+address is already in use'):
            s = QServer()
            s.start_server()


class TestGuiIsSenderMode(GuiApp, BaseUIElements):
    """Test UI when app is in sender mode."""

    label = "Ready to send"
    port_is_enabled = True

    ip_entry_readonly = False
    ip_label_text = 'Send To IP Address'

    sender_mode_enabled = True
    receiver_mode_active = False

    send_btn_enabled = True
    test_btn_enabled = False
    connect_btn_enabled = False

    connect_btn_text = 'Connect'

    status_text = ''
    received_text = ''
    output_text = ''

    @pytest.fixture(autouse=True)
    def activate_sender_mode(self, _main_ui):
        """Activate the sender mode.

        After tests will activate back the receiver mode.
        """
        _main_ui.connections.sender_mode.toggle()
        yield
        _main_ui.connections.receiver_mode.toggle()

    @pytest.fixture()
    def _change_ip_entry(self, _main_ui):
        """Check if ip entry can be changed."""
        ip_entry = _main_ui.connections.ip_entry

        # XXX: if RANDOM_IP is the same as local ip, will not write the value
        # to the config file probably because it does not update its value?
        # setting the text to an empty string and then write the port seems to
        # do the trick
        ip_entry.setText('')
        ip_entry.setText(RANDOM_IP)

    def test_send_local_ip(self, _change_ip_entry,  _tmp_settings_file):
        """Check if `local_ip` is saved correctly in config when changed."""
        config = configparser.ConfigParser()
        config.read(_tmp_settings_file)

        settings_values = config['server']['send_to_address']

        assert settings_values == RANDOM_IP


def test_not_connected_label(_main_ui, _start_server):
    """Check UI label when not able to connect.

    Method will start a connection and then try to start a new one. This should
    set the UI status label to 'Not Connected' because it couldn't connect.
    """
    # start second connection from UI
    _main_ui.toggle_connection(True)
    assert _main_ui.connections._is_connected.text() == 'Not Connected'
