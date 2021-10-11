
import os
import configparser
from shutil import rmtree

from textwrap import dedent

import pytest

from src.connection import SendNodesClient
from src.main import MainWindow, MainWindowWidget, init_settings
from src.widgets import ConnectionsWidget

from tests.run_app import MyApplication


@pytest.fixture(scope='module')
def init_tmp(package):
    tmp_folder = os.path.join(package, 'src', '.tmp')
    rmtree(tmp_folder)
    yield


@pytest.fixture()
def transfer_node_file(init_tmp, tmp_settings_file):
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


def test_transfer_file_exists(ui, transfer_node_file):
    """Check if transfer_nodes.tmp file gets created."""

    widget = ui.connections
    widget.sender_mode.toggle()

    ui._send_nodes()

    assert os.path.exists(transfer_node_file)


def test_transfer_file_is_valid(transfer_node_file):
    """Check if file got copied correctly."""
    _transfer_nodes = dedent("""
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
    """).strip()
    with open(transfer_node_file) as f:
        assert _transfer_nodes == f.read()


# TODO: need to create second instance

@pytest.mark.skip(reason='need second instace')
def test_send_was_successful(ui, qtbot):
    """Check if nodes were sent with success.

    This will only work if there is another instance connected.
    """
    widget = ui.connections
    widget.sender_mode.toggle()

    widget.server_port.setValue(54322)
    widget.ip_entry.setText('192.168.1.34')

    ui._send_nodes()

    def check_status():
        """Wait for the status to register the transfer"""
        log = ui.log_widgets.status_widget.text_box
        assert 'Connection successful' in log.toPlainText()

    qtbot.waitUntil(check_status)
