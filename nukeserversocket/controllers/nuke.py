"""Nuke-specific plugin for the NukeServerSocket."""
from __future__ import annotations

import os
import json
import logging
from typing import Optional
from textwrap import dedent

from .._qt import (QWidget, QSplitter, QTextEdit, QPushButton, QApplication,
                   QPlainTextEdit)

from .base import EditorController
from ..main import NukeServerSocket
from ..received_data import ReceivedData

LOGGER = logging.getLogger('nukeserversocket')


class NukeScriptEditor:

    def __init__(self):
        # Keep the parents referenced: PySide invalidates a child found through a
        # temporary parent wrapper once that wrapper is garbage collected (Nuke 17).
        self.script_editor = self.get_script_editor()
        self.splitter = self.script_editor.findChild(QSplitter)
        self.input_editor = self.splitter.findChild(QPlainTextEdit)
        self.output_editor = self.splitter.findChild(QTextEdit)
        self.run_button = self.get_run_button()

    def get_script_editor(self) -> QWidget:
        for widget in QApplication.allWidgets():
            if 'scripteditor.1' in widget.objectName():
                return widget
        raise RuntimeError('Could not find script editor')

    def get_run_button(self) -> QPushButton:
        btn = next(
            (
                button
                for button in self.script_editor.findChildren(QPushButton)
                if button.toolTip().lower().startswith('run the current script')
            ),
            None,
        )
        if not btn:
            # likely will never going to happen
            raise RuntimeError(
                'NukeServerSocket error: Could not find Nuke Script Editor execute button'
            )

        return btn


class NukeController(EditorController):
    def __init__(self, editor: Optional[NukeScriptEditor] = None):
        self._editor = editor

    @property
    def editor(self) -> NukeScriptEditor:
        # Look up lazily: a panel restored at startup can exist before the Script Editor does.
        if self._editor is None:
            self._editor = NukeScriptEditor()
        return self._editor

    def execute(self, data: ReceivedData) -> str:
        try:
            return super().execute(data)
        except RuntimeError:
            # Nuke can rebuild the Script Editor (e.g. on a workspace switch),
            # which deletes the widgets we hold: look them up again once.
            self._editor = None
            return super().execute(data)

    def execute_code(self):
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
        index = output.find('# Result:')
        return output[index + 10:] if index != -1 else output

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
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(NukeController(), parent)


def install_nuke():
    import nukescripts

    nukescripts.panels.registerWidgetAsPanel(
        'nukeserversocket.controllers.nuke.NukeEditor', 'NukeServerSocket',
        'uk.co.thefoundry.NukeServerSocket'
    )
