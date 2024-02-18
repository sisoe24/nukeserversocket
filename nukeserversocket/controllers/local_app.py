"""Local application for NukeServerSocket.

Only used for testing purposes.

"""
from __future__ import annotations

import sys

from PySide2.QtWidgets import (QLabel, QTextEdit, QPushButton, QApplication,
                               QPlainTextEdit)

from ..main import NukeServerSocket
from ..utils import stdoutIO
from ..editor_controller import EditorController


class LocalController(EditorController):
    def __init__(self):
        super().__init__()
        self._input_editor = QPlainTextEdit()

        self._output_editor = QTextEdit()
        self._output_editor.setReadOnly(True)

    @property
    def input_editor(self) -> QPlainTextEdit:
        return self._input_editor

    @property
    def output_editor(self) -> QTextEdit:
        return self._output_editor

    def execute(self) -> None:
        with stdoutIO() as s:
            exec(self.input_editor.toPlainText())
            result = s.getvalue()
            self.output_editor.setPlainText(result)


class LocalEditor(NukeServerSocket):
    def __init__(self):
        super().__init__(LocalController())

        run_button = QPushButton('Run')
        run_button.clicked.connect(self.editor.execute)
        run_button.setShortcut('Ctrl+R')

        main_layout = self.view.layout()
        main_layout.addWidget(QLabel('<h3>Local Editor</h3>'))
        main_layout.addWidget(self.editor.output_editor)
        main_layout.addWidget(self.editor.input_editor)
        main_layout.addWidget(run_button)


def main():
    """Main function for NukeServerSocket."""

    app = QApplication(sys.argv)
    window = LocalEditor()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
