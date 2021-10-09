import configparser

import pytest

from src.connection import Server, nss_client
from src.widgets import LogWidgets

from src.widgets.connections_widget import TcpPort

from src.utils import AppSettings


def port_range(value):
    """Return True if port is in expected range."""
    return 49512 <= value <= 65535


def test_default_value_server(startup_no_settings):
    """Test port default value if no settings.ini is found"""
    server_port = Server(LogWidgets()).tcp_port
    assert server_port == 54321


def test_default_value_client(startup_no_settings):
    """Test port default value if no settings.ini is found"""
    server_port = nss_client.NetworkAddresses().port
    assert server_port == 54321


@pytest.fixture()
def wrong_port_ui(startup_no_settings):
    """Change port to a different value."""
    TcpPort().setValue(99999)


def test_port_new_value_ui(wrong_port_ui):
    """Check if port widget is still correct when user tries to enter a wrong value"""
    assert port_range(TcpPort().value())


def test_port_new_value_file(wrong_port_ui, tmp_settings_file):
    """Test if port change is saved into config file"""

    config = configparser.ConfigParser()
    config.read(tmp_settings_file)

    settings_values = config['server']['port']
    assert int(settings_values) == TcpPort().value()


@pytest.fixture()
def wrong_port_file(startup_no_settings, tmp_settings_file):
    """Write a bad port settings into settings.ini file."""
    config = configparser.ConfigParser()
    config['server'] = {'port': '11111'}

    with open(tmp_settings_file, 'w') as configfile:
        config.write(configfile)


def test_wrong_port_ui(wrong_port_file):
    """Check if port widget is still correct when settings.ini has a wrong value"""
    assert port_range(TcpPort().value())


def test_wrong_port_file(wrong_port_file, tmp_settings_file):
    """Check if verify_port_config works when settings.ini has a wrong value"""
    AppSettings().validate_port_settings()

    config = configparser.ConfigParser()
    config.read(tmp_settings_file)

    settings_values = config['server']['port']
    assert int(settings_values) == 54321
