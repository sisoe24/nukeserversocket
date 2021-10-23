"""Test Port Widget module."""
import configparser

import pytest

from src.connection import QServer, nss_client
from src.widgets.connections_widget import TcpPort
from src.utils import AppSettings


def port_range(value):
    """Return True if port is in expected range."""
    return 49512 <= value <= 65535


def test_default_value_server(qtbot):
    """Test port default value if no settings.ini is found."""
    server_port = QServer().tcp_port
    assert server_port == 54321


def test_default_value_client():
    """Test port default value if no settings.ini is found."""
    server_port = nss_client.NetworkAddresses().port
    assert server_port == 54321


@pytest.fixture()
def tcp_port(qtbot):
    """Init the TcpPort widget class."""
    widget = TcpPort()
    qtbot.addWidget(widget)
    yield widget


@pytest.fixture()
def wrong_port_ui(tcp_port):
    """Change port to a wrong value."""
    tcp_port.setValue(99999)


def test_port_new_value_ui(wrong_port_ui, tcp_port):
    """Check if port auto fixes.

    If user enters a wrong value, port should auto fix into the correct range.
    """
    assert port_range(tcp_port.value())


def test_port_new_value_file(wrong_port_ui, tmp_settings_file, tcp_port):
    """Test if port change is saved into config file."""
    config = configparser.ConfigParser()
    config.read(tmp_settings_file)

    settings_values = config['server']['port']

    assert int(settings_values) == tcp_port.value()


@pytest.fixture()
def wrong_port_file(tmp_settings_file):
    """Write a bad port settings into settings.ini file."""
    config = configparser.ConfigParser()
    config['server'] = {'port': '11111'}

    with open(tmp_settings_file, 'w') as configfile:
        config.write(configfile)


def test_wrong_port_ui(wrong_port_file, tcp_port):
    """Check port widget value.

    When port is written manually in the config file but with a wrong value, it
    should auto fix in the correct range inside the widget.
    """
    assert port_range(tcp_port.value())


def test_wrong_port_file(wrong_port_file, tmp_settings_file):
    """Test verify_port_config method.

    When app starts will try to fix any wrong port value.
    """
    AppSettings().validate_port_settings()

    config = configparser.ConfigParser()
    config.read(tmp_settings_file)

    settings_values = config['server']['port']
    assert int(settings_values) == 54321
