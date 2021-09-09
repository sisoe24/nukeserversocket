# coding: utf-8
from __future__ import print_function

import re
import os
import logging

from sys import getsizeof

from PySide2.QtWidgets import (
    QSplitter,
    QTextEdit,
    QPlainTextEdit,
    QTextEdit,
    QPushButton,
    QApplication
)

from . import SettingsState, insert_time

# HACK: really dont like this way of executing code. is too hacky

LOGGER = logging.getLogger('NukeServerSocket.get_script_editor')


def _clean_output(text):
    """Return last section (after #Result:) of the output.

    Arguments:

        str text: text do be cleaned

    Returns:
        str: cleaned text
    """
    clean_input = re.search(r'(?:.*Result:\s)(.+)', text, re.S)
    if clean_input:
        return clean_input.group(1)
    return text


def _format_output(text, file, use_unicode=True):
    """Format output to send to nuke internal console."""
    text = _clean_output(text)

    output = "[Nuke Tools] %s \n%s" % (file, text)

    if use_unicode:
        # Arrow sign going down
        unicode = u'\u21B4'
        output = "[Nuke Tools] %s %s\n%s" % (file, unicode, text)

    output = insert_time(output)

    return output


class ScriptEditor:
    """Manipulate Nuke internal script editor."""
    lines = []

    def __init__(self):

        self.settings = SettingsState()

        self.input_widget = _get_input()
        self.output_widget = _get_output()

        self.initial_input = ""
        self.initial_output = ""

        self._file = ''

        self._save_state()

    def _save_state(self):
        """Save initial state of the editor before any modification."""
        self.initial_input = self.input_widget.toPlainText()
        self.initial_output = self.output_widget.toPlainText()

    def set_text(self, text):
        """Set text to the input editor.

        Arguments
            (str) text - text to insert.
        """
        self.input_widget.setPlainText(text)

    def set_file(self, file):
        """Set the file that is being executed.

        File could be empty string, in that case will do nothing

        Args:
            (str) file - file path of the file that is being executed from NukeTools
        """
        self._file = file if self.settings.get_bool(
            'options/include_path') else os.path.basename(file)

    def set_status_output(self):
        """Get a clean version of the output editor for status widget."""
        return _clean_output(self._get_output())

    def _get_output(self):
        """Get output from the nuke internal script editor."""
        return self.output_widget.document().toPlainText()

    @staticmethod
    def execute():
        """Execute the run script editor button."""
        btn = _get_run_button()
        btn.click()

    def _restore_input(self):
        """Override input editor if setting is True."""
        if not self.settings.get_bool('options/override_input'):
            self.input_widget.setPlainText(self.initial_input)

    @classmethod
    def _append_output(cls, output_text):
        """Append text to class list in order to have a history output.

        The list can have a maximum size of 1mb after that it deletes the last element.
        Theoretically this is way to big. But I am also unsure about this method
        in general so it works for now. Need to think it better.

        :param output_text: text to append into the list
        :type output_text: str
        """
        cls.lines.append(output_text)
        list_size = [getsizeof(n) for n in cls.lines]

        # print("➡ list_size :", sum(list_size))
        # print("➡ list_size :", len(cls.lines))

        # HACK: not sure about this. give the list cap at 1 mb. way too generous?
        if sum(list_size) >= 1000000:
            cls.lines.pop(0)

    @classmethod
    def _clear_list(cls):
        """Clear the history list."""
        cls.lines = []

    def _restore_output(self):
        """Send text to script editor output if setting is True."""
        if self.settings.get_bool('options/output_console'):
            self._output_to_console()
        else:
            self.output_widget.setPlainText(self.initial_output)

    def _output_to_console(self):
        """Output data to Nuke internal script editor console."""
        output_text = self._get_output()

        if self.settings.get_bool('options/format_text', True):
            use_unicode = self.settings.get_bool('options/use_unicode', True)
            output_text = _format_output(output_text, self._file, use_unicode)

            if self.settings.get_bool('options/clear_output', True):
                self._clear_list()
                self.output_widget.setPlainText(output_text)
            else:
                self._append_output(output_text)
                self.output_widget.setPlainText(''.join(self.lines))
                return

        self._clear_list()

    def restore_state(self):
        """Restore the initial state of the editor."""
        self._restore_input()
        self._restore_output()


def _get_script_editor():
    """Get script editor widget."""
    # TODO: can the script editor don't exists? if yes then what?
    for widget in QApplication.allWidgets():
        if widget.objectName() == 'uk.co.thefoundry.scripteditor.1':
            return widget
    return None


def _get_console():
    """Get sub widget QSplitter of script editor."""
    script_editor = _get_script_editor()
    for widget in script_editor.children():
        if isinstance(widget, QSplitter):
            return widget
    return None


def _get_output():
    """Get the QTextEdit output widget (upper part)."""
    console_widgets = _get_console().children()
    for widget in console_widgets:
        if isinstance(widget, QTextEdit):
            return widget
    return None


def _get_input():
    """Get the QPlainTextEdit output widget (lower part)."""
    console_widgets = _get_console().children()
    for widget in console_widgets:
        if isinstance(widget, QPlainTextEdit):
            return widget
    return None


def _get_run_button():
    """Get the execute script button from the script editor"""
    script_editor = _get_script_editor()
    for widget in script_editor.children():
        if isinstance(widget, QPushButton):
            if widget.toolTip().startswith('Run the current'):
                return widget
    return None
