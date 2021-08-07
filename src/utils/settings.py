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

    def get_bool(self, value, default=False):
        """Convert .ini file bool to python valid data type.

        Args:
            value (str): the value to get from the config file.
            default (bool, optional): Default vaule if not present in config. Defaults to False.

        Returns:
            [type]: [description]
        """
        return self.value(value, default) in (True, 'true')
