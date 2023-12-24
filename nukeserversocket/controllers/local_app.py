"""Local application for NukeServerSocket.

Only used for testing purposes.

"""
from __future__ import annotations

import io
import sys
import contextlib

from PySide2.QtWidgets import (QLabel, QTextEdit, QPushButton, QVBoxLayout,
                               QApplication, QPlainTextEdit)

from ..main import NukeServerSocket
from ..editor_controller import EditorController


@contextlib.contextmanager
def _stdoutIO(stdout=None):
    """Get output from sys.stdout after executing code from `exec`.

    https://stackoverflow.com/a/3906390/9392852
    """
    old = sys.stdout
    if stdout is None:
        stdout = io.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old


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
        with _stdoutIO() as s:
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
