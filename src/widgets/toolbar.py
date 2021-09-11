# coding: utf-8
from __future__ import print_function

from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QDialog, QToolBar, QVBoxLayout

from .settings_widget import SettingsWidget
from .about_widget import AboutWidget


class FloatingDialog(QDialog):
    def __init__(self, title, object_name, widget, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        self.setObjectName(object_name)

        _layout = QVBoxLayout()
        _layout.addWidget(widget())

        self.setLayout(_layout)

    def closeEvent(self, event):
        """When close event triggers destroy the widget."""
        self.deleteLater()


class ToolBar(QToolBar):
    # TODO: should create a toolbar controller class?
    def __init__(self):
        QToolBar.__init__(self)
        self.setIconSize(QSize(15, 15))
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setMovable(False)

        self.setStyleSheet('''color: white;''')
        self._initial_style = self.styleSheet()

        self._open_settings = QAction('Settings', self)
        self._open_settings.triggered.connect(self._show_settings)
        self.addAction(self._open_settings)

        self._open_about = QAction('About', self)
        self._open_about.triggered.connect(self._show_about)
        self.addAction(self._open_about)

    def _dialog_exists(self, object_name):
        """Check if the widget is already present. If yes then raise the window set focus

        Args:
            object_name (str): objectName of the widget to search for

        Returns:
            bool: true if found and raised false otherwise
        """
        for widget in self.children():
            if widget.objectName() == object_name:
                widget.setFocus(Qt.PopupFocusReason)
                widget.raise_()
                widget.activateWindow()
                return True
        return False

    def _show_about(self):
        obj_name = 'AboutDialog'
        if not self._dialog_exists(obj_name):

            FloatingDialog(
                title='About',
                object_name=obj_name,
                widget=AboutWidget,
                parent=self
            ).show()

    def _show_settings(self):
        obj_name = 'SettingsDialog'
        if not self._dialog_exists(obj_name):

            FloatingDialog(
                title='Settings',
                object_name=obj_name,
                widget=SettingsWidget,
                parent=self
            ).show()
