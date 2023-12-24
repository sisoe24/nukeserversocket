from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import List
from datetime import datetime

from PySide2.QtWidgets import QTextEdit, QPlainTextEdit

from .logger import get_logger
from .settings import get_settings
from .received_data import ReceivedData

LOGGER = get_logger()


def format_output(file: str, text: str) -> str:
    placeholders = {
        '%d': datetime.now().strftime('%H:%M:%S'),
        '%f': file,
        '%F': os.path.basename(file),
        '%t': text,
        '%n': '\n'
    }

    output_format = get_settings().get('format_output')
    for key, value in placeholders.items():
        if key in output_format:
            output_format = output_format.replace(key, value)

    return output_format


class EditorController(ABC):
    history: List[str] = []

    @property
    @abstractmethod
    def input_editor(self) -> QPlainTextEdit: ...

    @property
    @abstractmethod
    def output_editor(self) -> QTextEdit: ...

    @abstractmethod
    def execute(self) -> None: ...

    @classmethod
    def _add_to_history(cls, text: str) -> None:
        cls.history.append(text)

    def _process_output(self, data: ReceivedData, result: str) -> str:

        if get_settings().get('format_output'):
            output = format_output(data.file, result)
            LOGGER.debug('Formatting output: %s', output.replace('\n', '\\n'))
        else:
            output = result

        if get_settings().get('clear_output'):
            LOGGER.debug('Clearing output.')
            self.history.clear()
            self.output_editor.setPlainText(output)
        else:
            self._add_to_history(output)
            self.output_editor.setPlainText('\n'.join(self.history) + '\n')

        self.output_editor.verticalScrollBar().setValue(
            self.output_editor.verticalScrollBar().maximum()
        )

        return output

    def get_output(self) -> str:
        return self.output_editor.toPlainText()

    def set_input(self, data: ReceivedData) -> None:
        self.input_editor.setPlainText(data.text)

    def run(self, data: ReceivedData) -> str:

        LOGGER.debug('Running script: %s', data.file)

        initial_input = self.input_editor.toPlainText()
        initial_output = self.output_editor.toPlainText()

        self.set_input(data)
        self.execute()

        result = self.get_output()

        LOGGER.debug('RUN get_settings(): %s', get_settings())

        if not get_settings().get('mirror_script_editor'):
            LOGGER.debug('Restoring script editor.')
            self.input_editor.setPlainText(initial_input)
            self.output_editor.setPlainText(initial_output)
            return result

        return self._process_output(data, result)
