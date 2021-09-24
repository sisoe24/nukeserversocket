# coding: utf-8
from __future__ import print_function

import logging

from abc import abstractmethod, ABCMeta, abstractproperty

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

    @classmethod
    def init_editor(cls):
        """Initialize NukeScriptEditor properties"""
        LOGGER.debug('Initialize getting Nuke Script Editor')
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
            RuntimeWarning: if script editor was not found
        """
        # .topLevelWidgets() is a smaller list but SE is not always there
        for widget in QApplication.allWidgets():

            # TODO: user should be able to decide which SE to use
            if 'scripteditor.1' in widget.objectName():
                return widget

        # XXX: can the script editor not exists?
        # TODO: don't like the traceback but probably will never be called anyway
        raise RuntimeWarning(
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

    def execute(cls):
        """Execute code inside Nuke Script Editor.

        Check if run_button exists otherwise simulate shortcut press.
        """
        try:
            cls.run_button.click()
        except AttributeError:
            cls._execute_shortcut()
