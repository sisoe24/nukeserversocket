# coding: utf-8
from __future__ import print_function

import logging
from PySide2.QtCore import Qt
from PySide2.QtGui import QDesktopServices

from PySide2.QtWidgets import (
    QFormLayout,
    QGridLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget
)

from ..about import about, about_links

LOGGER = logging.getLogger('ProfileInspector.about_widget')


class AboutWidget(QWidget):
    def __init__(self,):
        QWidget.__init__(self)
        # TODO: cant figure out how to keep the layout in center
        # self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)

        self._form_layout = QFormLayout()
        self._fill_form_layout()

        self._grid_layout = QGridLayout()
        self._fill_grid_buttons()

        self._layout = QVBoxLayout()
        self._layout.addLayout(self._form_layout, Qt.AlignCenter)
        self._layout.addLayout(self._grid_layout, Qt.AlignCenter)

        # arbitrary magic number to push the bottom layout at the top
        # self._layout.addStretch(5000)

        self.setLayout(self._layout)

    def _fill_form_layout(self):
        """fill the form layout with the information from about.py"""
        self._form_layout.setFormAlignment(Qt.AlignHCenter | Qt.AlignTop)

        for key, value in about():
            self._form_layout.addRow(QLabel(key), QLabel(value))

    def _fill_grid_buttons(self, columns=2):
        """Fill the grid layout with the buttons. By default will change row every 2 columns"""
        row = 0
        column = 0

        for key, value in about_links():
            btn = self._create_btn(key, value)
            self._grid_layout.addWidget(btn, row, column)

            column += 1
            if column == columns:
                row += 1
                column = 0

    @staticmethod
    def _create_btn(key, value):
        """Template to create buttons and assign them the signal to open an url."""
        btn = QPushButton(key)
        btn.setToolTip('Open ' + value)
        btn.setProperty('link', value)
        btn.clicked.connect(lambda: QDesktopServices.openUrl(value))
        return btn
