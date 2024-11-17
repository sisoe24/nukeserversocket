from __future__ import annotations

import json
from typing import Any
from textwrap import dedent

import pytest
from pytestqt.qtbot import QtBot
from PySide2.QtWidgets import QTextEdit, QPushButton, QPlainTextEdit

from nukeserversocket.settings import _NssSettings
from nukeserversocket.utils.stdout import stdoutIO
from nukeserversocket.received_data import ReceivedData
from nukeserversocket.controllers.nuke import NukeController, NukeScriptEditor


class MockNukeEditor(NukeScriptEditor):
    def __init__(self):
        self.input_editor = QPlainTextEdit()
        self.output_editor = QTextEdit()
        self.run_button = QPushButton()
        self.run_button.clicked.connect(self._eval_input)

    def _eval_input(self):
        # we are eval any code since we dont really care
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
