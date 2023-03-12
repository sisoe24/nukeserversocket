"""Run application locally outside Nuke."""
# coding: utf-8
import os
import sys
import logging
from random import randint

from PySide2.QtWidgets import QWidget, QVBoxLayout, QApplication

from .mock import nuke
from ..main import MainWindow, MainWindowWidget
from ..widgets import FakeScriptEditor

LOGGER = logging.getLogger('nukeserversocket')


class NukeServerSocketLocal(QWidget):
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
        MainWindow.__init__(self, main_widget=NukeServerSocketLocal)
        self.setWindowTitle('NukeServerSocket Local - %s' % nuke.env['NukeVersionMajor'])
        if os.getenv('USERNAME', os.getenv('USER')) == 'virgil':
            self.setGeometry(1449.26171875, 602.8671875, 1080, 1980)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = _MainWindow()
    window.show()
    app.exec_()
