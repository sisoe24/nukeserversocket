# coding: utf-8
from __future__ import print_function

from PySide2.QtCore import QSize, Qt
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QAction, QDialog, QToolBar, QVBoxLayout

from .settings_widget import SettingsWidget
from .about_widget import AboutWidget


class FloatingDialog(QDialog):
    def __init__(self, title, obj_name, widget, parent=None):
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        self.setObjectName(obj_name)

        _layout = QVBoxLayout()
        _layout.addWidget(widget())

        self.setLayout(_layout)

    def closeEvent(self, event):
        """When close event triggers destroy the widget."""
        self.deleteLater()


class ToolBar(QToolBar):
    def __init__(self):
        QToolBar.__init__(self)
        self.setIconSize(QSize(15, 15))
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setMovable(False)

        self.setStyleSheet('color: white;')
        self._initial_style = self.styleSheet()

        self._setup_settings_action()
        self._setup_about_action()

    def _setup_settings_action(self):
        return self._setup_action(
            title='Settings', obj_name='SettingsDialog', widget=SettingsWidget
        )

    def _setup_about_action(self):
        return self._setup_action(
            title='About', obj_name='AboutDialog', widget=AboutWidget
        )

    def _setup_action(self, title, obj_name, widget):
        action = QAction(title, self)
        self.addAction(action)

        action.triggered.connect(
            lambda: self._show_dialog(title, obj_name, widget)
        )
        return action

    def _dialog_exists(self, obj_name):
        """Check if the widget is already present. If yes then raise the window set focus

        Args:
            obj_name (str): objectName of the widget to search for

        Returns:
            bool: true if found and raised false otherwise
        """
        for widget in self.children():
            if widget.objectName() == obj_name:
                widget.setFocus(Qt.PopupFocusReason)
                widget.raise_()
                widget.activateWindow()
                return True
        return False

    def _show_dialog(self, title, obj_name, widget):
        if not self._dialog_exists(obj_name):
            dialog = FloatingDialog(title=title, obj_name=obj_name,
                                    widget=widget, parent=self)
            dialog.show()
            return dialog

        return 'Already active'
