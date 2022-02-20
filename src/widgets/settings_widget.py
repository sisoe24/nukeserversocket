"""Settings widget module."""
# -*- coding: utf-8 -*-
from __future__ import print_function

import logging
from collections import namedtuple

from PySide2.QtCore import Qt
from PySide2.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QWidget,
    QGroupBox,
    QVBoxLayout,
    QSpinBox,
    QLabel,
    QRadioButton
)

from ..utils import AppSettings

LOGGER = logging.getLogger('NukeServerSocket.settings_widget')

_RadioButton = namedtuple('RadioButtons', ['label', 'state'])


def _format_name(name):
    """Format name.

    Format a name into lowercase and no space: `This Button` to `this_button`.

    Args:
        name (str): name to be formatted

    Returns:
        str: the formatted name.
    """
    return name.lower().replace(' ', '_')


class CheckBox(QCheckBox):
    """Custom QCheckBox class.

    CheckBox is a custom QCheckBox class that initializes a checkbox obj and
    assigns them some default values based on the arguments. Class will also
    connect the toggle signal to update the configuration setting value.
    """

    def __init__(self, title, label, default_state, tooltip, parent=None):
        # type: (str, str, bool, str, QWidget | None) -> None
        """Init method for the CheckBox class.

        Args:
            title (str): title of the checkbox.
            label (str): label of the checkbox.
            default_state (bool): initial state of the checkbox if does not have
            already a setting value in the config file.
            tooltip (str): checkbox tooltip.
            parent (str, optional): QWidget to set as parent. Defaults to None.
        """
        QCheckBox.__init__(self, title, parent)
        self.setToolTip(tooltip)
        self._label = label

        obj_name = _format_name(title)
        setting_name = 'options/%s' % obj_name
        self.setObjectName(obj_name)

        settings = AppSettings()
        self.setChecked(settings.get_bool(setting_name, default_state))
        self.toggled.connect(
            lambda: settings.setValue(setting_name, self.isChecked())
        )


class ScriptEditorSettings(QGroupBox):
    """A QGroupBox class for the script editor settings.

    Class that deals mostly with showing the checkbox ui and enabling/disabling
    certain checkboxes state.
    """

    def __init__(self):
        """Init method for the ScriptEditorSettings class."""
        QGroupBox.__init__(self, 'Mirror To Script Editor')

        self._setup_group_toggle()

        self._output_console = CheckBox(
            default_state=False, title='Override Output Editor', parent=self,
            tooltip='Output to internal Script Editor', label='Output:')

        self._format_output = CheckBox(
            default_state=False, title='Format Text', parent=self, label='',
            tooltip='Clean and format output console text')

        self._clear_output = CheckBox(
            default_state=False, title='Clear Output', parent=self, label='',
            tooltip='Clear previous output in console. Works only if Format Text is enabled')

        self._show_path = CheckBox(
            default_state=False, title='Show File Path', parent=self, label='',
            tooltip='Include full path of the executed file')

        self._show_unicode = CheckBox(
            default_state=False, title='Show Unicode', parent=self, label='',
            tooltip='include unicode character in output text')

        self._override_input = CheckBox(
            default_state=False, title='Override Input Editor', parent=self,
            tooltip='Override internal input text editor', label='Input:')

        _layout = QFormLayout()
        _layout.setAlignment(Qt.AlignCenter)
        _layout.setVerticalSpacing(10)

        for checkbox in self.findChildren(CheckBox):
            _layout.addRow(checkbox._label, checkbox)

        self.setLayout(_layout)

        self.toggled.connect(self._toggle_sub_options)
        self._output_console.toggled.connect(self._toggle_output_options)
        self._format_output.toggled.connect(self._toggle_clear_console)

    def _setup_group_toggle(self):
        """Set initial default groupbox widget settings."""
        self.setCheckable(True)

        setting_name = "options/mirror_to_script_editor"

        settings = AppSettings()
        self.setChecked(settings.get_bool(setting_name))

        self.toggled.connect(
            lambda: settings.setValue(
                setting_name, self.isChecked())
        )

    @staticmethod
    def _toggle_checkboxes(checkbox, state):  # type: (CheckBox, bool) -> None
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
        for checkbox in self.findChildren(CheckBox):
            self._toggle_checkboxes(checkbox, state)


class TimeoutSettings(QGroupBox):
    """A QGroupBox class for the timeout settings."""

    def __init__(self):
        """Initialize the TimeoutSettings class."""
        QGroupBox.__init__(self, 'Timeout')

        _layout = QFormLayout()
        _layout.setAlignment(Qt.AlignCenter)
        _layout.addRow(QLabel('Server (minutes)'),
                       self.set_spinbox('server', 10))
        _layout.addRow(QLabel('Receiver (seconds)'),
                       self.set_spinbox('client', 10))
        _layout.addRow(QLabel('Send Nodes (seconds)'),
                       self.set_spinbox('socket', 30))
        self.setLayout(_layout)

    @staticmethod
    def set_spinbox(label, value):  # type: (str, int) -> QSpinBox
        """Set a spinbox QWidgets class.

        Set up a spinbox class to be used for the timeout settings.

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
        spinbox.valueChanged.connect(
            lambda time: settings.setValue(label, time)
        )
        return spinbox


class RadioButtons(QGroupBox):
    """A QGroupBox class for the code execution engine settings.

    Settings will allow the user to choose which engine to use when executing
    code:
        * Nuke internal: nukeExecuteInMainThread.
        * Script Editor: Qt scriptEditor widget.
    """

    def __init__(self, title, buttons=None):
        """Initialize the CodeEngineSettings class."""
        QGroupBox.__init__(self, title)

        _layout = QVBoxLayout()
        _layout.setAlignment(Qt.AlignCenter)

        if buttons:
            for button in buttons:
                _layout.addWidget(self.setup_button(
                    button.label, button.state))

        self.setLayout(_layout)

    def setup_button(self, label, default_state):  # type: (str, bool) -> QRadioButton
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
        setting_name = '%s/%s' % (_format_name(self.title()),
                                  _format_name(label))

        radiobutton = QRadioButton(label)
        radiobutton.setChecked(settings.get_bool(setting_name, default_state))

        radiobutton.toggled.connect(
            lambda state: settings.setValue(setting_name, state)
        )

        return radiobutton


class SettingsWidget(QWidget):
    """Settings Widget."""

    def __init__(self):
        """Init method for the SettingsWidget class."""
        QWidget.__init__(self)
        self.setObjectName('SettingsWidget')

        _layout = QVBoxLayout()
        _layout.addWidget(RadioButtons('Code Execution Engine',
                                       [_RadioButton('Nuke Internal', True),
                                        _RadioButton('Script Editor', False)]))
        _layout.addWidget(RadioButtons('Connection Type',
                                       [_RadioButton('TCP', True),
                                        _RadioButton('WebSocket', False)]))
        _layout.addWidget(ScriptEditorSettings())
        _layout.addWidget(TimeoutSettings())

        self.setLayout(_layout)
