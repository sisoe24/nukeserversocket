# -*- coding: utf-8 -*-
from __future__ import print_function

import logging

from PySide2.QtWidgets import (
    QCheckBox,
    QFormLayout,
    QFrame,
    QSizePolicy,
    QLabel,
    QSizePolicy,
    QWidget
)

from ..utils import Settings

LOGGER = logging.getLogger('NukeServerSocket.server_status')


class QHLine(QFrame):
    def __init__(self):
        QFrame.__init__(self,)

        self.setMinimumWidth(100)
        self.setFixedHeight(20)
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)


class SettingsWidget(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.settings = Settings()

        # setup checkboxes
        self._output_console = self._create_checkbox(
            state=False, obj_name='output_console',
            toolTip='Output to internal Script Editor'
        )

        self._format_output = self._create_checkbox(
            state=True, obj_name='format_text',
            toolTip='Clean and format output console text'
        )

        self._clear_output = self._create_checkbox(
            state=True, obj_name='clear_output',
            toolTip='Clear previous output in console. Works only if format text is enabled'
        )

        self._override_input = self._create_checkbox(
            state=False, obj_name='override_input',
            toolTip='Override internal input text editor',
        )

        self._include_path = self._create_checkbox(
            state=False, obj_name='include_path',
            toolTip='Include full path of the executed file'
        )

        self._include_unicode = self._create_checkbox(
            state=True, obj_name='use_unicode',
            toolTip='include unicode character in output text'
        )

        # setup Labels
        _format = QLabel('Clean & Format Text')
        _format.setToolTip('what the fuck')
        _format.setObjectName('label1')

        _clear = QLabel('Clear Previous Output')
        _clear.setObjectName('label2')

        # setup Layout
        _layout = QFormLayout()
        _layout.addRow(QLabel('Output'), QHLine())
        _layout.addRow(QLabel('Output to Script Editor'), self._output_console)
        _layout.addRow(_format, self._format_output)
        _layout.addRow(_clear, self._clear_output)

        _layout.addRow(QLabel('Input'), QHLine())
        _layout.addRow(QLabel('Override Input Editor'), self._override_input)

        _layout.addRow(QLabel('Other'), QHLine())
        _layout.addRow(QLabel('Include file full path'), self._include_path)
        _layout.addRow(QLabel('Include unicode'), self._include_unicode)

        self.setLayout(_layout)

        self.setStyleSheet('QCheckBox:disabled {color: grey;}')
        self.initial_style = self.styleSheet()

        for checkbox in self.findChildren(QCheckBox):
            self._setup_checkbox_config(
                propriety=checkbox,
                default_value=checkbox.isChecked(),
                config=checkbox.objectName()
            )

    @staticmethod
    def _create_checkbox(*args, **kwargs):
        """Create template checkbox"""
        checkbox = QCheckBox()

        checkbox.setChecked(kwargs.get('state', False))
        checkbox.setObjectName(kwargs.get('obj_name', ''))
        checkbox.setStatusTip(kwargs.get('statusBarTip', ''))

        # BUG: nuke doesnt display tooltip in dialog window?
        checkbox.setToolTip(kwargs.get('toolTip', ''))

        return checkbox

    def _setup_checkbox_config(self, propriety, default_value, config):
        """Auto-setup for setChecked and signal toggled for all the checkboxes in widget.

        Args:
            propriety (QCheckBox): QCheckBox to initiate setup.
            default_value (bool): Value to set if no config is present.
            config (str): name of the configuration in the settings file.
        """
        propriety.setChecked(
            self.settings.get_bool('options/%s' % config, default_value)
        )
        propriety.toggled.connect(
            lambda value: self._update_settings(config, value)
        )

        self._set_substate(self._output_console.isChecked())

    def _set_substate(self, value):
        """Set sub options that should be enabled only if output console is True.

        Args:
            value (bool): state of output_console property
        """
        self._format_output.setEnabled(value)

        # HACK: if format output is True but console is false then override state to false
        sub_state = self._format_output.isChecked() if value else False
        self._clear_output.setEnabled(sub_state)

        style = self._set_format_label(value)
        self._set_clear_label(style, sub_state)

    def _set_format_label(self, value):
        """Set the label color to enabled/disabled based on widget state.

        Args:
            value (bool): state of the widget.

        Returns:
            style (str): widget style css string.
        """
        style = self.initial_style

        add_style = 'QLabel#label1 {color: grey;}'
        if value:
            add_style = 'QLabel#label1 {color: white;}'

        style += add_style
        return style

    def _set_clear_label(self, add_style, value):
        """Set the label color to enabled/disabled based on widget state.

        Args:
            add_style (str): string to append new style.
            value (bool): state of the widget.
        """
        style = add_style
        add_style = 'QLabel#label2 {color: grey;}'

        if value:
            add_style = 'QLabel#label2 {color: white;}'

        style += add_style

        self.setStyleSheet(style)

    def _update_settings(self, config, value):
        """Update settings file for checkboxes.

        Args:
            config([type]): [description]
            value([type_config]): [description]
        """
        if config == 'output_console':
            self._set_substate(value)
        elif config == 'format_text':
            self._clear_output.setEnabled(value)
            self._set_clear_label(self.initial_style, value)

        self.settings.setValue('options/%s' % config, value)
