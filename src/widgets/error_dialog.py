# coding: utf-8
from __future__ import print_function, with_statement

import os
import logging
import traceback


from PySide2.QtWidgets import QMessageBox
from PySide2.QtGui import QClipboard, QDesktopServices

from ..about import get_about_key, about_to_string


LOGGER = logging.getLogger('NukeServerSocket.error_dialog')


def _get_critical_logger():
    """Search for logger named Critical if any and return it."""

    for logger in LOGGER.parent.handlers:
        if logger.name == 'Critical':
            return logger

    return None


def _prepare_report():
    """Prepare report when user wants to report bug to github and
    insert 'about' information to log critical file.
    """

    critical_logger = _get_critical_logger()

    if not critical_logger:
        return None

    with open(critical_logger.baseFilename, 'r+') as file:
        content = file.read()
        file.seek(0, 0)

        about_traceback = about_to_string() + '\n' + content
        file.write(about_traceback)

    return about_traceback


class ErrorDialog(QMessageBox):
    def __init__(self, msg, parent=None):
        QMessageBox.__init__(self, parent)
        self.setWindowTitle('NukeServerSocket')
        self.setIcon(QMessageBox.Warning)

        self.setText('NukeServerSocket error...')
        self.setInformativeText(str(msg))

        self.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        self.addButton('Report bug', QMessageBox.ActionRole)
        self.addButton('Open logs', QMessageBox.ActionRole)

        self.buttonClicked.connect(self.click_event)

        _info = (
            'Traceback will be copied into your clipboard when clicking Report Bug.\n---\n'
        )

        self._traceback = traceback.format_exc()
        self.setDetailedText(_info + self._traceback)

    def click_event(self, button):
        if button.text() == 'Report bug':

            report = _prepare_report()
            if not report:
                report = self._traceback

            clipboard = QClipboard()
            clipboard.setText(report)

            to_open = get_about_key('Issues')

        elif button.text() == 'Open logs':
            to_open = get_about_key('Logs')

        elif button.text() == 'Cancel':
            return

        QDesktopServices.openUrl(to_open)
