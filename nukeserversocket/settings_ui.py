"""Settings UI for Nuke Server Socket.

This module is a wrapper around the settings module, and provides a UI for it.

"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional
from textwrap import dedent

from ._qt import (Slot, QLabel, QWidget, QSpinBox, QCheckBox, QLineEdit, QFileDialog,
                  QFormLayout, QHBoxLayout, QPushButton)

from .tools import create_sample
from .logger import get_logger

if TYPE_CHECKING:
    from .settings import _NssSettings

LOGGER = get_logger()


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
        self.timeout.setRange(0, 1440)
        self.timeout.setSpecialValueText('Never')
        self.timeout.setToolTip('Close the server after this many idle minutes. 0 never closes it.')

        self.auto_start = QCheckBox()
        self.auto_start.setToolTip('Start the server when the panel opens')

        self.allow_lan = QCheckBox()
        self.allow_lan.setToolTip(
            'Accept code from other machines on the network, with no authentication. '
            'Applies the next time the server connects.'
        )

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

        self.tools_file = QLineEdit()
        self.tools_file.setPlaceholderText('None: clients can run any code')
        self.tools_file.setToolTip(
            'JSON file of the tools clients may call, and whether they may run code. '
            'Applies the next time the server connects.'
        )
        self.tools_file_browse = QPushButton('Browse...')
        self.tools_file_sample = QPushButton('Create sample...')
        self.tools_file_sample.setToolTip(
            'Write a sample tools file and its Python module into a folder, and use it.')
        # buttons go under the field, so a narrow panel still shows the path
        tools_layout = QHBoxLayout()
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.addWidget(self.tools_file_browse)
        tools_layout.addWidget(self.tools_file_sample)
        tools_layout.addStretch()
        tools_buttons = QWidget()
        tools_buttons.setLayout(tools_layout)
        self.tools_file_note = QLabel('Set by the NSS_TOOLS environment variable.')
        self.tools_file_note.setVisible(False)

        form_layout = QFormLayout()
        form_layout.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        form_layout.addRow('Server Timeout (min):', self.timeout)
        form_layout.addRow('Auto start:', self.auto_start)
        form_layout.addRow('Allow LAN connections:', self.allow_lan)
        form_layout.addRow('Mirror script editor:', self.mirror_script_editor)
        form_layout.addRow('Format output:', self.format_output)
        form_layout.addRow('Clear output:', self.clear_output)
        form_layout.addRow('Tools file:', self.tools_file)
        form_layout.addRow('', tools_buttons)
        form_layout.addRow('', self.tools_file_note)

        self.setLayout(form_layout)

    def set_tools_file(self, path: str, from_env: bool):
        self.tools_file.setText(path)
        self.tools_file.setEnabled(not from_env)
        self.tools_file_browse.setEnabled(not from_env)
        self.tools_file_sample.setEnabled(not from_env)
        self.tools_file_note.setVisible(from_env)

    def browse_tools_file(self) -> str:
        path, _ = QFileDialog.getOpenFileName(
            self, 'Tools file', self.tools_file.text(), 'JSON (*.json)')
        return path

    def choose_sample_folder(self) -> str:
        return QFileDialog.getExistingDirectory(self, 'Folder for the sample tools file')


class NssSettingsController:
    def __init__(self, view: NssSettingsView, model: NssSettingsModel):
        self._view = view
        self._model = model

        self._view.timeout.valueChanged.connect(self._on_timeout_changed)
        self._view.auto_start.stateChanged.connect(self._on_auto_start_changed)
        self._view.allow_lan.stateChanged.connect(self._on_allow_lan_changed)
        self._view.format_output.textChanged.connect(self._on_format_output_changed)
        self._view.mirror_script_editor.stateChanged.connect(self._on_mirror_script_editor_changed)
        self._view.clear_output.stateChanged.connect(self._on_clear_output_changed)
        self._view.tools_file.editingFinished.connect(self._on_tools_file_changed)
        self._view.tools_file_browse.clicked.connect(self._on_tools_file_browse)
        self._view.tools_file_sample.clicked.connect(self._on_create_sample)

    @Slot()
    def _on_create_sample(self):
        folder = self._view.choose_sample_folder()
        if not folder:
            return
        try:
            path = create_sample(folder)
        except OSError as e:
            LOGGER.warning('Could not create the sample tools file: %s', e)
            return
        self._view.tools_file.setText(path)
        self._on_tools_file_changed()
        LOGGER.info('Created sample tools file %s. Edit it, then reconnect.', path)

    @Slot()
    def _on_tools_file_changed(self):
        self._model.set('tools_file', self._view.tools_file.text().strip())

    @Slot()
    def _on_tools_file_browse(self):
        path = self._view.browse_tools_file()
        if path:
            self._view.tools_file.setText(path)
            self._on_tools_file_changed()

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
    def _on_auto_start_changed(self, state: int):
        self._model.set('auto_start', state == 2)

    @Slot(int)
    def _on_allow_lan_changed(self, state: int):
        self._model.set('allow_lan', state == 2)

    @Slot(int)
    def _on_timeout_changed(self, timeout: int):
        self._model.set('server_timeout', timeout * 60000)

    def init(self):
        self._view.timeout.setValue(self._model.get('server_timeout') // 60000)
        self._view.auto_start.setChecked(self._model.get('auto_start'))
        self._view.allow_lan.setChecked(self._model.get('allow_lan'))

        mirror_script_editor_state = self._model.get('mirror_script_editor')
        self._view.mirror_script_editor.setChecked(mirror_script_editor_state)
        if not mirror_script_editor_state:
            self._view.clear_output.setEnabled(False)
            self._view.format_output.setEnabled(False)

        self._view.format_output.setText(self._model.get('format_output'))
        self._view.clear_output.setChecked(self._model.get('clear_output'))
        self._view.set_tools_file(*self._model.settings.tools_file())


class NssSettingsUI:
    def __init__(self, settings: _NssSettings):
        self.model = NssSettingsModel(settings)
        self.view = NssSettingsView()
        self.controller = NssSettingsController(self.view, self.model)
        self.controller.init()
