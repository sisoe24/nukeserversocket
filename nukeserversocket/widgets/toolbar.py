"""Toolbar widget module."""
# coding: utf-8

from PySide2.QtWidgets import QMenu, QAction, QWidget, QToolBar, QToolButton

from .about_widget import AboutWidget
from .settings_widget import SettingsWidget


def show_window(widget):  # type:(QWidget) -> None
    """Show a widget window.

    If widget is already visible then regain focus.

    Args:
        widget (QWidget): a widget to insert inside the dialog widget.
    """
    widget.show()
    widget.activateWindow()
    widget.raise_()


class ToolBar(QToolBar):
    """Custom QToolBar class."""

    def __init__(self):
        """Init method for the ToolBar class."""
        QToolBar.__init__(self)
        self.setMovable(False)
        self.setStyleSheet('color: white;')
        self.add_widget(title='Help', widget=AboutWidget())
        self.add_widget(title='Settings', widget=SettingsWidget())

    def add_menu(self, title, menu):  # type: (str, QMenu)-> None
        """Set up a menu stile QtoolButton inside the Toolbar."""
        btn = QToolButton()
        btn.setText(title)
        btn.setPopupMode(QToolButton.InstantPopup)
        btn.setMenu(menu)
        self.addWidget(btn)

    def add_widget(self, title, widget):  # type: (str, QWidget) -> QAction
        """Set up action for toolbar.

        Method will set up a QAction and connect its trigger signal to show a
        widget window.

        Args:
            title (str): title of the window widget.
            widget (QWidget): QWidget to show.

        Returns:
            QAction: The QAction created.
        """
        widget.setWindowTitle(title)
        action = QAction(title, self)
        action.triggered.connect(lambda: show_window(widget))
        self.addAction(action)
        return action
