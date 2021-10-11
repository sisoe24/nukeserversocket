import os
import configparser

import pytest

from src.utils import settings
from src.main import MainWindow, MainWindowWidget
from tests.run_app import MyApplication, _MainWindow, _MainwindowWidgets


@pytest.fixture(scope='session')
def tmp_settings_file():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    tmp_dir = os.path.join(current_dir, 'tmp')

    os.makedirs(tmp_dir, exist_ok=True)

    file = os.path.join(tmp_dir, 'fake_ini.ini')

    with open(file, 'w') as _:
        pass

    yield file

    # os.remove(file)


@pytest.fixture(autouse=True, scope='session')
def qapp():
    app = MyApplication([])
    yield app


@pytest.fixture()
def config_file(tmp_settings_file):
    """Return the config file object."""
    config = configparser.ConfigParser()
    config.read(tmp_settings_file)

    yield config


@pytest.fixture(autouse=True)
def patch_settings(tmp_settings_file, monkeypatch):
    """Patch CONFIG_FILE path with new fake settings file."""
    monkeypatch.setattr(settings, 'CONFIG_FILE', tmp_settings_file)


@pytest.fixture()
def ui(qtbot):
    """Main UI Widget"""
    widget = _MainwindowWidgets()
    qtbot.addWidget(widget)
    yield widget.main_app


@pytest.fixture()
def start_connection(ui):
    """Click the connect button of the UI and enter in the connected state."""
    ui.connect_btn.setChecked(True)
    yield
    ui.connect_btn.setChecked(False)


@pytest.fixture()
def activate_sender_mode(ui):
    """Click the connect button of the UI and enter in the connected state."""
    ui.connections.sender_mode.toggle()
    yield
    ui.connections.receiver_mode.toggle()
