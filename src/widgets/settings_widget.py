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
        # TODO: refactor sections into their own classes?

        # BUG: when reloading the settings widget, checkboxes that depend on
        # `output_console` will override their original state

        self._output_console = CheckBox(
            is_checked=True, title='Output To Console', parent=self,
            tooltip='Output to internal Script Editor')

        self._format_output = CheckBox(
            is_checked=True, title='Format Text', parent=self,
            tooltip='Clean and format output console text')

        self._clear_output = CheckBox(
            is_checked=True, title='Clear Output', parent=self,
            tooltip='Clear previous output in console. Works only if Format Text is enabled')

        CheckBox(is_checked=False, title='Override Input Editor', parent=self,
                 tooltip='Override internal input text editor',)

        CheckBox(is_checked=False, title='Show File Path', parent=self,
                 tooltip='Include full path of the executed file')

        CheckBox(is_checked=True, title='Show Unicode', parent=self,
                 tooltip='include unicode character in output text')

        _layout = QFormLayout()
        _layout.setVerticalSpacing(10)

        # HACK: this is really ugly. need to think something else
        # try to add the labels dynamically in a loop
        labels = ('Output:', '', '', 'Input:', 'Misc:', '')
        for label, checkbox in zip(labels, self.children()):
            _layout.addRow(QLabel(label), checkbox)

        self.setLayout(_layout)

        self._enable_sub_options()
        self._output_console.toggled.connect(self._enable_sub_options)
        self._format_output.toggled.connect(self._enable_clear_console)

    def _enable_clear_console(self, state):  # type: (bool) -> None
        """Set checkbox state of Clear Console option."""
        self._clear_output.setEnabled(state)
        self._clear_output.setChecked(state)

    def _enable_format_output(self, state):  # type: (bool) -> None
        """Set checkbox state of Format Output option."""
        self._format_output.setEnabled(state)
        self._format_output.setChecked(state)

    def _enable_sub_options(self):
        """Set chcekboxes sub options state.

        Sub options should be enabled only if Output Console is True.

        Args:
            state (bool): state of output_console attribute
        """
        state = self._output_console.isChecked()

        self._enable_format_output(state)
        self._enable_clear_console(state)
