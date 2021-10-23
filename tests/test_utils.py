"""Test utils module."""
import re
import sys

from PySide2.QtCore import QByteArray

from src.utils import get_ip
from src.utils.util import validate_output


def test_get_ip():
    """Test ip match.

    Test if ip matches one of the following pattern:
        - 192.168.1.34 or 127.0.0.1
        - 192.168.1.34 or 192.168.1.3
        - 192.168.1.35
        - 127.0.0.1
    """
    ip = get_ip()
    assert re.match(r'''
        (\d{3}\.\d{3}\.\d\.\d{1,2})?
        (\sor\s)?
        (127\.0\.0\.1)?''', ip, re.X)


def test_validate_output_py3():
    """Check validate output method.

    If python version is 3 or higher should be bytearray.
    """
    if sys.version_info > (3, 0):
        output = validate_output('test message')
        assert isinstance(output, bytearray)


def test_validate_output_py2(monkeypatch):
    """Check validate output method.

    If python version is 2 be QByteArray.
    """
    monkeypatch.setattr(sys, 'version_info', (2, 7, 16))
    if sys.version_info < (3, 0):
        output = validate_output('test message')
        assert isinstance(output, QByteArray)
