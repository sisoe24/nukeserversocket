# coding: utf-8
from __future__ import print_function, with_statement

import os
import logging
import traceback


from PySide2.QtWidgets import QMessageBox
from PySide2.QtGui import QClipboard, QDesktopServices

from ..about import about, about_to_string
from ..utils import get_src

LOGGER = logging.getLogger('NukeServerSocket.error_dialog')


def prepare_report(about_str):
    """Prepare report when user wants to report bug to github and
    insert about information to log critical file.

    Args:
        about (str): package/machine information from package.src.about
    """
    for logger in LOGGER.parent.handlers:
        if logger.name == 'Critical':

            with open(logger.baseFilename, 'r+') as file:
                content = file.read()
                file.seek(0, 0)
                file.write(about_str + '\n' + content)

    report = about_to_string(exclude='Github')
    return report


def log_file():
    """Get file path of package.src directory where the log folder is located.

    Returns:
        (str): full path of the errors.log file.
    """
    return os.path.join(get_src(), 'log', 'errors.log')


class ErrorDialog(QMessageBox):
    def __init__(self, parent, msg):
        QMessageBox.__init__(self, parent)

        self.setWindowTitle('NukeServerSocket')
        self.setIcon(QMessageBox.Warning)

        self.setStandardButtons(QMessageBox.Help | QMessageBox.Ok)

        self.addButton('Report bug', QMessageBox.ActionRole)

        self.buttonClicked.connect(self.click_event)

        self.setText('NukeServerSocket error...')
        self.setInformativeText(str(msg))

        self.traceback_msg = traceback.format_exc()
        self.setDetailedText(self.traceback_msg)

    def click_event(self, button):
        if button.text() == 'Report bug':
            q = QMessageBox()
            q.setIcon(QMessageBox.Information)
            q.setText('Report Bug')
            q.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
            q.setInformativeText('Report bug via github')
            q.setDetailedText(
                'The machine info and traceback will be copied into your clipboard when you press Ok. '
                'Alternatively it can be found inside the %s' % log_file())
            q.exec_()

            clipboard = QClipboard()
            clipboard.setText(prepare_report(self.traceback_msg))

            QDesktopServices.openUrl(about['Github'] + '/issues')

        elif button.text() == 'Help':
            pass
