"""Test connection when is a websocket."""
import pytest

from src.network import QServer
from src.settings import AppSettings


@pytest.fixture(autouse=True)
def _start_connection(_main_ui):
    """Click the connect button of the UI and enter in the connected state."""
    AppSettings().setValue('connection_type/websocket', True)

    _main_ui.connect_btn.setChecked(True)
    yield
    _main_ui.connect_btn.setChecked(False)


@pytest.fixture()
def _send_test_msg_web(_main_ui):
    """Send a test message from TestClient."""
    test_client = _main_ui.send_test()
    yield
    test_client._disconnect()


def test_tester_message_status_websocket(qtbot, _send_test_msg_web, _main_ui):
    """Send a test message and check status log text."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert 'Connection successful' in _main_ui.log_widgets.status_text

    qtbot.waitUntil(check_status)


def test_tester_message_received_websocket(qtbot, _send_test_msg_web, _main_ui):
    """Send a test message and check received log text."""
    def check_status():
        """Wait for the status to register the transfer."""
        msg = 'Hello from Test WebSocket Client'
        assert msg in _main_ui.log_widgets.received_text

    qtbot.waitUntil(check_status, timeout=10000)


def test_tester_message_output_websocket(qtbot, _send_test_msg_web, _main_ui):
    """Send a test message and check output log text."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert 'Hello from Test WebSocket Client' in _main_ui.log_widgets.output_text

    qtbot.waitUntil(check_status)
