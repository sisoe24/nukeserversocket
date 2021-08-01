# coding: utf-8
from __future__ import print_function, with_statement
from PySide2.QtCore import QSysInfo, __version__

import os
import logging
import traceback
import subprocess

from PySide2.QtWidgets import QMessageBox
from PySide2.QtGui import QClipboard, QDesktopServices

from src import nuke


LOGGER = logging.getLogger('NukeServerSocket.error_dialog')

__about__ = {
    'NukeServerSocket': '0.0.1',
    'PySide2': __version__,
    'Nuke': nuke.NUKE_VERSION_STRING,
    'machine': QSysInfo().prettyProductName()
}


def append_machine_info(machine):

    for i in LOGGER.parent.handlers:
        if i.name == 'Critical':

            with open(i.baseFilename, 'r+') as f:
                content = f.read()
                f.seek(0, 0)
                f.write(machine + '\n' + content)


def machine_info_string():
    machine = ''
    for k, v in __about__.items():
        machine += '%s: %s\n' % (k, v)
    append_machine_info(machine)
    return machine


def generate_report(trace):
    report = machine_info_string() + trace
    return report


def file_path():
    current_path = os.path.dirname(__file__)
    src_path = os.path.dirname(current_path)
    abs_path = os.path.abspath(src_path)
    full_path = os.path.join(abs_path, 'log', 'errors.log')
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
            clipboard.setText(generate_report(self.traceback_msg))

            try:
                issue_url = subprocess.check_output(
                    ['git', 'config', '--get', 'remote.origin.url']
                )
            except subprocess.CalledProcessError as err:
                print('no remote yet', err)
            else:
                issue_url = issue_url.replace('.git', 'issues')

                QDesktopServices.openUrl(issue_url)

        elif button.text() == 'Help':
            pass
