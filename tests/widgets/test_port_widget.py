"""Test Port Widget module."""
import configparser

import pytest

from src.connection import nss_client
from src.widgets.connections_widget import TcpPort
from src.utils import AppSettings


def _port_in_range(value):
    """Return True if port is in expected range."""
    return 49512 <= value <= 65535


def test_default_value_client():
    """Test port default value if no settings.ini is found."""
    server_port = nss_client.NetworkAddresses().port
    assert server_port == 54321


@pytest.fixture()
def _tcp_port(qtbot):
    """Init the TcpPort widget class."""
    widget = TcpPort()
    qtbot.addWidget(widget)
    yield widget


@pytest.fixture()
def _bad_port_ui_value(_tcp_port):
    """Change port to a wrong value."""
    _tcp_port.setValue(99999)


def test_port_new_value_ui(_tcp_port, _bad_port_ui_value):
    """Check if port auto adjusts the value.

    If user enters a wrong value, should auto adjust into the correct range.
    """
    assert _port_in_range(_tcp_port.value())


@pytest.mark.quicktest
def test_port_new_value_file(_tmp_settings_file, _tcp_port, _bad_port_ui_value):
    """Test if port change is saved into config file."""
    config = configparser.ConfigParser()
    config.read(_tmp_settings_file)

    settings_values = config['server']['port']

    assert int(settings_values) == _tcp_port.value()


@pytest.fixture()
def _bad_port_file_value(_tmp_settings_file):
    """Write a bad port settings into settings.ini file."""
    config = configparser.ConfigParser()
    config['server'] = {'port': '11111'}

    with open(_tmp_settings_file, 'w') as configfile:
        config.write(configfile)


def test_wrong_port_ui(_bad_port_file_value, _tcp_port):
    """Check port widget value.

    When port is written manually in the config file but with a wrong value, it
    should auto adjust in the correct range inside the widget.
    """
    assert _port_in_range(_tcp_port.value())


def test_wrong_port_file(_bad_port_file_value, _tmp_settings_file):
    """Test verify_port_config method.

    When app starts will try to fix any wrong port value.
    """
    AppSettings().validate_port_settings()

    config = configparser.ConfigParser()
    config.read(_tmp_settings_file)

    settings_values = config['server']['port']
    assert int(settings_values) == 54321
