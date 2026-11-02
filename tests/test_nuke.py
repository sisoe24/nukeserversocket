from __future__ import annotations

import json
from textwrap import dedent

import pytest
from pytestqt.qtbot import QtBot

from nukeserversocket.settings import _NssSettings
from nukeserversocket.controllers import nuke as nuke_controller
from nukeserversocket.received_data import ReceivedData
from nukeserversocket.controllers.nuke import NukeController, NukeScriptEditor

from nukeserversocket._qt import QTextEdit, QPushButton, QPlainTextEdit


class MockNukeEditor(NukeScriptEditor):
    def __init__(self):
        self.input_editor = QPlainTextEdit()
        self.output_editor = QTextEdit()
        self.run_button = QPushButton()
        self.run_button.clicked.connect(self._eval_input)

    def _eval_input(self):
        # we dont eval any code since we dont really care
        r = self.input_editor.toPlainText()
        self.output_editor.setPlainText(f"# Result: {r}")


def test_nuke_python(qtbot: QtBot, mock_settings: _NssSettings):
    d = json.dumps({'file': 'test.py', 'text': 'print("hello world")'})
    data = ReceivedData(d)
    editor = NukeController(MockNukeEditor())
    editor.settings = mock_settings
    editor.settings.set('mirror_script_editor', True)

    out = editor.execute(data)

    assert editor.editor.input_editor.toPlainText() == 'print("hello world")'
    assert 'hello world' in out


@pytest.mark.parametrize('file, text', (
    ('test.cpp', 'blinkscript'),
    ('test.blink', 'blinkscript'),
))
def test_nuke_blinkscript(qtbot: QtBot, mock_settings: _NssSettings, file: str, text: str):
    d = json.dumps({'file': file, 'text': text})
    data = ReceivedData(d)

    editor = NukeController(MockNukeEditor())
    editor.settings = mock_settings
    editor.settings.set('mirror_script_editor', True)

    editor.execute(data)

    assert editor.editor.input_editor.toPlainText() == dedent(f"""
    node = nuke.toNode("test") or nuke.createNode('BlinkScript', 'name test')
    knobs = node.knobs()
    knobs['kernelSourceFile'].setValue('{file}')
    knobs['kernelSource'].setText("{text}")
    knobs['recompile'].execute()
    """).strip()


@pytest.mark.parametrize('output, expected', (
    ('# Result: hello world', 'hello world'),
    ('hello world', 'hello world'),
))
def test_nuke_get_output(qtbot: QtBot, output: str, expected: str):
    editor = NukeController(MockNukeEditor())
    editor.output_editor.setPlainText(output)

    assert editor.get_output() == expected


class StaleNukeEditor:
    """Stands in for a Script Editor whose widgets Nuke has deleted."""

    @property
    def input_editor(self):
        raise RuntimeError('Internal C++ object already deleted.')


def test_nuke_execute_looks_up_rebuilt_script_editor(
    qtbot: QtBot, mock_settings: _NssSettings, monkeypatch: pytest.MonkeyPatch
):
    monkeypatch.setattr(nuke_controller, 'NukeScriptEditor', MockNukeEditor)

    editor = NukeController(StaleNukeEditor())
    editor.settings = mock_settings
    editor.settings.set('mirror_script_editor', True)

    out = editor.execute(ReceivedData(json.dumps({'text': 'print("hello")'})))

    assert isinstance(editor.editor, MockNukeEditor)
    assert 'hello' in out
