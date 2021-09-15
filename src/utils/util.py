# coding: utf-8
from __future__ import print_function

import socket
import logging

from PySide2.QtCore import QByteArray, QTime
from PySide2.QtNetwork import QNetworkInterface

from .. import nuke

LOGGER = logging.getLogger('NukeServerSocket.util')


def insert_time(text):  # type: (str) -> str
    """Insert textual time at the beginning of the string. 

    Example: [17:49:25] Hello World

    Args:
        text (str): str to insert the time.

    Returns:
        str: string with inserted current timed at the beginning.
    """
    time = QTime().currentTime().toString()
    return '[%s] %s\n' % (time, text)


def validate_output(data):  # type: (str) -> bytearray | QByteArray
    """Check for nuke version and return appropriate type of output data.

    Nuke11, 12 output type is 'unicode'
    Nuke13 output type is 'str'

    QByteArray Supported signatures:
        PySide2.QtCore.QByteArray()
        PySide2.QtCore.QByteArray(bytearray)
        PySide2.QtCore.QByteArray(bytes) # Nuke 11&12 (str) not (bytes)
        PySide2.QtCore.QByteArray(PySide2.QtCore.QByteArray)
        PySide2.QtCore.QByteArray(int, typing.Char)
    """
    nuke_version = nuke.env['NukeVersionMajor']
    LOGGER.debug('Running Nuke: %s', nuke_version)

    if nuke_version == 13:
        data = bytearray(data, 'utf-8')
    else:
        data = QByteArray(data.encode('utf-8'))

    return data


def get_ip():
    def _get_ip_qt():
        """Doesn't work on Nuke 11 as QNetworkInterface doesn't not have .isglobal()"""
        return [
            address.toString()
            for address in QNetworkInterface().allAddresses()
            if address.isGlobal()
        ]

    def _get_ip_py():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(('10.255.255.255', 1))
            ip, port = s.getsockname()
        except Exception:
            ip = '127.0.0.1'
        finally:
            s.close()
        return [ip]

    # HACK: Nuke11 doesnt have Network.isGlobal()
    if nuke.env['NukeVersionMajor'] == 11:
        ip1 = []
    else:
        ip1 = _get_ip_qt()

    ip2 = _get_ip_py()

    return ' or '.join(list(set(ip1).union(ip2)))
