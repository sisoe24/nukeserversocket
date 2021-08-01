# coding: utf-8
""" Text widget needed for status purposes."""
from __future__ import print_function


from PySide2.QtWidgets import (
    QGroupBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget
)

from src.utils import insert_time


class TextBox(QGroupBox):
    def __init__(self, title):
        QGroupBox.__init__(self, title)

        self.text_box = QPlainTextEdit()
        self.text_box.setReadOnly(True)

        btn = QPushButton('Clear text')
        btn.clicked.connect(self.text_box.clear)

        _layout = QVBoxLayout()
        _layout.addWidget(self.text_box)
        _layout.addWidget(btn)

        self.setLayout(_layout)


class TextWidgets(QWidget):
    def __init__(self):
        QWidget.__init__(self)
        self.status_text = TextBox('Status')
        self.input_text = TextBox('Input')
        self.ouput_text = TextBox('Output')

        _layout = QVBoxLayout()
        _layout.addWidget(self.status_text)
        _layout.addWidget(self.input_text)
        _layout.addWidget(self.ouput_text)

        self.setLayout(_layout)

    def set_status_text(self, text):
        self.status_text.text_box.insertPlainText(insert_time(text))

    def set_input_text(self, text):
        self.input_text.text_box.insertPlainText(insert_time(text))

    def set_output_text(self, text):
        text = str(text).strip()
        self.ouput_text.text_box.insertPlainText(insert_time(text))
