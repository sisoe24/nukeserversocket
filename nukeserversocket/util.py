"""Module with various utility functions."""
# coding: utf-8
from __future__ import print_function

import sys
import socket

from PySide2.QtCore import QTime, QByteArray


def insert_time(text):  # type: (str) -> str
    """Insert time at the beginning of the string.

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

    # check for unicode python2. u''.__class_ will not create confusion for py3
    # linters as `unicode` keyword does not exists
    if isinstance(text, u''.__class__):
        return text.encode('utf-8')
    return text


def get_ip():
    """Return the local network ip address.

    Get ip network with python socket modules. If socket error happens, then
    will return the local host `127.0.0.1`.

    Returns:
        str: network ip address (eg. 192.168.1.60)
    """
    _socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        _socket.connect(('10.255.255.255', 1))
        ip, _ = _socket.getsockname()
    except socket.error:
        ip = '127.0.0.1'
    finally:
        _socket.close()
    return ip
