"""Settings widget module."""
# -*- coding: utf-8 -*-

from collections import namedtuple

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QLabel, QWidget, QSpinBox, QCheckBox, QGroupBox,
                               QFormLayout, QVBoxLayout, QRadioButton)

from ..settings import AppSettings
from ..local.mock import nuke


def _format_name(name):
    """Format name.

    Format a name into lowercase and no space: `This Button` to `this_button`.

    Args:
        name (str): name to be formatted

    Returns:
        str: the formatted name.
    """
    return name.lower().replace(' ', '_')


class _ScriptEditorSettings(QGroupBox):
    """A QGroupBox class for the script editor settings.

    Class that deals mostly with showing the checkbox ui and enabling/disabling
    certain checkboxes state.
    """

    def __init__(self):
        """Init method for the ScriptEditorSettings class."""
        QGroupBox.__init__(self, 'Mirror To Script Editor')

        self._setup_group_toggle()

        # label: output
        self._output_console = self._checkbox_factory(
            'Override Output Editor', 'Output to internal Script Editor', 'Output:')

        self._format_output = self._checkbox_factory(
            'Format Text', 'Clean and format output console text')

        self._clear_output = self._checkbox_factory(
            'Clear Output', 'Output to internal Script Editor')

        self._show_path = self._checkbox_factory(
            'Show File Path', 'Include full path of the executed file')

        self._show_unicode = self._checkbox_factory(
            'Show Unicode', 'include unicode character in output text')

        # label: input
        self._override_input = self._checkbox_factory(
            'Override Input Editor', 'Override internal input text editor', 'Input:')

        _layout = QFormLayout()
        _layout.setAlignment(Qt.AlignCenter)
        _layout.setVerticalSpacing(10)

        for checkbox in self.findChildren(QCheckBox):
            _layout.addRow(checkbox.category, checkbox)

        self.setLayout(_layout)

        self.toggled.connect(self._toggle_sub_options)
        self._output_console.toggled.connect(self._toggle_output_options)
        self._format_output.toggled.connect(self._toggle_clear_console)

    def _checkbox_factory(self, title, tooltip, category=''):
        checkbox = QCheckBox(self, title)
        checkbox.setText(title)
        checkbox.setToolTip(tooltip)

        # HACK: add an attribute to the checkbox for later reference
        checkbox.category = category

        obj_name = _format_name(title)
        setting_name = 'options/%s' % obj_name
        checkbox.setObjectName(obj_name)

        settings = AppSettings()
        checkbox.setChecked(settings.get_bool(setting_name, False))
        checkbox.toggled.connect(
            lambda: settings.setValue(setting_name, checkbox.isChecked())
        )
        return checkbox

    def _setup_group_toggle(self):
        """Set up default groupbox widget settings."""
        self.setCheckable(True)

        setting_name = 'options/mirror_to_script_editor'

        settings = AppSettings()
        self.setChecked(settings.get_bool(setting_name))

        self.toggled.connect(lambda: settings.setValue(setting_name, self.isChecked()))

    @staticmethod
    def _toggle_checkboxes(checkbox, state):  # type: (QCheckBox, bool) -> None
        """Toggle checkbox state.

        Args:
            checkbox (CheckBox): Checkbox object
            state (bool): state of the checkbox.
        """
        checkbox.setEnabled(state)
        checkbox.setChecked(state)

    def _toggle_clear_console(self, state):  # type: (bool) -> None
        """Set checkbox state of Clear Console option.

        Those options should be enabled only if Format Output is True.

        Args:
            state (bool): state of the checkbox.
        """
        self._toggle_checkboxes(self._clear_output, state)
        self._toggle_checkboxes(self._show_unicode, state)
        self._toggle_checkboxes(self._show_path, state)

    def _toggle_output_options(self, state):
        """Set output checkboxes sub options state.

        Those options should be enabled only if Output Console is True.

        Args:
            state (bool): state of output_console attribute
        """
        self._toggle_checkboxes(self._format_output, state)
        self._toggle_checkboxes(self._clear_output, state)
        self._toggle_checkboxes(self._show_path, state)
        self._toggle_checkboxes(self._show_unicode, state)

    def _toggle_sub_options(self):
        """Set checkboxes sub options state.

        All sub options should be enabled only if Mirror to ScriptEditor is True.

        Args:
            state (bool): state of output_console attribute
        """
        state = self.isChecked()
        for checkbox in self.findChildren(QCheckBox):
            self._toggle_checkboxes(checkbox, state)


class _TimeoutSettings(QGroupBox):
    """A QGroupBox class for the timeout settings."""

    def __init__(self):
        """Initialize the TimeoutSettings class."""
        QGroupBox.__init__(self, 'Timeout')

        _layout = QFormLayout()
        _layout.setAlignment(Qt.AlignCenter)
        _layout.addRow(QLabel('Server (minutes)'), self._set_spinbox('server', 10))
        _layout.addRow(QLabel('Receiver (seconds)'), self._set_spinbox('client', 10))
        _layout.addRow(QLabel('Send Nodes (seconds)'), self._set_spinbox('socket', 30))
        self.setLayout(_layout)

    @staticmethod
    def _set_spinbox(label, value):  # type: (str, int) -> QSpinBox
        """Set a spinbox QWidgets object.

        Set up a spinbox class to used in the timeout settings. The value is
        saved inside the NukeServerSocket.ini configuration file.

        Args:
            label (str): the spinbox label to be used in the settings file.
            value (int): the initial value for the spinbox.

        Returns:
            QSpinBox: The QSpinBox object.
        """
        label = 'timeout/%s' % label

        settings = AppSettings()
        spinbox = QSpinBox()
        spinbox.setValue(int(settings.value(label, value)))
        spinbox.valueChanged.connect(lambda time: settings.setValue(label, time))
        return spinbox


class _RadioButtons(QGroupBox):
    """Factory class for creating a QGroupBox with a bunch for radio buttons."""

    def __init__(self, title, buttons=None):
        """Initialize the CodeEngineSettings class."""
        QGroupBox.__init__(self, title)

        _layout = QVBoxLayout()
        _layout.setAlignment(Qt.AlignCenter)

        for button in buttons or []:
            _layout.addWidget(self._setup_button(button.label, button.state))

        self.setLayout(_layout)

    def _setup_button(self, label, default_state):  # type: (str, bool) -> QRadioButton
        """Set a QRadioButton widget.

        Set up a QRadioButton widget default state and connects its toggle
        signal to the application settings.

        Args:
            label (str): label of the radiobutton
            default_state (bool): default state of the button if no settings is
            found.

        Returns:
            _type_: A QRadioButton object.
        """
        settings = AppSettings()
        setting_name = '%s/%s' % (_format_name(self.title()), _format_name(label))

        radiobutton = QRadioButton(label)
        radiobutton.setChecked(settings.get_bool(setting_name, default_state))

        radiobutton.toggled.connect(lambda state: settings.setValue(setting_name, state))

        return radiobutton


class SettingsWidget(QWidget):
    """Settings Widget."""

    def __init__(self):
        """Init method for the SettingsWidget class."""
        QWidget.__init__(self)
        self.setObjectName('SettingsWidget')

        RadioButton = namedtuple('RadioButtons', ['label', 'state'])

        _layout = QVBoxLayout()
        _layout.addWidget(_RadioButtons('Code Execution Engine',
                                        [RadioButton('Nuke Internal', False),
                                         RadioButton('Script Editor', True)]))
        if nuke.env.get('NukeVersionMajor') < 14:
            _layout.addWidget(_RadioButtons('Connection Type',
                                            [RadioButton('TCP', True),
                                             RadioButton('WebSocket', False)]))
        _layout.addWidget(_ScriptEditorSettings())
        _layout.addWidget(_TimeoutSettings())

        self.setLayout(_layout)
