from __future__ import annotations

import pytest
from PySide2.QtCore import Signal, QObject
from pytestqt.qtbot import QtBot
from PySide2.QtWidgets import QTextEdit, QPlainTextEdit

from nukeserversocket.main import MainView, MainModel, MainController
from nukeserversocket.server import NssServer
from nukeserversocket.settings import _NssSettings
from nukeserversocket.editor_controller import EditorController

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

    def execute(self):
        pass


class MockServer(QObject):
    on_data_received = Signal()

    def __init__(self, editor: MockEditorController, parent=None):
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

    assert view.port_input.value() == 54321
    assert view.connect_btn.text() == 'Disconnect'
    assert view.port_input.isEnabled() is False
    assert controller._timer.isActive() is True


def test_main_controller_on_disconnect(controller: Controller, view: View):

    controller._on_connect(False)

    assert view.port_input.value() == 54321
    assert view.connect_btn.text() == 'Connect'
    assert view.port_input.isEnabled() is True
    assert controller._timer.isActive() is False


def test_main_controller_on_data_received(controller: Controller):

    assert controller._timer.isActive() is False

    controller._on_data_received()

    assert controller._timer.isActive() is True
