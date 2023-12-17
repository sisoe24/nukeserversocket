"""Toolbar widget module."""

from __future__ import annotations

from PySide2.QtCore import Slot
from PySide2.QtWidgets import (QLabel, QAction, QDialog, QWidget, QToolBar,
                               QFormLayout, QPushButton)

from .about import about
from .settings_ui import NssSettings


class HelpWidget(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('NukeServerSocket Help')

        form_layout = QFormLayout()
        for name, value in about().items():
            form_layout.addRow(f'{name.title()}:', QLabel(value))

        self.issues = self._button_factory('Issues')
        self.readme = self._button_factory('Readme')
        self.changelog = self._button_factory('Changelog')

        form_layout.addRow(self.readme)
        form_layout.addRow(self.changelog)
        form_layout.addRow(self.issues)
        self.setLayout(form_layout)

    def _button_factory(self, text: str) -> QPushButton:
        button = QPushButton(text)
        button.clicked.connect(lambda: self._on_open_link(text))
        return button

    @Slot(str)
    def _on_open_link(self, link: str):
        gitrepo = 'https://github.com/sisoe24/nukeserversocket'
        links = {
            'issues': f'{gitrepo}/issues',
            'changelog': f'{gitrepo}/blob/master/CHANGELOG.md',
            'readme': f'{gitrepo}/blob/master/README.md'
        }
        import webbrowser
        webbrowser.open(links[link.lower()])


def _show_window(widget: QWidget) -> None:
    """Show a widget window.

    If widget is already visible then regain focus.

    """
    widget.show()
    widget.activateWindow()
    widget.raise_()


class ToolBar(QToolBar):
    """Custom QToolBar class."""

    def __init__(self, parent=None):
        """Init method for the ToolBar class."""
        super().__init__(parent)
        self.setMovable(False)
        self.setStyleSheet('color: white;')

        self.settings = NssSettings()
        self.add_widget(title='Settings', widget=self.settings.view())
        self.addAction('Help', HelpWidget(self).show)

    def add_widget(self, title: str, widget: QWidget) -> QAction:
        widget.setWindowTitle(title)
        action = QAction(title, self)
        action.triggered.connect(lambda: _show_window(widget))
        self.addAction(action)
        return action
