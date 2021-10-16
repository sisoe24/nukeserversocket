# coding: utf-8
"""Fake emulation of the internal nuke script editor layout/widgets."""
from __future__ import print_function

import sys
import random
import logging
import subprocess

from PySide2.QtCore import Qt
from PySide2.QtGui import QKeySequence, QKeyEvent

from PySide2.QtWidgets import (
    QVBoxLayout,
    QWidget,
    QPlainTextEdit,
    QSplitter,
    QTextEdit,
    QPushButton,
    QApplication, QMainWindow
)

from src.script_editor.nuke_se_controllers import LOGGER

LOGGER = logging.getLogger('NukeServerSocket.fakescripteditor')


class OutputEditor(QTextEdit):
    def __init__(self):
        QTextEdit.__init__(self)
        LOGGER.debug('OutputEditor :: init')
        self.setReadOnly(True)


class InputEditor(QPlainTextEdit):
    def __init__(self):
        QPlainTextEdit.__init__(self)
        LOGGER.debug('InputEditor :: init')
        r = random.randint(1, 50)
        self.setPlainText("print('Hello From Internal SE %s')" % r)


class FakeScriptEditor(QWidget):
    def __init__(self, object_name='uk.co.thefoundry.scripteditor.1'):
        QWidget.__init__(self)
        LOGGER.debug('FakeScriptEditor :: init')
        self.setObjectName(object_name)

        self.run_btn = QPushButton('Run')
        self.run_btn.setToolTip('Run the current')
        self.run_btn.setShortcut(QKeySequence(Qt.CTRL + Qt.Key_Return))
        self.run_btn.clicked.connect(self.run_code)

        self.input_console = InputEditor()

        self.output_console = OutputEditor()

        self.splitter = QSplitter()
        self.splitter.setOrientation(Qt.Vertical)
        self.splitter.addWidget(self.output_console)
        self.splitter.addWidget(self.input_console)

        _layout = QVBoxLayout()
        _layout.addWidget(self.run_btn)
        _layout.addWidget(self.splitter)
        self.setLayout(_layout)

        self.installEventFilter(self)

    def eventFilter(self, obj, event):
        if isinstance(event, QKeyEvent):
            if event.modifiers() == Qt.CTRL and event.key() == Qt.Key_Return:
                # print('shortcut pressed')
                self.run_code()
                event.accept()
                return True
        return super(FakeScriptEditor, self).eventFilter(obj, event)

    def run_code(self):
        code = self.input_console.toPlainText()
        if 'nuke.nodePaste' not in code:
            try:
                code = subprocess.check_output(
                    ['python', '-c', code], encoding='utf-8')
            except subprocess.CalledProcessError:
                LOGGER.error('Error executing code: -> %s <-', code)
                return
        self.output_console.setPlainText(code)


class MainWindow(QMainWindow):
    def __init__(self):
        QMainWindow.__init__(self)

        self.script_editor = FakeScriptEditor()
        self.setCentralWidget(self.script_editor)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    window.script_editor.run_btn.click()
    app.exec_()
