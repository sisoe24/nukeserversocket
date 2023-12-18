"""Local application for NukeServerSocket.

Only used for testing purposes.

"""
from __future__ import annotations

import sys

from PySide2.QtWidgets import QTextEdit, QApplication, QPlainTextEdit

from ..main import NukeServerSocket
from ..editor_controller import EditorController, BaseEditorController

# TODO: Implement a fake script editor.


class LocalController(BaseEditorController):

    @property
    def input_editor(self) -> QPlainTextEdit:
        return QPlainTextEdit()

    @property
    def output_editor(self) -> QTextEdit:
        return QTextEdit()

    def execute(self) -> None: ...


def main():
    """Main function for NukeServerSocket."""

    EditorController.set_instance(LocalController)

    app = QApplication(sys.argv)
    window = NukeServerSocket()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
