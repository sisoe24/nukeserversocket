"""Module with various utility functions."""
# coding: utf-8
from __future__ import print_function

import sys
import socket
import logging

from PySide2.QtCore import QByteArray, QTime, QTimer
from PySide2.QtNetwork import QNetworkInterface

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


def connection_timer(timeout):  # type: (int) -> QTimer
    """Set up a single shot connection timeout QTimer.

    Args:
        timeout (int): timeout time in seconds: 1, 10, 60

    Returns:
        QTimer: QTimer object
    """
    # TODO: should be cool to have a widget timer with the time left
    _timer = QTimer()
    _timer.setInterval(timeout * 1000)
    _timer.setSingleShot(True)
    return _timer


def validate_output(data):  # type: (str) -> bytearray | QByteArray
    """Check for nuke version and return appropriate type of output data.

    Nuke11, 12 output type is 'unicode' and Nuke13 output type is 'str'.
    """
    if sys.version_info > (3, 0):
        data = bytearray(data, 'utf-8')
    else:
        data = QByteArray(data.encode('utf-8'))

    return data


def pyDecoder(text):
    """Python 2/3 `utf-8` decoder.

    The return will depend on which version of python is being used. With py2
    will return a `unicode` and py3 a `str`. If wrong type is passed will do
    nothing.

    Args:
        (str) text: text to be decoded.

    Returns:
        (str|unicode): decoded utf-8 unicode text
    """
    if sys.version_info > (3, 0):
        if isinstance(text, bytes):
            return text.decode('utf-8')
        return text

    if isinstance(text, str):
        return text.decode('utf-8')
    return text


def pyEncoder(text):
    """Python 2/3 `utf-8` encoder.

    The return will depend on which version of python is being used. With py2
    will return a `str` and py3 a `bytes`. If wrong type is passed will do
    nothing.

    Args:
        (unicode|str) text: text to be encoded.

    Returns:
        (str|bytes): encoded utf-8 text.
    """
    if sys.version_info > (3, 0):
        return text

    if isinstance(text, unicode):
        return text.encode('utf-8')
    return text


def get_ip():
    """Return the network ip to show to user.

    Method will try to get the first address using Qt modules and then using
    python socket module.

    Returns:
        (str): a str with the ip address. Could be more than one in that case
        will have the format: `first_address or second_address`
    """
    def _get_ip_qt():
        """Get ip network with Qt modules.

        Doesn't work on Nuke 11 as QNetworkInterface doesn't not have .isglobal
        """
        # TODO: should probably delete this
        return [
            address.toString()
            for address in QNetworkInterface().allAddresses()
            if address.isGlobal()
        ]

    def _get_ip_py():
        """Get ip network with python socket modules."""
        _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            _socket.connect(('10.255.255.255', 1))
            ip, _ = _socket.getsockname()
        except Exception:
            ip = '127.0.0.1'
        finally:
            _socket.close()
        return [ip]

    # Nuke11 doesn't have Network.isGlobal()
    try:
        ip1 = _get_ip_qt()
    except AttributeError:
        ip1 = []

    ip2 = _get_ip_py()

    return ' or '.join(list(set(ip1).union(ip2)))
