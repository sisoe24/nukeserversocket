from __future__ import annotations

from typing import Optional

import pytest
from pytestqt.qtbot import QtBot

from nukeserversocket.main import MainView, MainModel, MainController
from nukeserversocket.server import NssServer
from nukeserversocket.settings import _NssSettings
from nukeserversocket.controllers.base import EditorController

from nukeserversocket._qt import (Signal, QObject, QWidget, QTextEdit,
                                  QPlainTextEdit)

Controller = MainController
View = MainView
Model = MainModel

# TODO: Test the timeout

# pytestmark = pytest.mark.quick


class MockEditorController(EditorController):
    def __init__(self):
        self._input_editor = QPlainTextEdit()
        self._output_editor = QTextEdit()

    @property
    def input_editor(self):
        return self._input_editor

    @property
    def output_editor(self):
        return self._output_editor

    def execute_code(self):
        pass


class MockServer(QObject):
    on_data_received = Signal()

    def __init__(self, editor: MockEditorController, parent: Optional[QWidget] = None):
        super().__init__(parent)

    def try_connect(self, port: int) -> bool:
        return True

    def isListening(self) -> bool:
        return False

    def close(self): ...

    def errorString(self) -> str:
        return 'error'


@pytest.fixture()
def model(mock_settings: _NssSettings):
    # auto start would connect behind the tests' back
    mock_settings.set('auto_start', False)
    return Model(mock_settings)


@pytest.fixture()
def view(qtbot: QtBot) -> View:
    view = View()
    qtbot.addWidget(view)
    return view


@pytest.fixture()
def editor() -> MockEditorController:
    return MockEditorController()


@pytest.fixture()
def server(editor: MockEditorController) -> NssServer:
    return MockServer(editor)


@pytest.fixture()
def controller(model: Model, view: View, server: MockServer) -> Controller:
    return Controller(view, model, server)


def test_main_controller_on_connect(controller: Controller, view: View):

    controller._on_connect(True)

    assert view.connect_btn.text() == 'Disconnect'
    assert view.port_input.isEnabled() is False
    assert controller._timer.isActive() is True


def test_main_controller_on_disconnect(controller: Controller, view: View):

    view.connect_btn.click()
    assert view.connect_btn.text() == 'Disconnect'

    controller._on_connect(False)

    assert view.connect_btn.isChecked() is False
    assert view.connect_btn.text() == 'Connect'
    assert view.port_input.isEnabled() is True
    assert controller._timer.isActive() is False


def test_main_controller_on_data_received(controller: Controller):

    assert controller._timer.isActive() is False

    controller._on_data_received()

    assert controller._timer.isActive() is True


def test_main_controller_timeout_disabled(controller: Controller, model: Model):
    model._settings.set('server_timeout', 0)

    controller._on_connect(True)

    assert controller._timer.isActive() is False


def test_main_controller_auto_start(qtbot: QtBot, model: Model, view: View, server: MockServer):
    model._settings.set('auto_start', True)

    controller = Controller(view, model, server)  # keep a reference so its slots stay connected

    qtbot.waitUntil(lambda: controller._timer.isActive())
