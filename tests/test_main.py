from __future__ import annotations

from typing import Optional

import pytest
from pytestqt.qtbot import QtBot

from nukeserversocket.main import MainView, MainModel, MainController
from nukeserversocket.tools import Tool, ToolSet
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
        self.allow_lan = None
        self.tools_file = None
        self.listening = False
        self.toolset = ToolSet()

    def try_connect(self, port: int, allow_lan: bool = False, tools_file=None) -> bool:
        self.allow_lan = allow_lan
        self.tools_file = tools_file
        return True

    def isListening(self) -> bool:
        return self.listening

    def close(self):
        self.listening = False

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


def _tool(name: str) -> Tool:
    return Tool(name, 'A tool.', {'type': 'object', 'properties': {}}, lambda: None)


@pytest.mark.parametrize('tools_file, toolset, tools, logs', [
    ('', ToolSet(), ['nuke_execute_code'], ['Listening on 127.0.0.1:54321']),
    ('/studio/nss_tools.json', ToolSet(tools={'a': _tool('a')}), ['nuke_execute_code', 'a'],
     ['Listening on 127.0.0.1:54321', 'Tools file /studio/nss_tools.json: 1 tool, code on']),
    ('/studio/nss_tools.json', ToolSet(allow_code=False), [],
     ['Listening on 127.0.0.1:54321', 'Tools file /studio/nss_tools.json: 0 tools, code off']),
    ('/studio/nss_tools.json',
     ToolSet(allow_code=False, tools={'a': _tool('a'), 'b': _tool('b')}, skipped={'c': 'x'}),
     ['a', 'b', 'c'],
     ['Listening on 127.0.0.1:54321',
      'Tools file /studio/nss_tools.json: 2 tools, 1 skipped, code off']),
])
def test_main_controller_shows_mcp_tools_on_connect(
        controller: Controller, model: Model, view: View, server: MockServer, monkeypatch,
        tools_file, toolset, tools, logs):
    monkeypatch.delenv('NSS_TOOLS', raising=False)
    model._settings.set('tools_file', tools_file)
    server.toolset = toolset
    logged = []
    monkeypatch.setattr('nukeserversocket.main.LOGGER.info', lambda msg, *a: logged.append(msg % a))
    assert view.tools_list.count() == 0

    controller._on_connect(True)

    assert server.tools_file == tools_file
    items = [view.tools_list.item(i) for i in range(view.tools_list.count())]
    assert [item.text() for item in items] == tools
    assert [item.toolTip() for item in items if not item.flags()] == [
        f'Skipped: {r}' for r in toolset.skipped.values()]
    assert logged == logs


def test_main_controller_prefers_nss_tools_over_settings(
        controller: Controller, model: Model, server: MockServer, monkeypatch):
    monkeypatch.setenv('NSS_TOOLS', '/studio/env_tools.json')
    model._settings.set('tools_file', '/home/me/my_tools.json')
    logged = []
    monkeypatch.setattr('nukeserversocket.main.LOGGER.info', lambda msg, *a: logged.append(msg % a))

    controller._on_connect(True)

    assert server.tools_file == '/studio/env_tools.json'
    assert logged[1] == 'Tools file /studio/env_tools.json (NSS_TOOLS): 0 tools, code on'


def test_main_controller_logs_why_it_stopped(
        controller: Controller, server: MockServer, monkeypatch):
    logged = []
    monkeypatch.setattr('nukeserversocket.main.LOGGER.info', lambda msg, *a: logged.append(msg % a))
    server.listening = True

    controller._on_timeout()

    assert logged == ['Stopped listening: no request for 60 min (Server Timeout)']


def test_main_controller_on_disconnect(controller: Controller, view: View):

    view.connect_btn.click()
    assert view.connect_btn.text() == 'Disconnect'
    assert view.tools_list.count() == 1

    controller._on_connect(False)

    assert view.connect_btn.isChecked() is False
    assert view.connect_btn.text() == 'Connect'
    assert view.tools_list.count() == 0
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


def test_main_controller_stays_local_by_default(controller: Controller, view: View, server: MockServer):
    controller._on_connect(True)

    assert server.allow_lan is False
    assert view.ip_label.text() == '127.0.0.1'


def test_main_controller_allow_lan(controller: Controller, model: Model, view: View, server: MockServer):
    model._settings.set('allow_lan', True)

    controller._on_connect(True)

    assert server.allow_lan is True
    assert view.ip_label.text() == model.get_ip()


def test_main_controller_auto_start(qtbot: QtBot, model: Model, view: View, server: MockServer):
    model._settings.set('auto_start', True)

    controller = Controller(view, model, server)  # keep a reference so its slots stay connected

    qtbot.waitUntil(lambda: controller._timer.isActive())
