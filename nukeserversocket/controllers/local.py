"""Local application for NukeServerSocket.

Only used for testing purposes.

"""
from __future__ import annotations

import sys
import json
import traceback

from PySide2.QtWidgets import (QLabel, QWidget, QTextEdit, QHBoxLayout,
                               QPushButton, QSizePolicy, QVBoxLayout,
                               QApplication, QPlainTextEdit)

from .base import EditorController
from ..main import NukeServerSocket
from ..utils import stdoutIO
from ..received_data import ReceivedData


class LocalController(EditorController):
    def __init__(self):
        super().__init__()
        self._input_editor = QPlainTextEdit()
        self._input_editor.setPlaceholderText('Enter your code here...')
        self._input_editor.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        self._input_editor.setPlainText('print("hello world".upper())')

        self._output_editor = QTextEdit()
        self._output_editor.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Maximum)
        self._output_editor.setPlaceholderText('Output will be shown here...')
        self._output_editor.setReadOnly(True)

    @property
    def input_editor(self) -> QPlainTextEdit:
        return self._input_editor

    @property
    def output_editor(self) -> QTextEdit:
        return self._output_editor

    def execute_code(self) -> None:
        with stdoutIO() as s:
            try:
                exec(self.input_editor.toPlainText())
            except Exception:
                result = traceback.format_exc()
            else:
                result = s.getvalue()

            self.output_editor.setPlainText(result)


class LocalEditor(NukeServerSocket):
    def __init__(self):
        super().__init__(LocalController())

        execute_button = QPushButton('Execute')
        execute_button.clicked.connect(self._execute)
        execute_button.setShortcut('Ctrl+R')

        input_layout = QVBoxLayout()
        input_layout.addWidget(QLabel('Input Editor'))
        input_layout.addWidget(self.editor.input_editor)

        output_layout = QVBoxLayout()
        output_layout.addWidget(QLabel('Output Editor'))
        output_layout.addWidget(self.editor.output_editor)

        lower_layout = QHBoxLayout()
        lower_layout.addLayout(input_layout)
        lower_layout.addLayout(output_layout)

        lower_widget = QWidget()
        lower_widget.setLayout(lower_layout)

        main_layout = self.view.layout()
        main_layout.addWidget(QLabel('<h3>Mock Editor</h3>'))
        main_layout.addWidget(execute_button)
        main_layout.addWidget(lower_widget)

        execute_button.click()

    def _execute(self):
        self.editor.execute(ReceivedData(
            json.dumps({'text': self.editor.input_editor.toPlainText()})
        ))


def main():
    """Main function for NukeServerSocket."""

    app = QApplication(sys.argv)
    window = LocalEditor()
    window.setGeometry(100, 100, 800, 600)
    window.show()
    app.exec_()


if __name__ == '__main__':
    main()
