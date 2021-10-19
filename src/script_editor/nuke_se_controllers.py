"""Module for the nuke script editor controller classes."""
# coding: utf-8
from __future__ import print_function

import re
import os
import json
import logging

from sys import getsizeof
from textwrap import dedent

from PySide2.QtCore import QObject

from ..utils import AppSettings, insert_time
from ..script_editor import NukeScriptEditor


LOGGER = logging.getLogger('NukeServerSocket.get_script_editor')


class ScriptEditorController():
    """Manipulate internal script editor."""

    def __init__(self):
        """Init method for the ScriptEditorController class.

        Method will also initialize the NukeScriptEditor class.
        """
        # TODO: should reference input_widget and output_widget
        self.script_editor = NukeScriptEditor()

        self.initial_input = None
        self.initial_output = None

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

    def input(self):  # type: () -> str
        """Get input from the nuke internal script editor."""
        return self.script_editor.input_widget.document().toPlainText()

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


class _PyController(ScriptEditorController, object):
    """Controller class that deals with python code execution."""

    history = []

    def __init__(self, file):
        """Init method for the _PyController class.

        Args:
            file (str): file path of the file that is being executed.
        """
        ScriptEditorController.__init__(self)
        self.settings = AppSettings()
        self._file = file

    def restore_input(self):
        """Override input editor if setting is True."""
        if not self.settings.get_bool('options/override_input_editor'):
            super(_PyController, self).restore_input()

    def restore_output(self):
        """Send text to script editor output if setting is True."""
        if self.settings.get_bool('options/output_to_console'):
            self._output_to_console()
        else:
            super(_PyController, self).restore_output()

    @classmethod
    def _clear_history(cls):
        """Clear the history list."""
        cls.history = []

    @classmethod
    def _append_output(cls, output_text):  # type: (str) -> None
        """Append text to list in order to have a history output.

        The list can have a maximum size of 1mb after that it deletes the last
        element. Theoretically this is way to big, but I am also unsure about
        this method in general so it works for now.

        Args:
            output_text (str): text to append into the list
        """
        cls.history.append(output_text)
        list_size = [getsizeof(n) for n in cls.history]

        if sum(list_size) >= 1000000:
            cls.history.pop(0)

    def _show_file(self):  # type: () -> str
        """Show the file that is being executed.

        File could be empty string, in that case will do nothing

        Returns:
            (str) file - file path of the file that is being executed.
        """
        return self._file if self.settings.get_bool(
            'options/show_file_path') else os.path.basename(self._file)

    @staticmethod
    def _clean_output(text):  # type: (str) -> str
        """Return last section (after #Result:) of the output.

        Args:
            text (str): text do be cleaned

        Returns:
            str: Cleaned text. If #Result is not present in text, then returns
            the untouched text.
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

        if self.settings.get_bool('options/show_unicode', True):
            # Arrow sign going down
            unicode = u'\u21B4'
            output = "[Nuke Tools] %s %s\n%s" % (file, unicode, text)

        return insert_time(output)

    def output(self):  # type: () -> str
        """Get a clean version of the output editor."""
        return self._clean_output(super(_PyController, self).output())

    def _output_to_console(self):
        """Output data to Nuke internal script editor console.

        This function is called only when Output To Console settings is True.
        Output style is decided based on other settings like Format Text and
        Clear Output settings.
        """
        if self.settings.get_bool('options/format_text', True):

            output_text = self._format_output(
                super(_PyController, self).output()
            )

            if self.settings.get_bool('options/clear_output', True):
                super(_PyController, self).set_output(output_text)
            else:
                self._append_output(output_text)
                super(_PyController, self).set_output(''.join(self.history))
                return

        self._clear_history()


class _BlinkController(ScriptEditorController, object):
    """Controller that deals with blink script execution code."""

    def __init__(self, file):
        """Init method for the _BlinkController class.

        Args:
            file (str):  file path of the file that is being executed.
        """
        ScriptEditorController.__init__(self)
        self._file = file

    def output(self):  # type: () -> str
        """Override parent method `output`.

        Returns:
            (str): string literal: 'Recompiling'
        """
        return 'Recompiling'

    def set_input(self, text):  # type: (str) -> str
        """Override parent method `set_input`.

        Wrap the code and insert it to the input widget to be executed.
        """
        text = self._blink_wrapper(text)
        super(_BlinkController, self).set_input(text)

    def _blink_wrapper(self, code):  # type: (str) -> str
        """Wrap the code from the client data into some nuke commands.

        The commands will check for a blinkscript and create one if needed,
        then will execute the code from the blinkscript recompile button.

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


class _CopyNodesController(ScriptEditorController, object):
    """Controller that deals with copy nodes execution code."""

    def __init__(self):
        """Init method for the _CopyNodesController class."""
        ScriptEditorController.__init__(self)

    def output(self):  # type: () -> str
        """Override parent method.

        Method will returning a simple string when pasting nodes.

        Returns:
            (str): string literal: 'Nodes received'.
        """
        return 'Nodes received.'

    def set_input(self, text):  # type: (str) -> str
        """Override parent method by executing the `nuke.nodePaste()` command.

        Method will create a file with the text data received to be used as an
        argument for the `nuke.nodePaste('file')` method.

        Args:
            text (str): the text to be set as input in the widget.
        """
        settings = AppSettings()
        transfer_file = settings.value('path/transfer_file')

        with open(transfer_file, 'w') as file:
            file.write(text)

        text = self._paste_nodes_wrapper(transfer_file)
        super(_CopyNodesController, self).set_input(text)

    def _paste_nodes_wrapper(self, transfer_file):
        """Wrap the file with a nuke nodePaste command.

        Args:
            transfer_file (str): the transfer_nodes.tmp file path.
        """
        return "nuke.nodePaste('{}')".format(transfer_file)


class CodeEditor(QObject):
    """Abstract facade for the script editor controller."""

    def __init__(self, data):  # type: (DataCode) -> None
        """Init method for the CodeEditor class.

        Initialize the controller class based on the type of data received.

        Args:
            data (DataCode): DataCode object.
        """
        self.data = data

        file = data.file
        _, file_ext = os.path.splitext(file)

        if file_ext in {'.cpp', '.blink'}:
            self._controller = _BlinkController(file)

        elif file_ext == '.tmp':
            self._controller = _CopyNodesController()

        else:
            self._controller = _PyController(file)

    def execute(self):
        """Higher level facade of the execute code function.

        Set the input, execute the code, return the output and restore the 
        editor state.
        """
        self._controller.set_input(self.data.text)
        self._controller.execute()

        output = self._controller.output()
        self._controller.restore_state()

        return output
