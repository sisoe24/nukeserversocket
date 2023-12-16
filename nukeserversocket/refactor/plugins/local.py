from __future__ import annotations

from typing import TYPE_CHECKING

from PySide2.QtWidgets import (QWidget, QSplitter, QTextEdit, QPushButton,
                               QApplication, QPlainTextEdit)

from nukeserversocket.refactor.received_data import ReceivedData

from ..utils import cache
from ..controller import EditorController, BaseEditorController

if TYPE_CHECKING:
    from ..server import ReceivedData


class LocalController(BaseEditorController):

    @property
    def input_editor(self) -> QPlainTextEdit:
        return QPlainTextEdit()

    @property
    def output_editor(self) -> QTextEdit:
        return QTextEdit()

    def execute(self) -> None: ...
