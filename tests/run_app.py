# coding: utf-8
from __future__ import print_function

import sys

from PySide2 import QtTest

from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QWidget,
    QStatusBar
)

from src.widgets import FakeScriptEditor, ToolBar
from src.main import MainWindowWidget

# personal monitor loc screen for rapid testing
screen_loc = {
    'hp': {
        'x': -1077.296875,
        'y': -5.31640625
    }
}


class TestMainwindowWidgets(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self)

        self.script_editor = FakeScriptEditor()
        self.main_app = MainWindowWidget(parent)

        _layout = QVBoxLayout()
        _layout.addWidget(self.main_app)
        _layout.addWidget(self.script_editor)
        self.setLayout(_layout)

        self.main_app.connect_btn.click()
        self.script_editor.run_btn.click()
        self.main_app.test_btn.click()


class TestMainWindow(QMainWindow):
    def __init__(self, *args, **kwargs):
        QMainWindow.__init__(self)
        self.setWindowTitle('NukeServerSocket Test')
        self.setGeometry(screen_loc['hp']['x'],
                         screen_loc['hp']['y'],
                         1080, 1980)

        toolbar = ToolBar()
        self.addToolBar(toolbar)

        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        try:
            main_window = TestMainwindowWidgets(self)
        except Exception as err:
            print("err :", err)
        else:
            self.setCentralWidget(main_window)


if __name__ == '__main__':

    app = QApplication(sys.argv)
    window = TestMainWindow()
    window.show()
    app.exec_()
