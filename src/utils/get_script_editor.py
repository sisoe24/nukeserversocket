# coding: utf-8
from __future__ import print_function

import re
import os
import json
import logging

from sys import getsizeof
from textwrap import dedent
from abc import abstractmethod, ABCMeta, abstractproperty

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


LOGGER = logging.getLogger('NukeServerSocket.get_script_editor')


class BaseScriptEditor(object):
    """Abstract class for te BaseScriptEditor implementation.

    This could potentially allow to include other applications like Maya.
    """
    __metaclass__ = ABCMeta

    @abstractmethod
    def execute(self):
        pass

    @abstractproperty
    def input_widget(self):
        pass

    @abstractproperty
    def output_widget(self):
        pass


class NukeScriptEditor(BaseScriptEditor):
    """Nuke Internal Script Editor widget.

    The class get initialized when The NukeServerSocket gets first created. Then
    will save all of the Nuke internal script editor widgets inside class properties
    so it can get called later without having to search each widget again.

    Note: This could break anytime if Foundry changes something.
    """
    # TODO: Should invest some time to find a better way.
    script_editor = QWidget
    run_button = QPushButton
    console = QSplitter
    input_widget = QWidget
    output_widget = QWidget

    def __init__(self):
        LOGGER.debug('init')
        self.init_editor()

    @classmethod
    def init_editor(cls):
        """Initialize NukeScriptEditor properties"""
        cls.script_editor = cls.get_script_editor()
        cls.run_button = cls.get_run_button()
        cls.console = cls.script_editor.findChild(QSplitter)
        cls.output_widget = cls.console.findChild(QTextEdit)
        cls.input_widget = cls.console.findChild(QPlainTextEdit)

    @classmethod
    def get_script_editor(cls):  # type: () -> QWidget
        """Get script editor widget.

        Returns:
            QWidget: Nuke Internal script editor widget

        Raises:
            BaseException: if script editor was not found
        """
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
        """Get the run button from the script editor.

        Returns:
            (QPushButton | None): Return the QPushButton otherwise None
        """
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

    def execute(self):
        """Execute code inside Nuke Script Editor.

        Check if run_button exists otherwise simulate shortcut press.
        """
        try:
            self.run_button.click()
        except AttributeError:
            self._execute_shortcut()


class ScriptEditorController():
    """Manipulate internal script editor."""

    def __init__(self):

        self.script_editor = NukeScriptEditor()

        self.initial_input = ""
        self.initial_output = ""

        self._file = ''

        self._save_state()

    def _save_state(self):
        """Save initial state of the editor before any modification."""
        self.initial_input = self.script_editor.input_widget.toPlainText()
        self.initial_output = self.script_editor.output_widget.toPlainText()

    def set_input(self, text):  # type: (str) -> None
        """Set text to the input editor.

        Arguments
            (str) text - text to insert.
        """
        self.script_editor.input_widget.setPlainText(text)

    def set_output(self, text):  # type: (str) -> None
        """Set text to the output editor.

        Arguments
            (str) text - text to insert.
        """
        self.script_editor.output_widget.setPlainText(text)

    def output(self):  # type: () -> str
        """Get output from the nuke internal script editor."""
        return self.script_editor.output_widget.document().toPlainText()

    def execute(self):
        """Abstract method for executing code from script editor."""
        self.script_editor.execute()

    def restore_input(self):
        """Restore input text."""
        self.script_editor.input_widget.setPlainText(self.initial_input)

    def restore_output(self):
        """Restore output text."""
        self.script_editor.output_widget.setPlainText(self.initial_output)

    def restore_state(self):
        """Restore the initial text data of the editor."""
        self.restore_input()
        self.restore_output()

    def __del__(self):
        """Restore widget text after deleting object"""
        self.restore_state()


class _PyController(ScriptEditorController, object):
    history = []

    def __init__(self, file):
        ScriptEditorController.__init__(self)
        self.settings = SettingsState()
        self._file = file

    def restore_input(self):
        """Override input editor if setting is True."""
        if not self.settings.get_bool('options/override_input'):
            super(_PyController, self).restore_input()

    def restore_output(self):
        """Send text to script editor output if setting is True."""
        if self.settings.get_bool('options/output_console'):
            self._output_to_console()
        else:
            super(_PyController, self).restore_output()

    @classmethod
    def _clear_history(cls):
        """Clear the history list."""
        cls.history = []

    @classmethod
    def _append_output(cls, output_text):  # type: (str) -> None
        """Append text to class list in order to have a history output.

        The list can have a maximum size of 1mb after that it deletes the last element.
        Theoretically this is way to big, but I am also unsure about this method
        in general so it works for now. 

        Args:
            output_text (str): text to append into the list
        """
        cls.history.append(output_text)
        list_size = [getsizeof(n) for n in cls.history]

        if sum(list_size) >= 1000000:
            cls.history.pop(0)

    def _show_file(self):  # type: () -> str
        """Set the file that is being executed.

        File could be empty string, in that case will do nothing

        Returns:
            (str) file - file path of the file that is being executed from NukeTools
        """
        return self._file if self.settings.get_bool(
            'options/include_path') else os.path.basename(self._file)

    @staticmethod
    def _clean_output(text):  # type: (str) -> str
        """Return last section (after #Result:) of the output.

        Args:

            text (str): text do be cleaned

        Returns:
            str: Cleaned text. If #Result is not present in text, then returns the untouched text.
        """
        try:
            return re.search(r'(?:.*Result:\s)(.+)', text, re.S).group(1)
        except AttributeError:
            return text

    def _format_output(self, text):  # type: (str) -> str
        """Format output to send to nuke internal console."""
        text = self._clean_output(text)
        file = self._show_file()

        output = "[Nuke Tools] %s \n%s" % (file, text)

        if self.settings.get_bool('options/use_unicode', True):
            # Arrow sign going down
            unicode = u'\u21B4'
            output = "[Nuke Tools] %s %s\n%s" % (file, unicode, text)

        return insert_time(output)

    def output(self):  # type: () -> str
        """Get a clean version of the output editor."""
        return self._clean_output(super(_PyController, self).output())

    def _output_to_console(self):
        """Output data to Nuke internal script editor console."""

        if self.settings.get_bool('options/format_text', True):

            output_text = self._format_output(
                super(_PyController, self).output()
            )

            if self.settings.get_bool('options/clear_output', True):
                self._clear_history()
                super(_PyController, self).set_output(output_text)
            else:
                self._append_output(output_text)
                super(_PyController, self).set_output(''.join(self.history))
                return

        self._clear_history()


class _BlinkController(ScriptEditorController, object):
    def __init__(self, file):
        ScriptEditorController.__init__(self)
        self._file = file

    def output(self):  # type: () -> str
        """Overriding parent method by returning a simple string when executing
        a blinkscript.
        """
        return 'Recompiling'

    def set_input(self, text):  # type: (str) -> str
        """Overriding parent method by wrapping the code inside a some python
        commands.
        """
        text = self._blink_wrapper(text)
        super(_BlinkController, self).set_input(text)

    def _blink_wrapper(self, code):  # type: (str) -> str
        """Wrap the code from the client data into some nuke commands.

        The nuke commands will check for a blinkscript and create one if needed.
        Then will execute the code from the blinkscript recompile button.

        Returns:
            str: wrapped text code.
        """
        kwargs = {
            'file': self._file,
            'filename': os.path.basename(self._file),
            'code': json.dumps(code)
        }

        return dedent("""
        nodes = [n for n in nuke.allNodes() if "{filename}" == n.name()]
        try:
            node = nodes[0]
        except IndexError:
            node = nuke.createNode('BlinkScript', 'name {filename}')
        finally:
            knobs = node.knobs()
            knobs['kernelSourceFile'].setValue('{file}')
            knobs['kernelSource'].setText({code})
            knobs['recompile'].execute()
        """).format(**kwargs).strip()


class CodeEditor(object):
    """Abstract facade for the script editor controller."""

    def __init__(self, file):  # type: (str) -> None
        if file and file.endswith('.blink'):
            self._controller = _BlinkController(file)
        else:
            self._controller = _PyController(file)

    @property
    def controller(self):
        """The script editor controller class."""
        return self._controller
