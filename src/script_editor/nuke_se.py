# coding: utf-8
from __future__ import print_function

import logging
from functools import wraps

from abc import abstractmethod, ABCMeta, abstractproperty

import shiboken2
from PySide2.QtCore import Qt
from PySide2.QtTest import QTest

from PySide2.QtWidgets import (
    QPushButton,
    QSplitter,
    QPlainTextEdit,
    QTextEdit,
    QApplication,
    QWidget
)


LOGGER = logging.getLogger('NukeServerSocket.get_script_editor')


class BaseScriptEditor(object):
    """Abstract class for the BaseScriptEditor implementation.

    This could potentially be used for base interface when implementing other
    application scripts editors like Maya.
    """
    __metaclass__ = ABCMeta

    # TODO: input/output widget should be a method ?

    @abstractmethod
    def execute(self):
        pass

    @abstractproperty
    def input_widget(self):
        pass

    @abstractproperty
    def output_widget(self):
        pass


editors_widgets = {}


def editor_cache(func):
    """Cache nuke script editor widgets.

    If object becomes invalid (eg. gets out of scope and deleted), will search
    for it again and re add it to the cache.
    """

    @wraps(func)
    def widget():
        """This wrapper is for the get widget method"""
        return func()

    def inner(*args, **kwargs):

        if (
            widget not in editors_widgets or
            not shiboken2.isValid(editors_widgets[widget])
        ):
            editors_widgets[widget] = func(*args, **kwargs)

        return editors_widgets[widget]

    return inner


class NukeScriptEditor(BaseScriptEditor):
    """Nuke Internal Script Editor widget.

    The class get initialized when The NukeServerSocket gets first created. Then
    will save all of the Nuke internal script editor widgets inside class properties
    so it can get called later without having to search each widget again.

    Note: This could break anytime if Foundry changes something.
    # TODO: Should invest some time to find a better way.
    """

    def __init__(self):
        """Initialize NukeScriptEditor properties"""
        LOGGER.debug('Initialize Nuke Script Editor')

        self._script_editor = self.get_script_editor()

        self._console = self.get_console()
        self._output_widget = self.get_output_widget()
        self._input_widget = self.get_input_widget()

        self._run_button = self.get_run_button()

    @property
    def script_editor(self):
        return self._script_editor

    @property
    def input_widget(self):
        return self._input_widget

    @property
    def output_widget(self):
        return self._output_widget

    @editor_cache
    def get_script_editor(self, editor='scripteditor.1'):  # type: (str) -> QWidget
        """Get script editor widget.

        Returns:
            QWidget: Nuke Internal script editor widget

        Raises:
            RuntimeWarning: if script editor was not found
        """
        # .topLevelWidgets() is a smaller list but SE is not always there
        for widget in QApplication.allWidgets():

            # TODO: user should be able to decide which SE to use
            if editor in widget.objectName():
                return widget

        # XXX: can the script editor not exists?
        # TODO: don't like the traceback but probably will never be called anyway
        raise RuntimeWarning(
            'NukeServerSocket: Script Editor panel not found! '
            'Please create one and reload the panel.'
        )

    @editor_cache
    def get_console(self):
        return self.get_script_editor().findChild(QSplitter)

    @editor_cache
    def get_output_widget(self):
        return self.get_console().findChild(QTextEdit)

    @editor_cache
    def get_input_widget(self):
        return self.get_console().findChild(QPlainTextEdit)

    @editor_cache
    def get_run_button(self, tooltip='Run'):  # type: (str) -> QPushButton | None
        """Get the run button from the script editor.

        Returns:
            (QPushButton | None): Return the QPushButton otherwise None
        """
        # TODO: if fail tooltip search for list position
        for button in self.get_output_widget().findChildren(QPushButton):
            # The only output_widget identifier of the button is a tooltip or
            # a fix position in list: n
            if tooltip in button.toolTip():
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

    def execute(self):
        """Execute code inside Nuke Script Editor.

        Check if run_button exists otherwise simulate shortcut press.
        """
        try:
            self.run_button.click()
        except AttributeError:
            self._execute_shortcut()
