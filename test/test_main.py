# coding: utf-8
from __future__ import print_function
import sys

from PySide2.QtWidgets import (
    QMainWindow,
    QApplication,
    QVBoxLayout,
    QWidget
)

from PySide2 import QtTest

from NukeServerSocket import main
from NukeServerSocket.test import ScriptEditor
from NukeServerSocket.src.main import MainWindowWidget

screen_loc = {
    'hp': {
        'x': -1077.296875,
        'y': -5.31640625
    }
}


class TestScriptEditor(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)

        self.main_app = MainWindowWidget(parent)
        self.script_editor = ScriptEditor()

        _layout = QVBoxLayout()
        _layout.addWidget(self.main_app)
        _layout.addWidget(self.script_editor)
        self.setLayout(_layout)

        self.main_app.connect_btn.click()
        self.script_editor.run_btn.click()
        self.main_app.test_btn.click()


class TestMainWindow(main.MainWindow):
    def __init__(self, *args, **kwargs):
        main.MainWindow.__init__(self)
        self.setWindowTitle('Test')
        self.setGeometry(screen_loc['hp']['x'],
                         screen_loc['hp']['y'],
                         1080, 1980)

        try:
            main_window = TestScriptEditor(self)
        except Exception as err:
            pass
        else:
            self.setCentralWidget(main_window)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    app.exec_()
