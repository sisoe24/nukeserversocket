# coding: utf-8
from __future__ import print_function

import os
import logging

from PySide2.QtCore import QSettings

LOGGER = logging.getLogger('NukeServerSocket.settings')


def config_file():
    """Get configuration file in home/.nuke"""
    return os.path.join(
        os.path.expanduser('~'), '.nuke/NukeServerSocket.ini'
    )


class SettingsState(QSettings):
    def __init__(self):
        QSettings.__init__(self, config_file(), QSettings.IniFormat)

    def verify_port_config(self, default_port='54321'):
        """If .ini file or port gets deleted after execution, create it back."""
        port = self.value('server/port')
        LOGGER.debug('Verify port configuration: %s', port)

        if not port or len(port) != 5:
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
