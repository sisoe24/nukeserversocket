"""Test connection when is a websocket."""
import pytest


@pytest.fixture(autouse=True)
def _start_connection(_main_ui_websocket):
    """Click the connect button of the UI and enter in the connected state."""
    _main_ui_websocket.connect_btn.setChecked(True)
    yield
    _main_ui_websocket.connect_btn.setChecked(False)


@pytest.fixture()
def _send_test_msg_web(_main_ui_websocket):
    """Send a test message from TestClient."""
    test_client = _main_ui_websocket.send_test()
    yield test_client
    test_client._disconnect()


def test_tester_message_status_websocket(qtbot, _send_test_msg_web, _main_ui_websocket):
    """Send a test message and check status log text."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert 'Connection successful' in _main_ui_websocket.log_widgets.status_text

    qtbot.waitUntil(check_status)


def test_tester_message_received_websocket(qtbot, _send_test_msg_web, _main_ui_websocket):
    """Send a test message and check received log text."""
    def check_status():
        """Wait for the status to register the transfer."""
        msg = 'Hello from Test _WebSocket Client'
        assert msg in _main_ui_websocket.log_widgets.received_text

    qtbot.waitUntil(check_status, timeout=10000)


def test_tester_message_output_websocket(qtbot, _send_test_msg_web, _main_ui_websocket):
    """Send a test message and check output log text."""
    def check_status():
        """Wait for the status to register the transfer."""
        assert 'Hello from Test _WebSocket Client' in _main_ui_websocket.log_widgets.output_text
    qtbot.waitUntil(check_status)
