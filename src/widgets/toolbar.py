"""Toolbar widget module."""
# coding: utf-8
from __future__ import print_function

from PySide2.QtCore import QSize, Qt
from PySide2.QtWidgets import QAction, QDialog, QToolBar, QVBoxLayout

from .settings_widget import SettingsWidget
from .about_widget import AboutWidget

# TODO: create a abstract class for the floating widget


class FloatingDialog(QDialog):
    """Create a floating widget based on the QDialog class."""

    def __init__(self, title, obj_name, widget, parent=None):
        """Init method for a Floating Window widget.

        Create a floating window widget based on the QDialog class.

        Args:
            title (str): title of the window.
            obj_name (str): object name of the widget.
            widget (QWidget): A QWidget to add inside the QDialog layout.
            parent (QWidget, optional): A QWidget to set as the parent.
            Defaults to None.
        """
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
    """Custom QToolBar class."""

    def __init__(self):
        """Init method for the ToolBar class."""
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
        """Check if dialog widget exists already.

        If yes then raise the window and set focus.

        Args:
            obj_name (str): objectName of the widget to search for

        Returns:
            bool: True if found and raised False otherwise
        """
        for widget in self.children():
            if widget.objectName() == obj_name:
                widget.setFocus(Qt.PopupFocusReason)
                widget.raise_()
                widget.activateWindow()
                return True
        return False

    def _show_dialog(self, title, obj_name, widget):
        """Spawn a dialog widget.

        If dialog widget is already visible then do nothing.

        Args:
            title (str): title of the dialog widget
            obj_name (str): object name for the new dialog widget
            widget (QWidget): a widget to insert inside the dialog widget.

        Returns:
            QDialog | str: QDialog if widget doesn't exists, str if if does.
        """
        if not self._dialog_exists(obj_name):
            dialog = FloatingDialog(title=title, obj_name=obj_name,
                                    widget=widget, parent=self)
            dialog.show()
            return dialog

        return 'Already active'
