
import os
import configparser
from shutil import rmtree

from textwrap import dedent

import pytest

from src.connection.nss_client import QBaseClient
from src.connection import Server, SendTestClient, SendNodesClient

from src.main import MainWindow, MainWindowWidget, init_settings
from src.widgets import ConnectionsWidget

from tests.run_app import MyApplication

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


@pytest.fixture(scope='module', autouse=True)
def init_tmp(package):
    tmp_folder = os.path.join(package, 'src', '.tmp')
    rmtree(tmp_folder)
    yield


@pytest.fixture()
def transfer_node_file(tmp_settings_file):
    """Initialize the tmp directory.

    If transfer_nodes.tmp file exists then it will be deleted.

    Yields:
        str: path to the transfer_node.tmp file
    """
    init_settings()

    config = configparser.ConfigParser()
    config.read(tmp_settings_file)

    path = config['path']['transfer_file']

    yield path


def test_transfer_dir_exists(transfer_node_file):
    """Check if tmp dir for transfer node file got created."""
    assert os.path.exists(os.path.dirname(transfer_node_file))


@pytest.mark.skip
def test_send_was_successful_no_settings():
    """Check if nodes were sent with success."""


def test_send_was_successful(ui, qtbot):
    """Check if nodes were sent with success.

    This will only work if there is another instance connected.
    """
    s = Server()
    s.start_server()

    widget = ui.connections
    widget.sender_mode.toggle()

    port = 54321
    hostname = '192.168.1.34'

    widget.server_port.setValue(port)
    widget.ip_entry.setText('')
    widget.ip_entry.setText(hostname)

    ui._send_nodes()

    def check_status():
        """Wait for the status to register the transfer"""
        log = ui.log_widgets.status_widget.text_box
        assert 'Connection successful {}:{}'.format(
            hostname, port) in log.toPlainText()

    qtbot.waitUntil(check_status)
    s.close_server()


def test_received_was_successful(ui, qtbot):
    """Check if nodes were received with success."""

    ui.toggle_connection(True)

    s = SendNodesClient()
    s.connect_to_host()

    def check_status():
        """Wait for the status to register the transfer"""
        assert 'Message received.' in ui.log_widgets.status_text
        assert 'Nodes received.' in ui.log_widgets.output_text
        assert TRANSFER_NODES_FILE in ui.log_widgets.received_text

    qtbot.waitUntil(check_status)


def test_transfer_file_is_valid(transfer_node_file):
    """Check if file got copied correctly."""

    with open(transfer_node_file) as f:
        assert TRANSFER_NODES_FILE == f.read()


@pytest.mark.skip
def test_send_was_not_successful():
    pass
