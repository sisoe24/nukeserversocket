"""Configuration file for the connection tests."""

import pytest

from src.connection.nss_server import QServer


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


@pytest.fixture()
def _check_log_widget(_main_ui):
    """Check if log text has message based on connection status."""
    # TODO: not sure if this is more confusing to understand than writing a
    # method to each test that checks the log.

    def _inspect_log(log, msg):
        """Inspect the various log widget text.

        Asserts if msg is inside the log text.

        Args:
            log (str): the name of the log widget to inspect. Valid names are:
            `status`, `received` and `output`.
            msg (str): the message to check inside the log.
        """
        if log == 'status':
            log = _main_ui.log_widgets.status_text
        elif log == 'received':
            log = _main_ui.log_widgets.received_text
        elif log == 'output':
            log = _main_ui.log_widgets.output_text
        else:
            raise ValueError('no log widget for this name: %s' % log)

        assert msg in log

    return _inspect_log
