
import json
import socket

import pytest

STRING = 'nss test msg'
TEXT = "print('%s'.upper())" % STRING
FILE = 'tmp/path/nss.py'

data = [TEXT, json.dumps({"text": TEXT, "file": FILE})]


@pytest.fixture(params=data)
def send_data(request):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connection host and port must match whats inside Nuke
    # 127.0.0.1 == localhost
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
