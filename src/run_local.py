"""Run application locally outside Nuke."""
# coding: utf-8
from __future__ import print_function

import sys
import logging

from random import randint

from PySide2.QtWidgets import (
    QApplication,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .widgets import FakeScriptEditor
from .main import MainWindowWidget, MainWindow


LOGGER = logging.getLogger('NukeServerSocket.runapp')


class SecondFakeScriptEditor(QWidget):
    """Second fake script editor class.

    I wanted to test what happens when a second script editor gets created, and
    the other gets deleted.
    """

    def __init__(self, se1):
        """Init method for the SecondFakeScriptEditor class."""
        QWidget.__init__(self)
        self.se1 = se1
        self.se2 = FakeScriptEditor('uk.co.thefoundry.scripteditor.2')

        delete_btn = QPushButton('Delete Editor')
        delete_btn.clicked.connect(self.delete_widget)

        _layout = QVBoxLayout()
        _layout.addWidget(delete_btn)
        _layout.addWidget(self.se2)

        self.setLayout(_layout)

    def delete_widget(self):
        """Delete the script editor1."""
        print('delete editor.1')
        self.se1.deleteLater()


class _MainWindowWidget(QWidget):
    """Main window widget that holds the main app and the fake script editor."""

    def __init__(self):
        """Init method for the _MainWindowWidget class."""
        QWidget.__init__(self)
        LOGGER.debug('RUN APP :: INIT')

        se_name = 'uk.co.thefoundry.scripteditor.1'
        self.script_editor = FakeScriptEditor(se_name)
        self.script_editor.input_console.setPlainText(
            "print('Hello From Fake SE %s'.upper())" % randint(1, 50))
        self.main_app = MainWindowWidget()

        _layout = QVBoxLayout()
        _layout.addWidget(self.main_app)
        _layout.addWidget(self.script_editor)
        # _layout.addWidget(SecondFakeScriptEditor(self.script_editor))
        self.setLayout(_layout)

    def _auto_test(self):
        """Auto run simple test."""
        self.main_app.connect_btn.click()
        self.script_editor.run_btn.click()
        self.main_app.test_btn.click()


class _MainWindow(MainWindow):
    """Main Window that inherits from main.py.

    This is to add some extra functionality when testing locally, like screen
    position.
    """

    def __init__(self):
        """Init method for the _MainWindow class."""
        MainWindow.__init__(self, main_widget=_MainWindowWidget)
        self.setWindowTitle('NukeServerSocket Test')

        # personal monitor loc for rapid testing
        screen_loc = {
            'hp': {'x': -1077.296875, 'y': -5.31640625}
        }
        self.setGeometry(screen_loc['hp']['x'],
                         screen_loc['hp']['y'],
                         1080, 1980)


class MyApplication(QApplication):
    """Custom QApplication class."""

    def __init__(self, *args):
        """Init method for the MyApplication class."""
        super(MyApplication, self).__init__(*args)
        self.window = _MainWindow()
        self.window.show()


if __name__ == '__main__':

    app = MyApplication(sys.argv)
    app.exec_()
