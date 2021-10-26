"""Test sending nodes module."""
import os
import configparser

from shutil import rmtree

import pytest

from src.main import init_settings
from src.connection import SendNodesClient


TRANSFER_NODES_FILE = """
set cut_paste_input [stack 0]
version 13.0 v1
push $cut_paste_input
Blur {
size {{curve x-16 100 x25 1.8 x101 100}}
name Blur1
selected true
xpos -150
ypos -277
}
Blur {
inputs 0
name Blur2
selected true
xpos -40
ypos -301
}
""".strip()

pytestmark = pytest.mark.connection


@pytest.fixture(scope='session', autouse=True)
def _delete_tmp_folder(_package):
    """Delete the tmp folder if it already exist."""
    tmp_folder = os.path.join(_package, 'src', '.tmp')
    rmtree(tmp_folder, ignore_errors=True)


@pytest.fixture()
def _transfer_node_file(_tmp_settings_file):
    """Initialize the tmp directory.

    Yields:
        str: path to the transfer_node.tmp file
    """
    init_settings()

    config = configparser.ConfigParser()
    config.read(_tmp_settings_file)

    path = config['path']['transfer_file']

    yield path


def test_transfer_dir_exists(_transfer_node_file):
    """Check if tmp dir for transfer node file got created."""
    assert os.path.exists(os.path.dirname(_transfer_node_file))


def test_received_was_successful(_main_ui, qtbot):
    """Check if nodes were received with success."""
    _main_ui.toggle_connection(True)

    client = SendNodesClient()
    client.connect_to_host()

    def check_status():
        """Wait for the status to register the transfer."""
        assert 'Message received.' in _main_ui.log_widgets.status_text
        assert 'Nodes received.' in _main_ui.log_widgets.output_text
        assert TRANSFER_NODES_FILE in _main_ui.log_widgets.received_text

    qtbot.waitUntil(check_status, timeout=10000)
    _main_ui._server.close_server()


@pytest.fixture()
def _nodes_client(_main_ui):
    """Send nodes from the SendNodesClient."""
    nodes_client = _main_ui._send_nodes()
    yield nodes_client
    nodes_client._disconnect()


def test_send_was_successful(qtbot, _start_server, _check_log_widget, _nodes_client):
    """Check if nodes were sent with success.

    This will only work if there is another instance connected that listens for
    incoming nodes.
    """
    msg = 'Connection successful {}:{}'.format('127.0.0.1', 54321)
    qtbot.waitUntil(lambda: _check_log_widget('status', msg))


def test_send_was_not_successful(qtbot, _check_log_widget,  _nodes_client):
    """Emit connection timeout."""
    _nodes_client._connection_timeout()
    qtbot.waitUntil(lambda: _check_log_widget('status', 'Connection timeout.'))


def test_send_was_error(qtbot, _main_ui, _nodes_client, _check_log_widget):
    """Emit connection error."""
    _nodes_client.on_error('test error')
    qtbot.waitUntil(lambda: _check_log_widget('status', 'Error:'))
