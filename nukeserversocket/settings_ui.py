"""Settings UI for Nuke Server Socket.

This module is a wrapper around the settings module, and provides a UI for it.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from textwrap import dedent

from PySide2.QtCore import Slot
from PySide2.QtWidgets import (QWidget, QSpinBox, QCheckBox, QLineEdit,
                               QFormLayout)

if TYPE_CHECKING:
    from .settings import _NssSettings


class NssSettingsModel:
    def __init__(self, settings: _NssSettings):
        self.settings = settings

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        self.settings.set(key, value)


class NssSettingsView(QWidget):
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setMinimumSize(400, 200)

        self.timeout = QSpinBox()
        self.timeout.setToolTip('Server timeout in minutes')

        self.format_output = QLineEdit()
        self.format_output.setToolTip(dedent('''
        Format output using the following placeholders:
        - %d: current time
        - %f: file path
        - %F: file name without path
        - %t: output text
        - %n: new line
        '''.strip()))

        self.mirror_script_editor = QCheckBox()
        self.mirror_script_editor.setToolTip('Mirror script editor')

        self.clear_output = QCheckBox()
        self.clear_output.setToolTip('Clear output before running script')

        form_layout = QFormLayout()
        form_layout.addRow('Server Timeout (min):', self.timeout)
        form_layout.addRow('Mirror script editor:', self.mirror_script_editor)
        form_layout.addRow('Format output:', self.format_output)
        form_layout.addRow('Clear output:', self.clear_output)

        self.setLayout(form_layout)


class NssSettingsController:
    def __init__(self, view: NssSettingsView, model: NssSettingsModel):
        self._view = view
        self._model = model

        self._view.timeout.valueChanged.connect(self._on_timeout_changed)
        self._view.format_output.textChanged.connect(self._on_format_output_changed)
        self._view.mirror_script_editor.stateChanged.connect(self._on_mirror_script_editor_changed)
        self._view.clear_output.stateChanged.connect(self._on_clear_output_changed)

    @Slot(int)
    def _on_mirror_script_editor_changed(self, state: int):
        is_checked = state == 2
        self._view.clear_output.setEnabled(is_checked)
        self._view.format_output.setEnabled(is_checked)
        self._model.set('mirror_script_editor', is_checked)

    @Slot(int)
    def _on_clear_output_changed(self, state: int):
        self._model.set('clear_output', state == 2)

    @Slot(str)
    def _on_format_output_changed(self, text: str):
        self._model.set('format_output', text)

    @Slot(int)
    def _on_timeout_changed(self, timeout: int):
        self._model.set('server_timeout', timeout * 60000)

    def init(self):
        self._view.timeout.setValue(self._model.get('server_timeout') / 60000)

        mirror_script_editor_state = self._model.get('mirror_script_editor')
        self._view.mirror_script_editor.setChecked(mirror_script_editor_state)
        if not mirror_script_editor_state:
            self._view.clear_output.setEnabled(False)
            self._view.format_output.setEnabled(False)

        self._view.format_output.setText(self._model.get('format_output'))
        self._view.clear_output.setChecked(self._model.get('clear_output'))


class NssSettingsUI:
    def __init__(self, settings: _NssSettings):
        self.model = NssSettingsModel(settings)
        self.view = NssSettingsView()
        self.controller = NssSettingsController(self.view, self.model)
        self.controller.init()
