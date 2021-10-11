# coding: utf-8
from __future__ import print_function

import re
import os
import json
import logging

from sys import getsizeof
from textwrap import dedent

from ..utils import AppSettings, insert_time
from ..script_editor import NukeScriptEditor


LOGGER = logging.getLogger('NukeServerSocket.get_script_editor')


class ScriptEditorController():
    """Manipulate internal script editor."""

    def __init__(self):

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
        # TODO: this is kind of confusing
        self.restore_state()


class _PyController(ScriptEditorController, object):
    history = []

    def __init__(self, file):
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
            'options/show_file_path') else os.path.basename(self._file)

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

        if self.settings.get_bool('options/show_unicode', True):
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


class _CopyNodesController(ScriptEditorController, object):
    def __init__(self):
        ScriptEditorController.__init__(self)
        self.settings = AppSettings()

    def output(self):  # type: () -> str
        """Overriding parent method by returning a simple string when pasting nodes.
        """
        return 'Nodes copied'

    def set_input(self, text):  # type: (str) -> str
        """Overriding parent method by executing the `nuke.nodePaste()` command.

        Method will create a file with the text data received to be used as an
        argument for the `nuke.nodePaste('file')` method.
        """
        transfer_file = self.settings.value('path/transfer_file')
        with open(transfer_file, 'w') as file:
            file.write(text)

        text = "nuke.nodePaste('%s')" % transfer_file
        super(_CopyNodesController, self).set_input(text)


class CodeEditor(object):
    """Abstract facade for the script editor controller."""

    def __init__(self, file):  # type: (str) -> None
        _, file_ext = os.path.splitext(file)

        if file_ext in {'.cpp', '.blink'}:
            self._controller = _BlinkController(file)

        elif file_ext == '.tmp':
            self._controller = _CopyNodesController()

        else:
            self._controller = _PyController(file)

    @property
    def controller(self):
        """The script editor controller class."""
        return self._controller
