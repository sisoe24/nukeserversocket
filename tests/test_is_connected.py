
import json
import socket

import pytest


STRING = 'nss test msg'
TEXT = "print('%s'.upper())" % STRING
FILE = 'tmp/path/nss.py'


@pytest.fixture(params=[TEXT, json.dumps({"text": TEXT, "file": FILE})])
def send_data(request):
    """Simple client to send data via TCP."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.connect(('127.0.0.1', 54321))
    s.sendall(bytearray(request.param, encoding='utf-8'))
    s.close()


@pytest.mark.usefixtures('start_connection', 'send_data')
class TestConnectionSuccessfulLogs:
    """When connection is successful, check for various log widget text returns"""

    def test_message_status(self, qtbot, ui):
        """Check if status log has right text."""
        def check_status():
            assert 'Message received' in ui.log_widgets.status_text

        qtbot.waitUntil(check_status)

    def test_message_received(self, qtbot, ui):
        """Check if received log has right text."""
        def check_status():
            assert TEXT in ui.log_widgets.received_text

        qtbot.waitUntil(check_status)

    def test_message_output(self, qtbot, ui):
        """Check if output log has right text."""
        def check_status():
            assert STRING.upper() in ui.log_widgets.output_text

        qtbot.waitUntil(check_status)


@pytest.mark.usefixtures('start_connection')
class TestSendTestMsg:
    """Send Test message from ui and check if log widgets text are correct."""

    def test_message_status(self, qtbot, ui):
        """Check if status log has right text."""
        ui._send_test()

        def check_status():
            assert 'Connection successful' in ui.log_widgets.status_text

        qtbot.waitUntil(check_status)

    def test_message_received(self, qtbot, ui):
        """Check if received log has right text."""
        ui._send_test()

        def check_status():
            msg = "from __future__ import print_function; print('Hello from Test Client'"
            assert msg in ui.log_widgets.received_text

        qtbot.waitUntil(check_status)

    def test_message_output(self, qtbot, ui):
        """Check if output log has right text."""
        ui._send_test()

        def check_status():
            msg = "Hello from Test Client"
            assert msg in ui.log_widgets.output_text

        qtbot.waitUntil(check_status)
