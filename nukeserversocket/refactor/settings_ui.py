from __future__ import annotations

from typing import Any, Dict

from PySide2.QtCore import Slot
from PySide2.QtWidgets import (QLabel, QWidget, QSpinBox, QCheckBox,
                               QFormLayout, QVBoxLayout)

from .settings import get_settings


class NssSettingsModel:
    def __init__(self, settings: Dict[str, Any]):
        self._settings = settings

    def set_timeout(self, timeout: int):
        self._settings.set('server_timeout', timeout)

    def get_timeout(self):
        return self._settings.get('server_timeout')

    def set_format_output(self, format_output: bool):
        self._settings.set('format_output', format_output)

    def get_format_output(self):
        return self._settings.get('format_output', True)


class NssSettingsView(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.timeout = QSpinBox()
        self.format_output = QCheckBox()

        form_layout = QFormLayout()
        form_layout.addRow('Server Timeout (min):', self.timeout)
        form_layout.addRow('Format output:', self.format_output)

        self.setLayout(form_layout)


class NssSettingsController:
    def __init__(self, view: NssSettingsView, model: NssSettingsModel):
        self._view = view
        self._model = model

        self._view.timeout.valueChanged.connect(self._on_timeout_changed)
        self._view.format_output.stateChanged.connect(self._on_format_output_changed)

    @Slot(int)
    def _on_format_output_changed(self, state: int):
        self._model.set_format_output(state == 2)

    @Slot(int)
    def _on_timeout_changed(self, timeout: int):
        self._model.set_timeout(timeout)

    def init(self):
        self._view.timeout.setValue(self._model.get_timeout())
        self._view.format_output.setChecked(self._model.get_format_output())


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
