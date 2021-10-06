# coding: utf-8
from __future__ import print_function

import sys
import traceback

from PySide2 import QtTest
from PySide2.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QStatusBar
)

from src.widgets import FakeScriptEditor, ToolBar, ErrorDialog
from src.main import MainWindowWidget

# personal monitor loc screen for rapid testing
screen_loc = {
    'hp': {
        'x': -1077.296875,
        'y': -5.31640625
    }
}


class SecondFakeScriptEditor(QWidget):
    def __init__(self, se1):
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
        print('delete editor.1')
        self.se1.deleteLater()


class _MainwindowWidgets(QWidget):
    def __init__(self, parent=None):
        QWidget.__init__(self)

        self.script_editor = FakeScriptEditor(
            'uk.co.thefoundry.scripteditor.1')
        self.main_app = MainWindowWidget(parent)

        _layout = QVBoxLayout()
        _layout.addWidget(self.main_app)
        _layout.addWidget(self.script_editor)
        # _layout.addWidget(SecondFakeScriptEditor(self.script_editor))
        self.setLayout(_layout)

        # self.main_app.connect_btn.click()
        # self.script_editor.run_btn.click()
        # self.main_app.test_btn.click()


class _MainWindow(QMainWindow):
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
            self.main_window = _MainwindowWidgets(self)
        except Exception as err:
            print("err :", err, traceback.format_exc())
            ErrorDialog(err, self).show()
        else:
            self.setCentralWidget(self.main_window)


class MyApplication(QApplication):
    def __init__(self, *args):
        super().__init__(*args)
        self.window = _MainWindow()
        self.window.show()


if __name__ == '__main__':

    app = MyApplication(sys.argv)
    app.exec_()
