# coding: utf-8
from __future__ import print_function

import re
import os
import logging

from sys import getsizeof

from PySide2.QtTest import QTest
from PySide2.QtCore import QObject, Qt

from PySide2.QtWidgets import (
    QPushButton,
    QSplitter,
    QTextEdit,
    QPlainTextEdit,
    QTextEdit,
    QApplication
)

from . import SettingsState, insert_time


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


class NSE(QObject):
    """Nuke Internal Script Editor widget.

    Although a class is not necessary, Qt will complain in some instances that
    internal C++ widget XXX is already deleted. This happens because of how python
    handles the garbage collection. Saving a reference into a instance variable keeps it "alive".

    This could break anytime if Foundry decides to change something.
    """

    def __init__(self, parent=None):
        QObject.__init__(self, parent)

        # HACK: really don't like this way of executing code. is too hacky
        self.script_editor = self.get_script_editor()
        self.run_button = self.get_run_button()
        self.console = self.script_editor.findChild(QSplitter)
        self.output_widget = self.console.findChild(QTextEdit)
        self.input_widget = self.console.findChild(QPlainTextEdit)

    @staticmethod
    def get_script_editor():
        """Get script editor widget."""
        # .topLevelWidgets() is a smaller list but SE is not always there
        for widget in QApplication.allWidgets():
            if 'scripteditor' in widget.objectName():
                return widget

        # XXX: can the script editor not exists?
        raise BaseException(
            'Script Editor panel does not exist! Please create one.'
        )

    def get_run_button(self):
        """Get the run button from the script editor."""
        for button in self.script_editor.findChildren(QPushButton):
            # The only apparent identifier of the button is a tooltip. Risky
            if 'Run' in button.toolTip():
                return button

        # XXX: can the button not be found?
        return None

    def _execute_shortcut(self):
        """Simulate shortcut CTRL + Return for running script.

        This method is currently used as a fallback in case the execute button
        couldn't be found.

        Note: Although this method brings more problems than is solves, it could come
        useful. Also I am not sure if shortcut could be changed by user somehow.
        """
        QTest.keyPress(self.input_widget, Qt.Key_Return, Qt.ControlModifier)
        QTest.keyRelease(self.input_widget, Qt.Key_Return, Qt.ControlModifier)


class ScriptEditor(NSE):
    """Manipulate Nuke internal script editor."""
    lines = []

    def __init__(self, parent=None):
        NSE.__init__(self, parent)

        self.settings = SettingsState()

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

    def execute(self):
        """Abstract method for executing code inside NSE.

        Check if run_button exists otherwise simulate shortcut press.
        """
        if self.run_button:
            self.run_button.click()
        else:
            self._execute_shortcut()

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
