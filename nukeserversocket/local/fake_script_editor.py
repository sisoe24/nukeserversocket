# coding: utf-8
"""Fake emulation of the internal nuke script editor layout/widgets.

This is needed only for testing purposes so application can be run locally.
"""
from __future__ import print_function

import sys
import logging
import subprocess

from PySide2.QtGui import QKeyEvent, QKeySequence
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QLabel, QWidget, QSplitter, QTextEdit,
                               QMainWindow, QPushButton, QVBoxLayout,
                               QApplication, QPlainTextEdit)

from ..util import pyDecoder

LOGGER = logging.getLogger('nukeserversocket')


class OutputEditor(QTextEdit):
    """Widget placeholder for the output editor.

    Widget will be read only; the same as the one in Nuke.
    """

    def __init__(self):
        """Init method of the the OutputEditor class."""
        QTextEdit.__init__(self)
        self.setReadOnly(True)


class InputEditor(QPlainTextEdit):
    """Widget placeholder for the input editor.

    Once initialized, will automatically insert a simple string with a random
    number.
    """

    def __init__(self):
        """Init method of the the InputEditor class."""
        QPlainTextEdit.__init__(self)


class FakeScriptEditor(QWidget):
    """Widget placeholder for the entire script editor.

    This mimics the Nuke script editor layout widget position and objectName.
    The Script editor is divided by a QSplitter widget and contains a Output
    Editor and an Input editor. There is also a Run button that executes python
    code from the input editor and it sends the output to the Output editor.

    The objectName is the same as the nuke's script editor so it can be found
    by the Controller class: "uk.co.thefoundry.scripteditor.1".
    """

    def __init__(self, object_name='uk.co.thefoundry.scripteditor.1'):
        """Init method of the the FakeScriptEditor class."""
        QWidget.__init__(self)
        self.setMaximumHeight(300)
        LOGGER.debug('FakeScriptEditor :: init')
        self.setObjectName(object_name)

        self.run_btn = QPushButton('Run')
        self.run_btn.setToolTip('Run the current script')
        self.run_btn.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Return))
        self.run_btn.clicked.connect(self.run_code)

        self.input_console = InputEditor()

        self.output_console = OutputEditor()

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.addWidget(self.output_console)
        self.splitter.addWidget(self.input_console)

        _layout = QVBoxLayout()
        _layout.addWidget(QLabel('Script Editor emulation'))
        _layout.addWidget(self.run_btn)
        _layout.addWidget(self.splitter)
        self.setLayout(_layout)

        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Event filter to intercept the shortcut.

        This is only needed for testing. When the run button is not found, will
        fallback on shortcut to execute the code.
        """
        if (
            isinstance(event, QKeyEvent)
            and event.modifiers() == Qt.CTRL
            and event.key() == Qt.Key_Return
        ):
            self.run_code()
            event.accept()
            return True
        return super(FakeScriptEditor, self).eventFilter(obj, event)

    def run_code(self):
        """Execute python code from the input_console editor.

        Code is executed using `subprocess.check_output` which is not the most
        safe.

        Raises:
            subprocess.CalledProcessError: when failing to execute the code.
        """
        code = self.input_console.toPlainText()

        # when executing from SendNodesClient, code will be just a nuke command
        # with a path inside, so skip subprocess.
        if 'nuke.nodePaste' not in code:
            try:
                code = subprocess.check_output([sys.executable, '-c', code])
                code = pyDecoder(code)
            except subprocess.CalledProcessError:
                LOGGER.error('Error executing code: -> %s <-', code)
                return
        self.output_console.setPlainText(code)


class MainWindow(QMainWindow):
    """Main class needed when testing the editor in standalone mode."""

    def __init__(self):
        """Init method of the MainWindow class."""
        QMainWindow.__init__(self)

        self.script_editor = FakeScriptEditor()
        self.setCentralWidget(self.script_editor)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.script_editor.run_btn.click()
    app.exec_()
