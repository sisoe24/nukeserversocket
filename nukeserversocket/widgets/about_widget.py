"""About widget with various app information and links."""
# coding: utf-8

from PySide2.QtGui import QDesktopServices
from PySide2.QtCore import Qt
from PySide2.QtWidgets import (QLabel, QWidget, QFormLayout, QGridLayout,
                               QPushButton, QVBoxLayout)

from ..about import about, about_links


class AboutWidget(QWidget):
    """About widget with various app information and links."""

    def __init__(self,):
        """Init method for the AboutWidget class."""
        QWidget.__init__(self)
        self.setObjectName('AboutWidget')

        self._form_layout = QFormLayout()
        self._fill_form_layout()

        self._grid_layout = QGridLayout()
        self._fill_grid_buttons()

        self._layout = QVBoxLayout()
        self._layout.addLayout(self._form_layout, Qt.AlignCenter)
        self._layout.addLayout(self._grid_layout, Qt.AlignCenter)

        self.setLayout(self._layout)

    def _fill_form_layout(self):
        """Fill the form layout with the information from about.py."""
        self._form_layout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)

        for key, value in about():
            self._form_layout.addRow(QLabel(key + ':'), QLabel(value))

    def _fill_grid_buttons(self, columns=2):
        """Fill the grid layout with the buttons.

        Args:
            columns (int, optional): Number of columns to show. Defaults to 2.
        """
        row = 0
        column = 0

        for name, link in about_links():
            btn = self._create_btn(name, link)
            self._grid_layout.addWidget(btn, row, column)

            column += 1
            if column == columns:
                row += 1
                column = 0

    @staticmethod
    def _create_btn(name, link):  # type: (str, str) -> QPushButton
        """Create buttons with some default values.

        Create a QPushButton adding the tooltip, the property and setting up
        the clicked signal. The property is needed to test that the link
        assigned to the signal is correct.

        Args:
            name (str): title of the button.
            link (str): web link to be assigned for the button.

        Returns:
            QPushButton: A QPushButton object.
        """
        btn = QPushButton(name)
        btn.setToolTip('Open ' + link)
        btn.setProperty('link', link)
        btn.clicked.connect(lambda: QDesktopServices.openUrl(link))
        return btn
