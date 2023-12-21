"""Local application for NukeServerSocket.

Only used for testing purposes.

"""
from __future__ import annotations

import sys

from PySide2.QtWidgets import (QLabel, QTextEdit, QPushButton, QVBoxLayout,
                               QApplication, QPlainTextEdit)

from ..main import NukeServerSocket
from ..editor_controller import EditorController


class LocalController(EditorController):

    @property
    def input_editor(self) -> QPlainTextEdit:
        return QPlainTextEdit()

    @property
    def output_editor(self) -> QTextEdit:
        return QTextEdit()

    def execute(self) -> None: ...


class LocalEditor(NukeServerSocket):
    def __init__(self):
        super().__init__(LocalController())

        # TODO: Implement a fake script editor.

        run_button = QPushButton('Run')
        run_button.clicked.connect(self.editor.execute)

        # main_layout = self.view.layout()
        # main_layout.addWidget(QLabel('<h3>Local Editor</h3>'))
        # main_layout.addWidget(self.editor.input_editor)
        # main_layout.addWidget(self.editor.output_editor)
        # main_layout.addWidget(run_button)


def main():
    """Main function for NukeServerSocket."""

    app = QApplication(sys.argv)
    window = LocalEditor()
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
