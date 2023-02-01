"""Error dialog widget that shows when app had an exception at launch."""
# coding: utf-8

import traceback

from PySide2.QtGui import QClipboard, QDesktopServices
from PySide2.QtWidgets import QMessageBox

from ..about import get_about_key, about_to_string


class ErrorDialog(QMessageBox):
    """Error dialog widget."""

    def __init__(self, msg, parent=None):
        """Init method for the ErrorDialog class.

        Create a custom QMessageBox widget to be shown when an error happens.
        Widget will have link to the github issues and the path to the logs.

        Traceback will be shown in the "see more details" section.

        Args:
            msg (str): message to be shown
            parent (QWidget, optional): QWidget to be set as a parent. This is
            needed when launch the widget in non modal mode. Defaults to None.
        """
        QMessageBox.__init__(self, parent)
        self.setWindowTitle('NukeServerSocket')
        self.setIcon(QMessageBox.Warning)

        self.setText('NukeServerSocket error...')
        self.setInformativeText(str(msg))

        self.setStandardButtons(QMessageBox.Cancel | QMessageBox.Ok)
        self.addButton('Report bug', QMessageBox.ActionRole)
        self.addButton('Open logs', QMessageBox.ActionRole)

        self.buttonClicked.connect(self._click_event)

        self._traceback = traceback.format_exc()
        self.setDetailedText(
            'Traceback will be copied to clipboard when clicking Report Bug.'
            '\n---\n' + self._traceback
        )

    def _prepare_report(self):
        """Prepare the error report and copies it to the clipboard.

        Returns:
            Report: a namedtuple with the link and the port attributes.
        """
        report = about_to_string() + '\n' + self._traceback
        QClipboard().setText(report)

    def _click_event(self, button):
        """After the click event, get the link to open."""
        if button.text() == 'Report bug':
            self._prepare_report()
            to_open = get_about_key('Issues')

        elif button.text() == 'Open logs':
            to_open = get_about_key('Logs')

        elif button.text() in ['OK', 'Cancel']:
            return

        QDesktopServices.openUrl(to_open)
