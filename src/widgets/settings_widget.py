"""Settings widget module."""
# -*- coding: utf-8 -*-
from __future__ import print_function

import logging

from PySide2.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QWidget
)

from ..utils import AppSettings

LOGGER = logging.getLogger('NukeServerSocket.settings_widget')


class CheckBox(QCheckBox):
    """Custom QCheckBox class.

    CheckBox is a custom QCheckBox class that initializes a checkbox obj and
    assigns them some default values based on the arguments. Class will also
    connect the toggle signal to update the configuration setting value.
    """

    def __init__(self, title, is_checked, tooltip, parent=None):
        # type: (str, bool, str, QWidget | None) -> None
        """Init method for the CheckBox class.

        Args:
            title (str): title of the checkbox.
            is_checked (bool): initial state of the checkbox if does not have
            already a setting value in the config file.
            tooltip (str): checkbox tooltip.
            parent (str, optional): QWidget to set as parent. Defaults to None.
        """
        QCheckBox.__init__(self, title, parent)
        self.setToolTip(tooltip)

        obj_name = title.lower().replace(' ', '_')
        ini_value = 'options/%s' % obj_name
        self.setObjectName(obj_name)

        self.settings = AppSettings()
        self.setChecked(self.settings.get_bool(ini_value, is_checked))

        self.toggled.connect(
            lambda: self.settings.setValue(ini_value, self.isChecked())
        )


class SettingsWidget(QWidget):
    """Settings Widget.

    Class that deals mostly with showing the checkbox ui and enabling/disabling
    certain checkboxs state.
    """

    def __init__(self):
        """Init method for the SettingsWidget class."""
        QWidget.__init__(self)
        self.setObjectName('SettingsWidget')

        self._mirror_to_se = CheckBox(
            is_checked=False, title='Mirror to ScriptEditor', parent=self,
            tooltip='Mirror code execution to internal script editor')

        self._output_console = CheckBox(
            is_checked=False, title='Override Output Editor', parent=self,
            tooltip='Output to internal Script Editor')

        self._format_output = CheckBox(
            is_checked=False, title='Format Text', parent=self,
            tooltip='Clean and format output console text')

        self._clear_output = CheckBox(
            is_checked=False, title='Clear Output', parent=self,
            tooltip='Clear previous output in console. Works only if Format Text is enabled')

        self._show_path = CheckBox(
            is_checked=False, title='Show File Path', parent=self,
            tooltip='Include full path of the executed file')

        self._show_unicode = CheckBox(
            is_checked=True, title='Show Unicode', parent=self,
            tooltip='include unicode character in output text')

        self._override_input = CheckBox(
            is_checked=False, title='Override Input Editor', parent=self,
            tooltip='Override internal input text editor',)

        _layout = QFormLayout()
        _layout.setVerticalSpacing(10)

        # HACK: this is really ugly.
        # try to add the labels dynamically in a loop
        labels = ('', 'Output:', '', '', '', '', 'Input:')
        for label, checkbox in zip(labels, self.children()):
            _layout.addRow(QLabel(label), checkbox)

        self.setLayout(_layout)

        self._toggle_sub_options()
        self._mirror_to_se.toggled.connect(self._toggle_sub_options)
        self._output_console.toggled.connect(self._toggle_output_options)
        self._format_output.toggled.connect(self._toggle_clear_console)

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

    def _toggle_output_options(self):
        """Set output checkboxes sub options state.

        Those options should be enabled only if Output Console is True.

        Args:
            state (bool): state of output_console attribute
        """
        state = self._output_console.isChecked()

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
        state = self._mirror_to_se.isChecked()
        for checkbox in self.children():
            if isinstance(checkbox, CheckBox) and checkbox.objectName() != 'mirror_to_scripteditor':
                self._toggle_checkboxes(checkbox, state)
