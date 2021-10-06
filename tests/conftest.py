import sys

import pytest
import time
from src.main import MainWindow

from tests.run_app import MyApplication, _MainWindow
from pytestqt.qt_compat import qt_api


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
    yield MyApplication([])


@pytest.fixture(scope='class')
def main_window(myapp: MyApplication) -> MainWindow:
    print('initialize main app')
    window = myapp.window.main_window.main_app
    yield window


@pytest.fixture(scope='class')
def start_connection(main_window: MainWindow):
    print('Start server Connection')
    main_window.connect_btn.click()
    yield
    main_window.connect_btn.click()
    print('End server Connection')


@pytest.fixture(scope='class')
def toggle_receiver_btn(main_window):
    main_window.connect_btn.click()
    main_window.test_btn.click()
    # time.sleep(5)

    yield

    main_window.connect_btn.click()


@pytest.fixture()
def connection_widgets(main_window):
    yield main_window.connections


@pytest.fixture(scope='class')
def activate_sender_mode(main_window):
    main_window.connections.sender_mode.toggle()
    yield
    main_window.connections.receiver_mode.toggle()
