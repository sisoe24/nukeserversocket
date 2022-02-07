"""Test sending messages via TCP when app is connected."""
import json
import socket

import pytest


STRING = 'nss test msg'
TEXT = "print('%s'.upper())" % STRING
FILE = 'tmp/path/nss.py'


def _socket_send(data):
    """Create a socket to send data.

    Socket will connect automatically to the localhost and port 54321.

    Args:
        data (str): data to send.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('127.0.0.1', 54321))
    s.sendall(bytearray(data, encoding='utf-8'))
    s.close()


@pytest.fixture(autouse=True)
def auto_start_connection(_start_connection):
    """Auto start connection for each test."""


def test_data_has_json_error(_main_ui, qtbot):
    """Check status log text when data has json error."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert 'Error json deserialization' in _main_ui.log_widgets.status_text

    # Data will have a missing enclosing quote
    _socket_send('{text":"print("hello")"}')
    qtbot.waitUntil(check_status)


@pytest.mark.parametrize('data', [' ', '{"name": true}', '{"text":""}'],
                         ids=['no data', 'wrong key', 'empty data'])
def test_data_is_invalid(data, qtbot, _main_ui):
    """Check if status log has right text."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert 'Error. Invalid data:' in _main_ui.log_widgets.status_text

    _socket_send(data)
    qtbot.waitUntil(check_status)


@pytest.fixture()
def _send_test_msg(_main_ui):
    """Send a test message from TestClient."""
    test_client = _main_ui.send_test()
    yield
    test_client._disconnect()


def test_tester_message_status(qtbot, _send_test_msg, _main_ui):
    """Send a test message and check status log text."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert 'Connection successful' in _main_ui.log_widgets.status_text

    qtbot.waitUntil(check_status)


def test_tester_message_received(qtbot, _send_test_msg, _main_ui):
    """Send a test message and check received log text."""
    def check_status():
        """Wait for the status to register the transfer."""
        msg = "Hello from Test Client"
        assert msg in _main_ui.log_widgets.received_text

    qtbot.waitUntil(check_status)


def test_tester_message_output(qtbot, _send_test_msg, _main_ui):
    """Send a test message and check output log text."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert "Hello from Test Client" in _main_ui.log_widgets.output_text

    qtbot.waitUntil(check_status)


@pytest.fixture(params=[TEXT, json.dumps({"text": TEXT, "file": FILE})],
                ids=['simple string', 'stringified array'])
def _send_data(request):
    """Send valid data via socket connection.

    Data sent will be a simple string and a stringified array.
    """
    _socket_send(request.param)


def test_message_status(_send_data, qtbot, _main_ui):
    """Check if status log has right text."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert 'Message received' in _main_ui.log_widgets.status_text

    qtbot.waitUntil(check_status)


def test_message_received(_send_data, qtbot, _main_ui):
    """Check if received log has right text."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert TEXT in _main_ui.log_widgets.received_text

    qtbot.waitUntil(check_status)


def test_message_output(_send_data, qtbot, _main_ui):
    """Check if output log has right text."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert STRING.upper() in _main_ui.log_widgets.output_text

    qtbot.waitUntil(check_status)
