import sys
import re

import pytest
from PySide2.QtCore import QByteArray

from src.utils import get_ip
from src.utils.util import validate_output


def test_get_ip():
    """Check for match:
        192.168.1.34 or 127.0.0.1
        192.168.1.34 or 192.168.1.3
        192.168.1.35
        127.0.0.1
    """
    ip = get_ip()
    assert re.match(r'''
        (\d{3}\.\d{3}\.\d\.\d{1,2})?
        (\sor\s)?
        (127\.0\.0\.1)?''', ip, re.X)


def test_validate_output():
    output = validate_output('test message')
    if sys.version_info > (3, 0):
        assert isinstance(output, bytearray)
    else:
        assert isinstance(output, QByteArray)
