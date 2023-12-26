"""Nuke-specific plugin for the NukeServerSocket."""
from __future__ import annotations

import os
import json
import logging
from textwrap import dedent
from dataclasses import dataclass

from PySide2.QtWidgets import (QWidget, QSplitter, QTextEdit, QPushButton,
                               QApplication, QPlainTextEdit)

from ..main import NukeServerSocket
from ..utils import cache
from ..received_data import ReceivedData
from ..editor_controller import EditorController

LOGGER = logging.getLogger('nukeserversocket')


@dataclass(init=False)
class Editor:

    input_editor: QPlainTextEdit
    output_editor: QTextEdit
    run_button: QPushButton

    def __init__(self):
        self.input_editor = self.get_input_editor()
        self.output_editor = self.get_output_editor()
        self.run_button = self.get_run_button()

    @cache('nuke')
    def get_script_editor(self) -> QWidget:
        for widget in QApplication.allWidgets():
            if 'scripteditor.1' in widget.objectName():
                return widget
        raise RuntimeError('Could not find script editor')

    @cache('nuke')
    def get_splitter(self) -> QSplitter:
        return self.get_script_editor().findChild(QSplitter)

    @cache('nuke')
    def get_input_editor(self) -> QPlainTextEdit:
        return self.get_splitter().findChild(QPlainTextEdit)

    @cache('nuke')
    def get_output_editor(self) -> QTextEdit:
        return self.get_splitter().findChild(QTextEdit)

    @cache('nuke')
    def get_run_button(self) -> QPushButton:
        return next(
            (
                button
                for button in self.get_script_editor().findChildren(QPushButton)
                if button.toolTip().lower().startswith('run the current script')
            ),
            None,
        )


class NukeController(EditorController):
    def __init__(self, editor: Editor):
        self.editor = editor

    def execute(self):
        self.editor.run_button.click()

    @property
    def input_editor(self) -> QPlainTextEdit:
        return self.editor.input_editor

    @property
    def output_editor(self) -> QTextEdit:
        return self.editor.output_editor

    def get_output(self) -> str:
        """Override the base method to remove the '# Result:' prefix."""
        output = self.editor.output_editor.toPlainText()
        return output[output.find('# Result:')+10:]

    def _blink_wrapper(self, data: ReceivedData) -> str:
        return dedent("""
            node = nuke.toNode("{filename}") or nuke.createNode('BlinkScript', 'name {filename}')
            knobs = node.knobs()
            knobs['kernelSourceFile'].setValue('{file}')
            knobs['kernelSource'].setText({text})
            knobs['recompile'].execute()
            """).format(
            filename=os.path.splitext(os.path.basename(data.file))[0],
            file=data.file,
            text=json.dumps(data.text)
        ).strip()

    def set_input(self, data: ReceivedData) -> None:
        """Override the base method."""

        ext = os.path.splitext(data.file)[1]

        text = self._blink_wrapper(data) if ext in ('.blink', '.cpp') else data.text
        self.input_editor.setPlainText(text)


class NukeEditor(NukeServerSocket):
    def __init__(self, parent=None):
        super().__init__(NukeController(Editor()), parent)


def install_nuke():
    import nukescripts

    nukescripts.panels.registerWidgetAsPanel(
        'nukeserversocket.controllers.nuke.NukeEditor', 'NukeServerSocket',
        'uk.co.thefoundry.NukeServerSocket'
    )
