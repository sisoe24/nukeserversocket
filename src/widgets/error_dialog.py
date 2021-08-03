# coding: utf-8
from __future__ import print_function, with_statement

import os
import logging
import traceback

from collections import OrderedDict

from PySide2.QtWidgets import QMessageBox
from PySide2.QtGui import QClipboard, QDesktopServices

from NukeServerSocket.src import about

LOGGER = logging.getLogger('NukeServerSocket.error_dialog')


def prepare_report(trace):
    """Prepare report when user wants to report bug to github.  """

    def _insert_about_info(about_str):
        """Insert about information to log critical file.

        Args:
            about (str): package/machine information from package.src.about
        """
        for i in LOGGER.parent.handlers:
            if i.name == 'Critical':

                with open(i.baseFilename, 'r+') as f:
                    content = f.read()
                    f.seek(0, 0)
                    f.write(about_str + '\n' + content)

    def _about_to_string():
        """Get about dict from package.src.about and convert it into a string."""
        about_str = ''
        for key, value in OrderedDict(sorted(about.items())).items():
            if key == 'Github':
                continue
            about_str += '%s: %s\n' % (key, value)

        _insert_about_info(about_str)
        return about_str

    report = _about_to_string() + trace
    return report


def file_path():
    """Get file path of package.src directory where the log folder is located.

    Returns:
        (str): full path of the errors.log file.
    """
    current_path = os.path.dirname(os.path.abspath(__file__))
    src_path = os.path.dirname(current_path)
    full_path = os.path.join(src_path, 'log', 'errors.log')
    return full_path


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
                'Alternatively it can be found inside the %s' % file_path())
            q.exec_()

            clipboard = QClipboard()
            clipboard.setText(prepare_report(self.traceback_msg))

            QDesktopServices.openUrl(about['Github'] + '/issues')

        elif button.text() == 'Help':
            pass
