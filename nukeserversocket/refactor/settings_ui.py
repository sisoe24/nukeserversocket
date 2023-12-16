from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict

from PySide2.QtCore import Slot
from PySide2.QtWidgets import (QLabel, QWidget, QSpinBox, QCheckBox, QLineEdit,
                               QFormLayout, QVBoxLayout)

from .settings import get_settings

if TYPE_CHECKING:
    from .settings import _NssSettings


class NssSettingsModel:
    def __init__(self, settings: '_NssSettings'):
        self._settings = settings

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        self._settings.set(key, value)


class NssSettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumSize(400, 200)

        self.timeout = QSpinBox()
        self.format_output = QLineEdit()
        self.mirror_script_editor = QCheckBox()
        self.clear_output = QCheckBox()

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
        self._view.format_output.textEdited.connect(self._on_format_output_changed)
        self._view.mirror_script_editor.stateChanged.connect(self._on_mirror_script_editor_changed)
        self._view.clear_output.stateChanged.connect(self._on_clear_output_changed)

    @Slot(int)
    def _on_mirror_script_editor_changed(self, state: int):
        self._model.set('mirror_script_editor', state == 2)

    @Slot(int)
    def _on_clear_output_changed(self, state: int):
        self._model.set('clear_output', state == 2)

    @Slot(int)
    def _on_format_output_changed(self, text: str):
        self._model.set('format_output', text)

    @Slot(int)
    def _on_timeout_changed(self, timeout: int):
        self._model.set('server_timeout', timeout * 10000)

    def init(self):
        self._view.timeout.setValue(self._model.get('server_timeout') / 10000)
        self._view.mirror_script_editor.setChecked(self._model.get('mirror_script_editor'))
        self._view.format_output.setText(self._model.get('format_output'))
        self._view.clear_output.setChecked(self._model.get('clear_output'))


class NssSettings:
    def __init__(self):
        self._model = NssSettingsModel(get_settings())
        self._view = NssSettingsView()
        self._controller = NssSettingsController(self._view, self._model)
        self._controller.init()

    def view(self):
        return self._view

    def model(self):
        return self._model

    def controller(self):
        return self._controller
