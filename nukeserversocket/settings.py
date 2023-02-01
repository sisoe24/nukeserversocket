"""Application settings module."""
# coding: utf-8
from __future__ import print_function

import os
import logging

from PySide2.QtCore import QSettings

LOGGER = logging.getLogger('nukeserversocket')


CONFIG_FILE = os.path.join(
    os.path.expanduser('~'), '.nuke', 'NukeServerSocket.ini'
)


class AppSettings(QSettings):
    """Custom QSettings app."""

    def __init__(self):
        """Init method for the AppSettings class.

        Class will be initialized by calling its parent class QSettings with a
        file path and the IniFormat option.
        """
        QSettings.__init__(self, CONFIG_FILE, QSettings.IniFormat)

    def validate_port_settings(self, default_port='54321'):
        """Check if the port config value in the ini file.

        If value is not found or is wrong, then create a default one with value
        `54321`.
        """
        port = self.value('server/port')
        LOGGER.debug('Verify port configuration: %s', port)

        if not port or not 49512 <= int(port) <= 65535:
            self.setValue('server/port', default_port)

    def get_bool(self, value, default=False):
        """Convert .ini bool to python valid bool type.

        A .ini bool will be a lowercase string so it must be converted into a
        valid python bool.

        Args:
            value (str): the value to get from the config file.
            default (bool, optional): Default value if not present in config.
            Defaults to False.

        Returns:
            bool: value of the setting.
        """
        return self.value(value, default) in (True, 'true')
