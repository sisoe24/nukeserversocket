from __future__ import annotations

import json
from textwrap import dedent

import pytest
from PySide2.QtWidgets import QTextEdit, QPushButton, QPlainTextEdit

from nukeserversocket.settings import _NssSettings
from nukeserversocket.received_data import ReceivedData
from nukeserversocket.controllers.nuke import Editor, NukeController

# pytestmark = pytest.mark.quick


class NukeEditor(Editor):
    def __init__(self):
        self.input_editor = QPlainTextEdit()
        self.output_editor = QTextEdit()
        self.run_button = QPushButton()


def test_nuke_python(qtbot, settings):
    data = ReceivedData('{"file": "test.py", "text": "print(\\"hello world\\")"}')
    editor = NukeController(NukeEditor())
    editor.settings = settings
    editor.settings.set('mirror_script_editor', True)

    editor.run(data)

    assert editor.editor.input_editor.toPlainText() == 'print("hello world")'


@pytest.mark.parametrize('file, text', (
    ('test.cpp', 'blinkscript'),
    ('test.blink', 'blinkscript'),
))
def test_nuke_blinkscript(qtbot, settings: _NssSettings, file: str, text: str):
    d = json.dumps({'file': file, 'text': text})
    data = ReceivedData(d)

    editor = NukeController(NukeEditor())
    editor.settings = settings
    editor.settings.set('mirror_script_editor', True)

    editor.run(data)

    assert editor.editor.input_editor.toPlainText() == dedent(f"""
    node = nuke.toNode("test") or nuke.createNode('BlinkScript', 'name test')
    knobs = node.knobs()
    knobs['kernelSourceFile'].setValue('{file}')
    knobs['kernelSource'].setText("{text}")
    knobs['recompile'].execute()
    """).strip()
