from __future__ import annotations

import os
import sys
import pathlib
import contextlib
from typing import TYPE_CHECKING

from PySide2.QtWidgets import (QWidget, QSplitter, QTextEdit, QPushButton,
                               QApplication, QPlainTextEdit)

from .utils import cache
from .controller import Controller, BaseController

if TYPE_CHECKING:
    from .server import ReceivedData


@cache
def get_script_editor() -> QWidget:
    for widget in QApplication.allWidgets():
        if 'scripteditor.1' in widget.objectName():
            return widget
    raise RuntimeError('Could not find script editor')


@cache
def get_splitter() -> QSplitter:
    return get_script_editor().findChild(QSplitter)


@cache
def get_input_editor() -> QPlainTextEdit:
    return get_splitter().findChild(QPlainTextEdit)


@cache
def get_output_editor() -> QTextEdit:
    return get_splitter().findChild(QTextEdit)


@cache
def get_run_button() -> QPushButton:
    # naively assume that the button always exists
    return next(
        (
            button
            for button in get_script_editor().findChildren(QPushButton)
            if button.toolTip().lower().startswith('run the current script')
        ),
        None,
    )


class NukeController(BaseController):
    def __init__(self):
        self._input_editor = get_input_editor()
        self._output_editor = get_output_editor()
        self._run_button = get_run_button()

    def get_input(self):
        return self._input_editor.toPlainText()

    def set_input(self, value: str):
        self._input_editor.setPlainText(value)

    def set_output(self, value: str):
        self._output_editor.setPlainText(value)

    def get_output(self):
        output = self._output_editor.toPlainText()
        f = output.find('# Result:')
        r = output[f+10:]
        self.set_output(r)
        return r

    def execute(self, data: ReceivedData) -> str:
        self.set_input(data.text)
        self._run_button.click()
        return self.get_output()


def install_nuke():
    with contextlib.suppress(ImportError):
        import nukescripts
        Controller.set_instance(NukeController)

        nukescripts.panels.registerWidgetAsPanel(
            'nukeserversocket.refactor.main.NukeServerSocket', 'NukeController',
            # 'nukeserversocket.refactor.install_nuke.NukeController', 'NukeController',
            'uk.co.thefoundry.NukeController'
        )
