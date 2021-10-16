import os

import pytest

from src.utils import settings
from src.script_editor import nuke_se
from src.script_editor.nuke_se import editors_widgets

from tests.run_local import MyApplication, _MainWindow, _MainWindowWidget


def pytest_addoption(parser):
    parser.addoption(
        '--checklinks', action='store_true', default=False, help='Validate web link'
    )


def pytest_configure(config):
    config.addinivalue_line('markers', 'web: validate web link')
    config.addinivalue_line('markers', 'quicktest: quick test methods')


def pytest_collection_modifyitems(config, items):
    if config.getoption('--checklinks'):
        return

    skip_check = pytest.mark.skip(reason='need --checklink option to run')

    for item in items:
        if "web" in item.keywords:
            item.add_marker(skip_check)


@pytest.fixture(scope='session')
def package():
    """Package directory path"""
    current_dir = os.path.dirname(__file__)
    package_dir = os.path.abspath(os.path.dirname(current_dir))
    yield package_dir


@pytest.fixture(scope='session')
def tmp_settings_file(package):
    """Temporary settings file path"""
    tmp_dir = os.path.join(package, 'tests', 'tmp')

    os.makedirs(tmp_dir, exist_ok=True)

    file = os.path.join(tmp_dir, 'fake_ini.ini')

    with open(file, 'w') as _:
        pass

    yield file

    # os.remove(file)


@pytest.fixture(autouse=True)
def patch_settings(tmp_settings_file, monkeypatch):
    """Patch CONFIG_FILE path with new fake settings file."""
    monkeypatch.setattr(settings, 'CONFIG_FILE', tmp_settings_file)
    monkeypatch.setattr(nuke_se, 'editors_widgets', {})


@pytest.fixture()
def ui(qtbot):
    """Main UI Widget"""
    widget = _MainWindowWidget()
    qtbot.addWidget(widget)
    # widget.show()
    yield widget.main_app


@pytest.fixture()
def start_connection(ui):
    """Click the connect button of the UI and enter in the connected state."""
    # TODO: probably should be inside test_connections.py
    ui.connect_btn.setChecked(True)
    yield
    ui.connect_btn.setChecked(False)


@pytest.fixture()
def activate_sender_mode(ui):
    """Click the connect button of the UI and enter in the connected state."""
    # TODO: probably should be inside test_connections.py
    ui.connections.sender_mode.toggle()
    yield
    ui.connections.receiver_mode.toggle()
