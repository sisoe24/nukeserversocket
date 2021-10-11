
import json
import socket

import pytest

from src.connection import SendNodesClient, SendTestClient
from src.connection.nss_client import NetworkAddresses


# TODO: should connect to a different port in case the usual port is already busy
# TODO: need second instance to test if already connected

STRING = 'nss test msg'
TEXT = "print('%s'.upper())" % STRING
FILE = 'tmp/path/nss.py'


@pytest.fixture(params=[TEXT, json.dumps({"text": TEXT, "file": FILE})])
def send_data(request):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    s.connect(('127.0.0.1', 54321))
    s.sendall(bytearray(request.param, encoding='utf-8'))
    s.close()


@pytest.mark.usefixtures('start_connection', 'send_data')
class TestConnectedLogs:

    def test_message_status(self, qtbot, ui):
        def check_status():
            assert 'Message received' in ui.log_widgets.status_text

        qtbot.waitUntil(check_status)

    def test_message_received(self, qtbot, ui):
        def check_status():
            assert TEXT in ui.log_widgets.received_text

        qtbot.waitUntil(check_status)

    def test_message_output(self, qtbot, ui):
        def check_status():
            assert STRING.upper() in ui.log_widgets.output_text

        qtbot.waitUntil(check_status)


@pytest.mark.usefixtures('start_connection')
class TestSendTestMsg:

    def test_message_status(self, qtbot, ui):
        ui._send_test()

        def check_status():
            assert 'Connection successful' in ui.log_widgets.status_text

        qtbot.waitUntil(check_status)

    # # @pytest.mark.skip()
    def test_message_received(self, qtbot, ui):
        ui._send_test()

        def check_status():
            msg = "from __future__ import print_function; print('Hello from Test Client'"
            assert msg in ui.log_widgets.received_text

        qtbot.waitUntil(check_status)

    def test_message_output(self, qtbot, ui):
        ui._send_test()

        def check_status():
            msg = "Hello from Test Client"
            assert msg in ui.log_widgets.output_text

        qtbot.waitUntil(check_status)
