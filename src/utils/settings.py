# coding: utf-8
from __future__ import print_function

import os
import logging

from PySide2.QtCore import QSettings

LOGGER = logging.getLogger('NukeServerSocket.settings')


CONFIG_FILE = os.path.join(
    os.path.expanduser('~'), '.nuke', 'NukeServerSocket.ini'
)


class AppSettings(QSettings):
    def __init__(self):
        QSettings.__init__(self, CONFIG_FILE, QSettings.IniFormat)

    def validate_port_settings(self, default_port='54321'):
        """Check for the port settings in the ini file and verify its correctness.

        If value is not found or is wrong, then create a default one with value `54321`
        """
        port = self.value('server/port')
        LOGGER.debug('Verify port configuration: %s', port)

        if not port or not 49512 <= int(port) <= 65535:
            self.setValue('server/port', default_port)

    def get_bool(self, value, default=False):
        """Convert .ini file bool to python valid data type.

        Args:
            value (str): the value to get from the config file.
            default (bool, optional): Default value if not present in config. Defaults to False.

        Returns:
            [type]: [description]
        """
        return self.value(value, default) in (True, 'true')
