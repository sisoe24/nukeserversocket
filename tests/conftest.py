"""Pytest configuration file."""
import os

import pytest
from src.connection.nss_server import QServer

from src.utils import settings
from src.script_editor import nuke_se
from src.widgets import FakeScriptEditor
from src.script_editor.nuke_se import editors_widgets

from src.run_local import _MainWindowWidget


def pytest_addoption(parser):
    """Add pytest new options."""
    parser.addoption(
        '--checklinks', action='store_true', default=False, help='Validate web link'
    )


def pytest_configure(config):
    """Add pytest new configurations."""
    config.addinivalue_line(
        'markers', 'connection: test modules that deal with connection')
    config.addinivalue_line('markers', 'web: validate web link')
    config.addinivalue_line('markers', 'quicktest: quick test methods')
    config.addinivalue_line(
        'markers', 'settings_name: test system options name')


def pytest_collection_modifyitems(config, items):
    """Change pytest behavior for certain marks."""
    if config.getoption('--checklinks'):
        return

    skip_check = pytest.mark.skip(reason='need --checklink option to run')

    for item in items:
        if "web" in item.keywords:
            item.add_marker(skip_check)


@pytest.fixture(scope='session')
def _package():
    """Package directory path.

    Method will also create a tmp directory if not already present.

    Yields:
        str: path of the _package root.
    """
    current_dir = os.path.dirname(__file__)
    package_dir = os.path.abspath(os.path.dirname(current_dir))

    tmp_dir = os.path.join(current_dir, 'tmp')
    if not os.path.exists(tmp_dir):
        os.mkdir(tmp_dir)

    yield package_dir


@pytest.fixture()
def _tmp_settings_file(_package):
    """Temporary settings file path. """
    file = os.path.join('tests', 'tmp', 'fake_ini.ini')
    yield file
    # os.remove(file)


@pytest.fixture(autouse=True)
def patch_settings(_tmp_settings_file, monkeypatch):
    """Patch CONFIG_FILE path with new fake settings file."""
    monkeypatch.setattr(settings, 'CONFIG_FILE', _tmp_settings_file)
    yield


@pytest.fixture()
def _main_ui(qtbot):
    """Initialize Main UI Widget."""
    widget = _MainWindowWidget()
    qtbot.addWidget(widget)
    # widget.show()
    yield widget.main_app


@pytest.fixture(autouse=True)
def _clean_settings(_tmp_settings_file):
    """Clean settings file before and after each test."""
    def _clean_file():
        """Clean file."""
        with open(_tmp_settings_file, 'w') as _:
            pass

    _clean_file()
    yield
    _clean_file()
