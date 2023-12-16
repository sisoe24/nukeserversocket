from __future__ import annotations

import os
from abc import ABC, abstractmethod
from typing import Callable, Optional
from datetime import datetime

from PySide2.QtWidgets import QTextEdit, QPlainTextEdit

from .settings import get_settings
from .received_data import ReceivedData


def format_output(data: ReceivedData, result: str) -> str:
    placeholders = {
        '%d': datetime.now().strftime('%H:%M:%S'),
        '%f': data.file,
        '%F': os.path.basename(data.file),
        '%t': data.text,
    }

    output_format = get_settings().get('format_output')
    for key, value in placeholders.items():
        if key in output_format:
            output_format = output_format.replace(key, value)

    return f'{output_format}\n{result}'


class BaseEditorController(ABC):

    @property
    @abstractmethod
    def input_editor(self) -> QPlainTextEdit: ...

    @property
    @abstractmethod
    def output_editor(self) -> QTextEdit: ...

    @abstractmethod
    def execute(self) -> None: ...

    def run(self, data: ReceivedData) -> str:
        initial_input = self.input_editor.toPlainText()
        initial_output = self.output_editor.toPlainText()

        self.input_editor.setPlainText(data.text)

        self.execute()

        result = self.output_editor.toPlainText()

        settings = get_settings()
        print(settings)

        if settings.get('mirror_script_editor'):
            self.input_editor.setPlainText(data.text)
            self.output_editor.setPlainText(result)
            return result

        # if settings.get('clear_output', True):
        #     self.output_editor.setPlainText('')

        if settings.get('format_output'):
            self.output_editor.setPlainText(format_output(data, result))

        # else:
        #     self.input_editor.setPlainText(initial_input)
        #     self.output_editor.setPlainText(initial_output)

        return result


C = Callable[[], BaseEditorController]


class EditorController:
    _controller: Optional[C] = None

    @classmethod
    def get_instance(cls) -> Optional[C]:
        return cls._controller

    @classmethod
    def set_instance(cls, controller: C) -> None:
        cls._controller = controller
