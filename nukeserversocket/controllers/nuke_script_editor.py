"""Module that deals with the Nuke Script Editor widget."""
# coding: utf-8

import logging
from abc import ABCMeta, abstractmethod
from functools import wraps

import shiboken2
from PySide2.QtCore import Qt
from PySide2.QtTest import QTest
from PySide2.QtWidgets import (QWidget, QSplitter, QTextEdit, QPushButton,
                               QApplication, QPlainTextEdit)

LOGGER = logging.getLogger('nukeserversocket')


class BaseScriptEditor(object):
    """Abstract class for the BaseScriptEditor implementation.

    This could potentially be used for base interface when implementing other
    application scripts editors like Maya.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def execute(self):
        """Execute code from the input editor."""
        raise NotImplementedError

    @property
    @abstractmethod
    def input_widget(self):
        """Input Editor widget."""
        raise NotImplementedError

    @property
    @abstractmethod
    def output_widget(self):
        """Output Editor widget."""
        raise NotImplementedError


editors_widgets = {}

# TODO: Re evaluate if caching the widgets still make sense. Maybe having a
# singleton NukeScriptEditor class is enough.


def editor_cache(func):
    """Cache nuke script editor widgets.

    If object becomes invalid (eg. gets out of scope and deleted), will search
    for it again and re add it to the cache.
    """

    @wraps(func)
    def widget():
        """Widget wrapper to call when validating cache."""
        return func()

    def inner(*args, **kwargs):
        """Check if widget is already cached and if is a valid qt object."""
        if (
            widget not in editors_widgets or
            not shiboken2.isValid(editors_widgets[widget])
        ):
            result = func(*args, **kwargs)

            # if result is empty do not add to cache and search again next time
            if not result:
                return result

            editors_widgets[widget] = result

        return editors_widgets[widget]

    return inner


class NukeScriptEditor(BaseScriptEditor):
    """Nuke Internal Script Editor widget.

    When class is initialized will automatically search for the script editors
    widget and cache them, to avoid searching for them at each code execution.

    Properties:
        script_editor (QWidget): the script editor QWidget.
        output_editor (QTextEdit): the output editor from the script editor.
        input_editor (QTextEdit): the input editor from the script editor.

    Methods:
        execute: execute the code.

    Note: This could break anytime if API changes.
    """

    def __init__(self):
        """Init method for the NukeScriptEditor class.

        Start searching for the script editor widgets and save them inside its
        attribute.
        """
        LOGGER.debug('Initialize Nuke Script Editor')

        self._script_editor = self._find_script_editor()

        self._output_widget = self._find_output_widget()
        self._input_widget = self._find_input_widget()

        self._run_button = self._find_run_button()

    @property
    def script_editor(self):  # type: () -> QWidget
        """Get the script editor widget."""
        return self._script_editor

    @property
    def input_widget(self):  # type: () -> QPlainTextEdit
        """Get the input widget (QPlainTextEdit) object."""
        return self._input_widget

    @property
    def output_widget(self):  # type: () -> QTextEdit
        """Get the output widget (QTextEdit) object."""
        return self._output_widget

    def execute(self):
        """Execute code inside Nuke Script Editor.

        Check if run_button exists otherwise simulate shortcut press.
        """
        try:
            self._run_button.click()
        except AttributeError:
            self._execute_shortcut()

    @staticmethod
    @editor_cache
    def _find_script_editor(editor='scripteditor.1'):  # type: (str) -> QWidget
        """Get script editor widget.

        Returns:
            QWidget: Nuke Internal script editor widget

        Raises:
            RuntimeWarning: if script editor was not found
        """
        # .topLevelWidgets() is a smaller list but SE is not always there
        for widget in QApplication.allWidgets():

            # XXX: should the user be able to decide which SE to use?
            if editor in widget.objectName():
                return widget

        # XXX: can the script editor not exists?
        raise RuntimeWarning(
            'NukeServerSocket: Script Editor panel not found! '
            'Please create one and reload the panel.'
        )

    @editor_cache
    def _find_console(self):
        """Find the console widget from its parent widget."""
        return self._find_script_editor().findChild(QSplitter)

    @editor_cache
    def _find_output_widget(self):
        """Find the output editor widget from its parent widget."""
        return self._find_console().findChild(QTextEdit)

    @editor_cache
    def _find_input_widget(self):
        """Find the input editor widget from its parent widget."""
        return self._find_console().findChild(QPlainTextEdit)

    @editor_cache
    def _find_run_button(self):  # type: (str) -> QPushButton | None
        """Find the run button from the script editor.

        The only way to grab the button is by searching its tooltip or by its
        position in the list of buttons from the parent widget.

        Args:
            tooltip (str): button tooltip to search for. Default to: 'Run'.

        Returns:
            (QPushButton | None): Return the QPushButton otherwise None
        """
        # TODO: if fail tooltip search for list position
        for button in self._find_script_editor().findChildren(QPushButton):
            if button.toolTip() == 'Run the current script':
                return button

        # XXX: can the button not be found?
        return None

    def _execute_shortcut(self):
        """Simulate shortcut CTRL + Return for running script.

        This method is currently used as a fallback in case the execute button
        couldn't be found.
        """
        # XXX: could the user change the shortcut? if yes then what?
        QTest.keyPress(self.input_widget, Qt.Key_Return, Qt.ControlModifier)
        QTest.keyRelease(self.input_widget, Qt.Key_Return, Qt.ControlModifier)


class ScriptEditorController():
    """Manipulate internal script editor."""

    def __init__(self):
        """Init method for the ScriptEditorController class.

        Method will also initialize the NukeScriptEditor class.
        """
        self.script_editor = NukeScriptEditor()

        self.initial_input = None
        self.initial_output = None

        self._save_state()

    def _save_state(self):
        """Save initial state of the editor before any modification."""
        self.initial_input = self.script_editor.input_widget.toPlainText()
        self.initial_output = self.script_editor.output_widget.toPlainText()

    def set_input(self, text):  # type: (str) -> None
        """Set text for the input editor.

        Arguments
            (str) text - text to insert.
        """
        self.script_editor.input_widget.setPlainText(text)

    def set_output(self, text):  # type: (str) -> None
        """Set text for the output editor.

        Arguments
            (str) text - text to insert.
        """
        self.script_editor.output_widget.setPlainText(text)

    def input(self):  # type: () -> str
        """Get text input text from the nuke internal script editor."""
        return self.script_editor.input_widget.document().toPlainText()

    def output(self):  # type: () -> str
        """Get text output text from the nuke internal script editor."""
        return self.script_editor.output_widget.document().toPlainText()

    def clear_input(self):
        """Delete all the text in the input text editor."""
        self.script_editor.input_widget.document().clear()

    def clear_output(self):
        """Delete all the text in the output text editor."""
        self.script_editor.output_widget.document().clear()

    def execute(self):
        """Execute code from script editor."""
        self.script_editor.execute()

    def restore_input(self):
        """Restore initial input text."""
        self.script_editor.input_widget.setPlainText(self.initial_input)

    def restore_output(self):
        """Restore initial output text."""
        self.script_editor.output_widget.setPlainText(self.initial_output)

    def restore_state(self):
        """Restore the initial text data of the editor."""
        self.restore_input()
        self.restore_output()
