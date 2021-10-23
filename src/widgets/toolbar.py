"""Toolbar widget module."""
# coding: utf-8
from __future__ import print_function

import logging

from PySide2.QtCore import QSize, Qt
from PySide2.QtWidgets import QAction, QDialog, QToolBar, QVBoxLayout, QWidget

from .settings_widget import SettingsWidget
from .about_widget import AboutWidget

LOGGER = logging.getLogger('NukeServerSocket.toolbar')


class FloatingDialog(QDialog):
    """Create a floating widget based on the QDialog class."""

    def __init__(self, widget, parent=None):  # type: (QWidget, None) -> None
        """Init method for a Floating Window widget.

        Create a floating window widget based on the QDialog class.

        Args:
            widget (QWidget): A QWidget to add inside the QDialog layout.
            parent (QWidget, optional): A QWidget to set as the parent.
            Defaults to None.
        """
        QDialog.__init__(self, parent)

        obj_name = widget.objectName()
        self.setWindowTitle(obj_name.replace('Widget', ''))
        self.setObjectName(obj_name)

        _layout = QVBoxLayout()
        _layout.addWidget(widget)

        self.setLayout(_layout)

    def closeEvent(self, event):
        """When close event triggers destroy the widget."""
        LOGGER.debug('FloatingDialog :: delete widget. %s', event)
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

        self._setup_action(title='Settings', widget=SettingsWidget)
        self._setup_action(title='About', widget=AboutWidget)

    def _setup_action(self, title, widget):
        """Set up action for toolbar.

        Method will set up a QAction and connect its trigger signal to spawn
        the floating dialog.

        Args:
            title (str): name of the action.
            widget (QWidget): QWidget to use as a floating dialog.

        Returns:
            QAction: The QAction created.
        """
        action = QAction(title, self)
        action.triggered.connect(lambda: self._show_dialog(widget))
        self.addAction(action)
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

    def _show_dialog(self, widget):  # type(QWidget) -> QDialog | str
        """Spawn a dialog widget.

        If dialog widget is already visible then do nothing.

        Args:
            widget (QWidget): a widget to insert inside the dialog widget.

        Returns:
            QDialog | str: QDialog if widget doesn't exists, str if if does.
        """
        widget = widget()

        obj_name = widget.objectName()
        if not obj_name:
            raise RuntimeWarning(
                'Widget must have an object name before spawning the QDialog')

        if not self._dialog_exists(obj_name):
            dialog = FloatingDialog(widget, parent=self)
            dialog.show()
            return dialog

        return 'Already active'
