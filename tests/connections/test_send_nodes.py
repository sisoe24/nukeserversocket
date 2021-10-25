"""Test sending nodes module."""
import os
import logging
import configparser

from shutil import rmtree

import pytest

from src.connection import SendNodesClient
from src.main import init_settings


LOGGER = logging.getLogger('NukeServerSocket.main')

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
def _delete_tmp_folder(package):
    """Delete the tmp folder if it already exist."""
    tmp_folder = os.path.join(package, 'src', '.tmp')
    rmtree(tmp_folder, ignore_errors=True)


@pytest.fixture()
def _transfer_node_file(tmp_settings_file):
    """Initialize the tmp directory.

    Yields:
        str: path to the transfer_node.tmp file
    """
    init_settings()

    config = configparser.ConfigParser()
    config.read(tmp_settings_file)

    path = config['path']['transfer_file']

    yield path


def test_transfer_dir_exists(_transfer_node_file):
    """Check if tmp dir for transfer node file got created."""
    assert os.path.exists(os.path.dirname(_transfer_node_file))


def test_send_was_successful(_main_ui, qtbot, _start_server):
    """Check if nodes were sent with success.

    This will only work if there is another instance connected that listens for
    incoming nodes.
    """
    nodes_client = _main_ui._send_nodes()

    def check_status():
        """Wait for the status to register the transfer."""
        log = _main_ui.log_widgets.status_text
        print("➡ log :", log)
        assert 'Connection successful {}:{}'.format('127.0.0.1', 54321) in log

    qtbot.waitUntil(check_status, timeout=10000)
    nodes_client._disconnect()


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
    nodes_client = _main_ui._send_nodes()
    yield nodes_client
    nodes_client._disconnect()


def test_send_was_not_successful(qtbot, _main_ui,  _nodes_client):
    """Emit connection timeout."""
    _nodes_client._connection_timeout()

    def check_status():
        """Wait for the status to register the transfer"""
        assert 'Connection timeout.' in _main_ui.log_widgets.status_text

    qtbot.waitUntil(check_status, timeout=10000)


def test_send_was_error(qtbot, _main_ui, _nodes_client):
    """Emit connection error."""
    _nodes_client.on_error('test error')

    def check_status():
        """Wait for the status to register the transfer"""
        assert 'Error: ' in _main_ui.log_widgets.status_text

    qtbot.waitUntil(check_status, timeout=10000)
