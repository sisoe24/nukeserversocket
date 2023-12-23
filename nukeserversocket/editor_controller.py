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


def format_output(data: ReceivedData, result: str) -> str:
    placeholders = {
        '%d': datetime.now().strftime('%H:%M:%S'),
        '%f': data.file,
        '%F': os.path.basename(data.file),
        '%t': result,
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
        # TODO: Limit history size
        cls.history.append(text)

    def _process_output(self, data: ReceivedData, result: str) -> str:
        settings = get_settings()

        if settings.get('format_output'):
            output = format_output(data, result)
            LOGGER.debug('Formatting output: %s', output.replace('\n', '\\n'))
        else:
            output = result

        self._add_to_history(output)

        if settings.get('clear_output'):
            LOGGER.debug('Clearing output.')
            self.output_editor.setPlainText(output)
        else:
            # TODO: Investigate why insertPlainText or appendPlainText
            # does not work as expected
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

        if not get_settings().get('mirror_script_editor'):
            LOGGER.debug('Restoring script editor.')
            self.input_editor.setPlainText(initial_input)
            self.output_editor.setPlainText(initial_output)
            return result

        return self._process_output(data, result)
