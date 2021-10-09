
from multiprocessing import Queue, Process
import os
import configparser
from textwrap import dedent

import pytest

from src.main import MainWindow, MainWindowWidget
from src.widgets import ConnectionsWidget
from tests.run_app import MyApplication


@pytest.fixture()
def transfer_node_file(startup_no_settings, tmp_settings_file):
    """Initialize the tmp directory creating and get the file path from settings."""
    MainWindowWidget()

    config = configparser.ConfigParser()
    config.read(tmp_settings_file)

    yield config['path']['transfer_file']


def test_transfer_dir_exists(transfer_node_file):
    """Check if tmp dir for transfer node file got created."""
    assert os.path.exists(os.path.dirname(transfer_node_file))


def test_transfer_file_exists(transfer_node_file):
    """Check if file got created."""
    widget = ConnectionsWidget()
    widget.sender_mode.toggle()
    MainWindowWidget()._send_nodes()
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


def test_send_was_successful(myapp):
    widget = ConnectionsWidget()

    widget.server_port.setValue(54322)
    widget.ip_entry.setText('192.168.1.34')
    widget.sender_mode.toggle()

    main = MainWindowWidget()
    main._send_nodes()

    log = main.log_widgets

    assert 'Nodes copied' in log.output_text.text_box.toPlainText()
