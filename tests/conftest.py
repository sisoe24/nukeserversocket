import os
import sys

import pytest
import time
from src.main import MainWindow

from tests.run_app import MyApplication, _MainWindow
from pytestqt.qt_compat import qt_api
from src.utils import settings

# @pytest.fixture()
# def main_app(qtbot):
#     print('init app')

#     widget = _MainWindow()
#     qtbot.addWidget(widget)

#     # widget.show()
#     # qtbot.stop()

#     yield widget.main_window.main_app


@pytest.fixture(scope='session')
def myapp():
    app = MyApplication([])
    yield app


@pytest.fixture(scope='class')
def main_window(myapp: MyApplication) -> MainWindow:
    print('initialize main app')
    window = myapp.window.main_widgets.main_app
    yield window


@pytest.fixture(scope='class')
def start_connection(main_window: MainWindow):
    print('Start server Connection')
    main_window.connect_btn.click()
    yield
    main_window.connect_btn.click()
    print('End server Connection')


@pytest.fixture()
def connection_widgets(main_window):
    yield main_window.connections


@pytest.fixture(scope='class')
def activate_sender_mode(main_window):
    main_window.connections.sender_mode.toggle()
    yield
    main_window.connections.receiver_mode.toggle()


@pytest.fixture(scope='session')
def tmp_settings_file():
    current_dir = os.path.abspath(os.path.dirname(__file__))
    tmp_dir = os.path.join(current_dir, 'tmp')

    os.makedirs(tmp_dir, exist_ok=True)

    file = os.path.join(tmp_dir, 'fake_ini.ini')

    yield file

    # os.remove(file)


@pytest.fixture()
def startup_no_settings(myapp, tmp_settings_file, monkeypatch):
    with open(tmp_settings_file, 'w') as _:
        pass
    monkeypatch.setattr(settings, 'CONFIG_FILE', tmp_settings_file)
    yield tmp_settings_file
