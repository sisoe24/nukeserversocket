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
    QApplication,
    QWidget
)

from . import SettingsState, insert_time
from ..widgets import ErrorDialog


LOGGER = logging.getLogger('NukeServerSocket.get_script_editor')


def _clean_output(text):  # type: (str) -> str
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


def _format_output(text, file, use_unicode=True):  # type: (str, str, bool) -> str
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

    Don't like this method of executing code, this could break anytime if
    Foundry changes something and it feels too hacky. Should invest some time to
    find a better way.
    """
    script_editor = QWidget
    run_button = QPushButton
    console = QSplitter
    input_widget = QWidget
    output_widget = QWidget

    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        LOGGER.debug('init')
        self.init_editor()

    @classmethod
    def init_editor(cls):
        """Initialize NSE properties"""
        cls.script_editor = cls.get_script_editor()
        cls.run_button = cls.get_run_button()
        cls.console = cls.script_editor.findChild(QSplitter)
        cls.output_widget = cls.console.findChild(QTextEdit)
        cls.input_widget = cls.console.findChild(QPlainTextEdit)

    @classmethod
    def get_script_editor(cls):  # type: () -> QWidget
        """Get script editor widget."""
        # .topLevelWidgets() is a smaller list but SE is not always there
        for widget in QApplication.allWidgets():

            # TODO: user should be able to decide which SE to use
            if 'scripteditor' in widget.objectName():
                return widget

        # XXX: can the script editor not exists?
        # TODO: don't like the traceback but probably will never be called anyway
        raise BaseException(
            'NukeServerSocket: Script Editor panel not found!'
            'Please create one and reload the panel.'
        )

    @classmethod
    def get_run_button(cls):  # type: () -> QPushButton | None
        """Get the run button from the script editor."""
        for button in cls.script_editor.findChildren(QPushButton):
            # The only apparent identifier of the button is a tooltip. Risky
            if 'Run' in button.toolTip():
                return button

        # XXX: can the button not be found?
        return None

    @classmethod
    def _execute_shortcut(cls):
        """Simulate shortcut CTRL + Return for running script.

        This method is currently used as a fallback in case the execute button
        couldn't be found.
        """
        # XXX: could the user change the shortcut? if yes then what?
        QTest.keyPress(cls.input_widget, Qt.Key_Return, Qt.ControlModifier)
        QTest.keyRelease(cls.input_widget, Qt.Key_Return, Qt.ControlModifier)


class ScriptEditor(NSE):
    """Manipulate Nuke internal script editor."""
    history = []

    def __init__(self, parent=None):

        self.settings = SettingsState()

        self.initial_input = ""
        self.initial_output = ""

        self._file = ''

        self._save_state()

    def refresh_parent(self):
        """Call super for parent class."""
        NSE.__init__(self)

    def _save_state(self):
        """Save initial state of the editor before any modification."""
        self.initial_input = self.input_widget.toPlainText()
        self.initial_output = self.output_widget.toPlainText()

    def set_text(self, text):  # type: (str) -> None
        """Set text to the input editor.

        Arguments
            (str) text - text to insert.
        """
        self.input_widget.setPlainText(text)

    def set_file(self, file):  # type: (str) -> None
        """Set the file that is being executed.

        File could be empty string, in that case will do nothing

        Args:
            (str) file - file path of the file that is being executed from NukeTools
        """
        self._file = file if self.settings.get_bool(
            'options/include_path') else os.path.basename(file)

    def set_status_output(self):  # type: () -> str
        """Get a clean version of the output editor for status widget."""
        return _clean_output(self._get_output())

    def _get_output(self):  # type: () -> str
        """Get output from the nuke internal script editor."""
        return self.output_widget.document().toPlainText()

    def execute(self):
        """Abstract method for executing code inside NSE.

        Check if run_button exists otherwise simulate shortcut press.
        """
        try:
            self.run_button.click()
        except AttributeError:
            self._execute_shortcut()

    def _restore_input(self):
        """Override input editor if setting is True."""
        if not self.settings.get_bool('options/override_input'):
            self.input_widget.setPlainText(self.initial_input)

    @classmethod
    def _append_output(cls, output_text):  # type: (str) -> None
        """Append text to class list in order to have a history output.

        The list can have a maximum size of 1mb after that it deletes the last element.
        Theoretically this is way to big. But I am also unsure about this method
        in general so it works for now. Need to think it better.

        :param output_text: text to append into the list
        :type output_text: str
        """
        cls.history.append(output_text)
        list_size = [getsizeof(n) for n in cls.history]

        # HACK: not sure about this. give the list cap at 1 mb. way too generous?
        if sum(list_size) >= 1000000:
            cls.history.pop(0)

    @classmethod
    def _clear_history(cls):
        """Clear the history list."""
        cls.history = []

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
                self._clear_history()
                self.output_widget.setPlainText(output_text)
            else:
                self._append_output(output_text)
                self.output_widget.setPlainText(''.join(self.history))
                return

        self._clear_history()

    def restore_state(self):
        """Restore the initial state of the editor."""
        self._restore_input()
        self._restore_output()
