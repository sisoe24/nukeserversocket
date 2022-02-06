"""Settings widget module."""
# -*- coding: utf-8 -*-
from __future__ import print_function

import logging

from PySide2.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QLabel,
    QWidget,
    QGroupBox,
    QVBoxLayout
)

from ..utils import AppSettings

LOGGER = logging.getLogger('NukeServerSocket.settings_widget')


class CheckBox(QCheckBox):
    """Custom QCheckBox class.

    CheckBox is a custom QCheckBox class that initializes a checkbox obj and
    assigns them some default values based on the arguments. Class will also
    connect the toggle signal to update the configuration setting value.
    """

    def __init__(self, title, label, is_checked, tooltip, parent=None):
        # type: (str, str, bool, str, QWidget | None) -> None
        """Init method for the CheckBox class.

        Args:
            title (str): title of the checkbox.
            label (str): label of the checkbox.
            is_checked (bool): initial state of the checkbox if does not have
            already a setting value in the config file.
            tooltip (str): checkbox tooltip.
            parent (str, optional): QWidget to set as parent. Defaults to None.
        """
        QCheckBox.__init__(self, title, parent)
        self.setToolTip(tooltip)
        self._label = label

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
    certain checkboxes state.
    """

    def __init__(self):
        """Init method for the SettingsWidget class."""
        QWidget.__init__(self)
        self.setObjectName('SettingsWidget')

        self._se_checkbox = QGroupBox('Mirror To Script Editor')
        self._se_checkbox.setCheckable(True)
        self._se_checkbox.setChecked(False)

        self._output_console = CheckBox(
            is_checked=False, title='Override Output Editor', parent=self,
            tooltip='Output to internal Script Editor', label='Output:')

        self._format_output = CheckBox(
            is_checked=False, title='Format Text', parent=self, label='',
            tooltip='Clean and format output console text')

        self._clear_output = CheckBox(
            is_checked=False, title='Clear Output', parent=self, label='',
            tooltip='Clear previous output in console. Works only if Format Text is enabled')

        self._show_path = CheckBox(
            is_checked=False, title='Show File Path', parent=self, label='',
            tooltip='Include full path of the executed file')

        self._show_unicode = CheckBox(
            is_checked=False, title='Show Unicode', parent=self, label='',
            tooltip='include unicode character in output text')

        self._override_input = CheckBox(
            is_checked=False, title='Override Input Editor', parent=self,
            tooltip='Override internal input text editor', label='Input:')

        _layout_checkboxes = QFormLayout()
        _layout_checkboxes.setVerticalSpacing(10)

        for checkbox in self.findChildren(CheckBox):
            _layout_checkboxes.addRow(checkbox._label, checkbox)

        self._se_checkbox.setLayout(_layout_checkboxes)

        _layout = QVBoxLayout()
        _layout.addWidget(self._se_checkbox)

        self.setLayout(_layout)

        self._se_checkbox.toggled.connect(self._toggle_sub_options)
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
        state = self._se_checkbox.isChecked()
        for checkbox in self._se_checkbox.findChildren(CheckBox):
            self._toggle_checkboxes(checkbox, state)
