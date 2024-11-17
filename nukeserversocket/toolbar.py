from __future__ import annotations

import os
import sysconfig
import webbrowser
from typing import Dict
from platform import python_version

from PySide2 import __version__ as PySide2_version
from PySide2.QtCore import Slot
from PySide2.QtWidgets import (QLabel, QAction, QDialog, QWidget, QToolBar,
                               QFormLayout, QPushButton)

from .version import __version__


def about() -> Dict[str, str]:
    """Return a dictionary with information about the application."""
    return {
        'version': __version__,
        'python': python_version(),
        'pyside': PySide2_version,
        'machine': sysconfig.get_platform(),
    }


class HelpWidget(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('NukeServerSocket Help')

        form_layout = QFormLayout()
        for name, value in about().items():
            form_layout.addRow(f'{name.title()}:', QLabel(value))

        form_layout.addRow(self._button_builder('Readme'))
        form_layout.addRow(self._button_builder('Changelog'))
        form_layout.addRow(self._button_builder('Issues'))

        self.setLayout(form_layout)

    def _button_builder(self, text: str) -> QPushButton:
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
        self.add_widget(title='Help', widget=HelpWidget(self))

    def add_widget(self, title: str, widget: QWidget) -> QAction:
        widget.setWindowTitle(title)
        action = QAction(title, self)
        action.triggered.connect(lambda: _show_window(widget))
        self.addAction(action)
        return action
