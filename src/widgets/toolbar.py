"""Toolbar widget module."""
# coding: utf-8

import logging

from PySide2.QtCore import QSize, Qt
from PySide2.QtWidgets import (
    QMenu,
    QToolButton,
    QAction,
    QDialog,
    QToolBar,
    QVBoxLayout,
    QWidget
)

from .settings_widget import SettingsWidget
from .about_widget import AboutWidget

LOGGER = logging.getLogger('NukeServerSocket.toolbar')


_dialog_widgets_cache = {}


class FloatingDialog(QDialog):
    """Create a floating widget based on the QDialog class."""

    def __init__(self, title, widget, parent=None):  # type:(str, QWidget, None) -> None
        """Init method for a Floating Window widget.

        Create a floating window widget based on the QDialog class.

        Args:
            title (str): title of the window.
            widget (QWidget): A QWidget to add inside the QDialog layout.
            parent (QWidget, optional): A QWidget to set as the parent.
            Defaults to None.
        """
        QDialog.__init__(self, parent)
        self.setWindowTitle(title)
        _dialog_widgets_cache[widget] = self

        _layout = QVBoxLayout()
        _layout.setContentsMargins(0, 0, 0, 0)
        _layout.addWidget(widget)

        self.setLayout(_layout)

    def closeEvent(self, event):
        """Close the widget."""
        self.close()


class ToolBar(QToolBar):
    """Custom QToolBar class."""

    def __init__(self):
        """Init method for the ToolBar class."""
        QToolBar.__init__(self)
        self.setIconSize(QSize(15, 15))
        self.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.setMovable(False)

        self.setStyleSheet('color: white;')
        self.add_float_widget(title='Settings', widget=SettingsWidget())
        self.add_float_widget(title='Help', widget=AboutWidget())

    def add_menu(self, title, menu):  # type:(str, QMenu) -> None
        btn = QToolButton()
        btn.setText(title)
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setMenu(menu)
        self.addWidget(btn)

    def add_float_widget(self, title, widget):  # type:(str, QWidget) -> QAction
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
        action.triggered.connect(lambda: self._show_dialog(title, widget))
        self.addAction(action)
        return action

    def _show_dialog(self, title, widget):  # type:(str, QWidget) -> QDialog
        """Spawn a dialog widget.

        If dialog widget is already visible then regain focus.

        Args:
            title (str): title of the floating dialog window.
            widget (QWidget): a widget to insert inside the dialog widget.

        Returns:
            QDialog : QDialog
        """
        dialog = _dialog_widgets_cache.get(widget)

        if not dialog:
            dialog = FloatingDialog(title, widget, parent=self)

        dialog.show()
        dialog.activateWindow()
        dialog.raise_()

        return dialog
