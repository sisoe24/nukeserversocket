"""Module for the nuke script editor controller classes."""
# coding: utf-8
from __future__ import print_function

import io
import re
import os
import sys
import json
import logging
import contextlib

from textwrap import dedent

from PySide2.QtCore import QObject, Signal

from .. import nuke
from ..utils import AppSettings, insert_time
from .nuke_script_editor import ScriptEditorController

LOGGER = logging.getLogger('NukeServerSocket.controllers')


class _ExecuteInMainThread(QObject):
    """Execute code inside Nuke.

    Execute code inside nuke with the method `executeInMainThreadWithResult`.

    Signal:
        (str) execution_error: emits wen there is an execution error; more
        specifically when it fails to execute the code with the nuke internal
        function `executeInMainThreadWithResult`. In that case will fallback to
        the ScriptEditorController to execute the code.
    """

    execution_error = Signal(str)

    def __init__(self):
        """Initialize the class and the the scriptEditorController."""
        QObject.__init__(self)
        self.script_editor = ScriptEditorController()

        self._output = None
        self._input = None

    @staticmethod
    @contextlib.contextmanager
    def stdoutIO(stdout=None):
        """Get output from sys.stdout after executing code from `exec`.

        https://stackoverflow.com/a/3906390/9392852
        """
        old = sys.stdout
        if stdout is None:
            stdout = io.StringIO()
        sys.stdout = stdout
        yield stdout
        sys.stdout = old

    def _exec(self, data):  # type: (str) -> str
        """Execute a string as a callable command."""
        with self.stdoutIO() as s:
            exec(data)
        return s.getvalue()

    def set_input(self, text):  # type: (str) -> None
        """Set input from the nuke command."""
        self._input = text

    def execute(self):
        """Execute code in the main thread.

        If for some reason execution fails, method will fallback on the script
        editor execution mechanism.
        """
        try:
            self._output = nuke.executeInMainThreadWithResult(
                self._exec, self._input)
        except Exception:  # skipcq: PYL-W0703
            err = "executeInMainThread Error. Fallback on ScriptEditor for now."
            self.execution_error.emit(err)
            LOGGER.error(err)

            self.script_editor.set_input(self._input)
            self.script_editor.execute()
            self._output = self.script_editor.output()
            self.script_editor.restore_state()

    def output(self):  # type: () -> str
        """Get output from the nuke command."""
        return self._output

    def input(self):  # type: () -> str
        """Get output from the nuke command."""
        return self._input


class _PyController(_ExecuteInMainThread, object):
    """Controller class that deals with python code execution."""

    history = []

    def __init__(self, file):
        """Init method for the _PyController class.

        Args:
            file (str): file path of the file that is being executed.
        """
        _ExecuteInMainThread.__init__(self)
        self.settings = AppSettings()
        self._file = file

    @classmethod
    def _clear_history(cls):
        """Clear the history list."""
        del cls.history[:]

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
        list_size = [sys.getsizeof(n) for n in cls.history]

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

    def to_console(self):
        """Send input/output to nuke internal console."""
        if self.settings.get_bool('options/override_input_editor'):
            self.script_editor.set_input(self.input())
        if self.settings.get_bool('options/override_output_editor'):
            self._output_to_console()

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
                self.script_editor.set_output(output_text)
            else:
                self._append_output(output_text)
                self.script_editor.set_output(''.join(self.history))
                return
        else:
            self.script_editor.set_output(self.output())

        self._clear_history()


class _BlinkController(_ExecuteInMainThread, object):
    """Controller that deals with blink script execution code."""

    def __init__(self, file):
        """Init method for the _BlinkController class.

        Args:
            file (str):  file path of the file that is being executed.
        """
        _ExecuteInMainThread.__init__(self)
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


class _CopyNodesController(_ExecuteInMainThread, object):
    """Controller that deals with copy nodes execution code."""

    def __init__(self):
        """Init method for the _CopyNodesController class."""
        _ExecuteInMainThread.__init__(self)

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

    @staticmethod
    def _paste_nodes_wrapper(transfer_file):
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

        send_to_console = AppSettings().get_bool('options/mirror_to_script_editor')

        if isinstance(self._controller, _PyController) and send_to_console:
            self._controller.to_console()

        return self._controller.output()
