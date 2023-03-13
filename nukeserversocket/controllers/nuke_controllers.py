"""Module for the nuke script editor controller classes."""
# coding: utf-8

import os
import re
import sys
import json
import logging
import contextlib
from textwrap import dedent

from PySide2.QtCore import Signal, QObject

from ..util import insert_time
from ..settings import AppSettings
from ..local.mock import nuke
from .nuke_script_editor import ScriptEditorController
from ..network.data_to_code import DataCode

if sys.version_info > (3, 0):
    import io as stringIO
else:
    import StringIO as stringIO

LOGGER = logging.getLogger('nukeserversocket')

# TODO: Create abstract code controller class


class _ExecuteCodeController(QObject):
    """Execute code inside Nuke.

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
            stdout = stringIO.StringIO()
        sys.stdout = stdout
        yield stdout
        sys.stdout = old

    def _exec(self, data):  # type: (str) -> str
        """Execute a string as a callable command."""
        try:
            with self.stdoutIO() as s:
                exec(data, {})  # skipcq: PYL-W0122
            return s.getvalue()
        except Exception as err:  # skipcq: PYL-W0703
            return 'An exception occurred running Nuke Internal engine: `%s`' % str(err)

    def set_input(self, text):  # type: (str) -> None
        """Set input for the nuke execution call."""
        self._input = text

    def execute(self):
        """Execute code in the main thread.

        If for some reason execution fails, fallback on the script editor
        mechanism.
        """
        if AppSettings().get_bool('code_execution_engine/nuke_internal', True):
            try:
                self._output = nuke.executeInMainThreadWithResult(
                    self._exec, self._input)
                LOGGER.debug('Execute engine :: Nuke Internal')
            except Exception:  # skipcq: PYL-W0703
                err = 'executeInMainThread Error. Fallback on ScriptEditor for now.'
                self.execution_error.emit(err)
                LOGGER.error(err)
                self._execute_script_editor()
        else:
            self._execute_script_editor()

    def _execute_script_editor(self):
        """Execute code from the internal script editor widget."""
        LOGGER.debug('Execute engine :: Script Editor')
        self.script_editor.set_input(self._input)
        self.script_editor.execute()
        self._output = self.script_editor.output()
        self.script_editor.restore_state()

    def output(self):  # type: () -> str
        """Get the output from the nuke execution call."""
        return self._output

    def input(self):  # type: () -> str
        """Get the input from the nuke execution call."""
        return self._input


class _PyController(_ExecuteCodeController, object):
    """Controller class that deals with python code execution."""

    history = []

    def __init__(self, file):
        """Init method for the _PyController class.

        Args:
            file (str): file path of the file that is being executed.
        """
        _ExecuteCodeController.__init__(self)
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

        Returns:
            (str) file - path of the file that is being executed or an empty string.
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
        """Format the output text to send to nuke internal console."""
        text = self._clean_output(text)
        file = self._show_file()

        output = '[Nuke Tools] %s \n%s' % (file, text)

        if self.settings.get_bool('options/show_unicode', True):
            # Arrow sign going down
            unicode = u'\u21B4'
            output = '[Nuke Tools] %s %s\n%s' % (file, unicode, text)

        return insert_time(output)

    def output(self):  # type: () -> str
        """Get a clean version of the output editor text."""
        return self._clean_output(super(_PyController, self).output())

    def to_console(self):
        """Send input/output to nuke internal console."""
        if self.settings.get_bool('options/override_input_editor'):
            self.script_editor.set_input(self.input())
        if self.settings.get_bool('options/override_output_editor'):
            self._output_to_console()

    def _output_to_console(self):
        """Output text to Nuke internal script editor console.

        The function is called only when `Output To Console` settings is True.
        It will format the text based on settings like Format Text and
        Clear Output settings.
        """
        if self.settings.get_bool('options/format_text', True):

            output_text = self._format_output(super(_PyController, self).output())

            if self.settings.get_bool('options/clear_output', True):
                self.script_editor.set_output(output_text)
            else:
                self._append_output(output_text)
                self.script_editor.set_output(''.join(self.history))
                return
        else:
            self.script_editor.set_output(self.output())

        self._clear_history()


class _BlinkController(_ExecuteCodeController, object):
    """Controller that deals with blink script execution code."""

    def __init__(self, file):
        """Init method for the _BlinkController class.

        Args:
            file (str): file path of the file that is being executed.
        """
        _ExecuteCodeController.__init__(self)
        self._file = file

    def output(self):  # type: () -> str
        """Override parent method `output`.

        Returns:
            (str): string literal: 'Recompiling'
        """
        return 'Recompiling'

    def set_input(self, text):  # type: (str) -> str
        """Override parent method `set_input`.

        Get the blinkscript command and insert it to the input widget.
        """
        text = self._blink_command(text)
        super(_BlinkController, self).set_input(text)

    def _blink_command(self, code):  # type: (str) -> str
        """Create the blinkscript command.

        The command checks for a blinkscript node and create one if needed.
        Then will execute the code using the blinkscript recompile button.

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


class _CopyNodesController(_ExecuteCodeController, object):
    """Controller that deals with copy nodes execution code."""

    def __init__(self):
        """Init method for the _CopyNodesController class."""
        _ExecuteCodeController.__init__(self)

    def output(self):  # type: () -> str
        """Override parent method.

        Returns:
            (str): string literal: 'Nodes received'.
        """
        return 'Nodes received.'

    def set_input(self, text):  # type: (str) -> str
        """Override parent method by executing the `nuke.nodePaste()` command.

        The method creates a file and writes the text argument received. Then
        it passes the file path to `nuke.nodePaste`.

        Args:
            text (str): the text to be set as input in the widget.
        """
        settings = AppSettings()
        transfer_file = settings.value('path/transfer_file')

        with open(transfer_file, 'w') as file:
            file.write(text)

        text = self._paste_nodes_command(transfer_file)
        super(_CopyNodesController, self).set_input(text)

    @staticmethod
    def _paste_nodes_command(transfer_file):
        """Create the `nuke.nodePaste` command.

        Args:
            transfer_file (str): the transfer_nodes.tmp file path.
        """
        return "nuke.nodePaste('{}')".format(transfer_file)


class CodeEditor(QObject):
    """Factory class for the script editor controllers."""

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
            self.controller = _BlinkController(file)

        elif file_ext == '.tmp':
            self.controller = _CopyNodesController()

        else:
            self.controller = _PyController(file)

    def execute(self):  # type: () -> str
        """Execute controller function.

        The function sets the controller input text and execute it. Once
        done, it will return the output and restore the script editor state.
        """
        self.controller.set_input(self.data.text)
        self.controller.execute()

        send_to_console = AppSettings().get_bool('options/mirror_to_script_editor')

        if isinstance(self.controller, _PyController) and send_to_console:
            self.controller.to_console()

        return self.controller.output()
