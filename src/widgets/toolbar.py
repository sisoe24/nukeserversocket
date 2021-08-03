# coding: utf-8
from __future__ import print_function

from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QToolBar, QWhatsThis

from .options import OptionsDialog


class ToolBar(QToolBar):
    def __init__(self):
        QToolBar.__init__(self)
        self.setIconSize(QSize(15, 15))
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setMovable(False)

        self.setStyleSheet('''color: white;''')
        self._initial_style = self.styleSheet()

        self.open_settings = QAction('Settings', self)
        self.open_settings.triggered.connect(self.show_settings)
        self.addAction(self.open_settings)

        # XXX: for some unknown reason, older pyside2 cannot create a whatsthis instance
        # even though is still a class
        # if nuke.env['NukeVersionMajor'] == 11:
        #     _whats_this = QWhatsThis
        # else:
        #     _whats_this = QWhatsThis()

        # self._help_button = _whats_this.createAction(self)
        # self._help_button.setIcon(QIcon(':/icons/question'))

    def show_settings(self):

        for widget in self.children():
            if widget.objectName() == 'OptionsDialog':
                widget.setFocus(Qt.PopupFocusReason)
                widget.raise_()
                widget.activateWindow()
                return

        options = OptionsDialog(self)
        options.show()
