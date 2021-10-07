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
    def __init__(self, title: str, is_checked: bool, tooltip: str, parent=None):
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
    def __init__(self):
        QWidget.__init__(self)

        self._output_console = CheckBox(
            is_checked=True, title='Output To Console', parent=self,
            tooltip='Output to internal Script Editor')

        self._format_output = CheckBox(
            is_checked=True, title='Format Text', parent=self,
            tooltip='Clean and format output console text')

        self._clear_output = CheckBox(
            is_checked=True, title='Clear Output', parent=self,
            tooltip='Clear previous output in console. Works only if format text is enabled')

        self._override_input = CheckBox(
            is_checked=False, title='Override Input Editor', parent=self,
            tooltip='Override internal input text editor',)

        self._include_path = CheckBox(
            is_checked=False, title='Show File Path', parent=self,
            tooltip='Include full path of the executed file')

        self._include_unicode = CheckBox(
            is_checked=True, title='Show Unicode', parent=self,
            tooltip='include unicode character in output text')

        _layout = QFormLayout()
        _layout.setVerticalSpacing(10)

        # HACK: this is obviously really ugly. need to find something else
        # try to add the labels dynamically in a loop
        labels = ('Output:', '', '', 'Input:', 'Misc:', '')
        for label, checkbox in zip(labels, self.children()):
            _layout.addRow(QLabel(label), checkbox)

        self.setLayout(_layout)

        self._enable_sub_options()
        self._output_console.toggled.connect(self._enable_sub_options)
        self._format_output.toggled.connect(self._enable_clear_console)

    def _enable_clear_console(self, state: bool):
        """Set state of format output option."""
        self._clear_output.setEnabled(state)
        self._clear_output.setChecked(state)

    def _enable_format_output(self, state: bool):
        """Set state of format output option."""
        self._format_output.setEnabled(state)
        self._format_output.setChecked(state)

    def _enable_sub_options(self):
        """Set sub options that should be enabled only if output console is True.

        Args:
            state (bool): state of output_console attribute
        """
        state = self._output_console.isChecked()

        self._enable_format_output(state)
        self._enable_clear_console(state)
