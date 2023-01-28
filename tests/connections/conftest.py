"""Configuration file for the connection tests."""

import pytest

from src.network.nss_server import QServer


@pytest.fixture()
def _start_server():
    """Start server connection."""
    server = QServer()
    server.start_server()
    yield server
    server.close_server()


@pytest.fixture()
def _start_connection(_main_ui):
    """Click the connect button of the UI and enter in the connected state."""
    _main_ui.connect_btn.setChecked(True)
    yield
    _main_ui.connect_btn.setChecked(False)
