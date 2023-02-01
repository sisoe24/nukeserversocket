"""Test utils module."""
import re
import sys

import pytest
from PySide2.QtCore import QByteArray

from nukeserversocket.util import get_ip, pyDecoder, pyEncoder, validate_output


def test_get_ip():
    """Test ip matches pattern.

    Test if ip matches one of the following pattern: `192.168.1.34` or
    `127.0.0.1`.
    """
    ip = get_ip()
    assert re.match(r'\d{3}\.\d{3}\.\d\.\d{1,2}|127\.0\.0\.1', ip)


def test_validate_output_py3():
    """Check validate output method.

    If python version is 3 or higher should be bytearray.
    """
    if sys.version_info > (3, 0):
        output = validate_output('test message')
        assert isinstance(output, bytearray)


@pytest.fixture()
def _py2_env(monkeypatch):
    """Simulate python 2 environment."""
    monkeypatch.setattr(sys, 'version_info', (2, 7, 16))


def test_validate_output_py2(_py2_env):
    """Check validate output method.

    If python version is 2 be QByteArray.
    """
    if sys.version_info < (3, 0):
        output = validate_output('test message')
        assert isinstance(output, QByteArray)


def test_py3_decoder():
    """Test py decoder method.

    If python3 method should return a str if a str is passed.
    """
    if sys.version_info > (3, 0):
        assert isinstance(pyDecoder('hello'), str)


@pytest.mark.skipif(sys.version_info > (3, 0), reason='only for python2')
def test_py2_decoder(_py2_env):
    """Test py decoder method.

    If python2, method should return a unicode if a str is passed.

    Note: u''.__class_ will not create confusion for py3 linters as `unicode`
    keyword does not exists in newer python.
    """
    if sys.version_info < (3, 0):
        assert isinstance(pyDecoder('hello'), u''.__class__)


def test_py_no_decoder():
    """Test py decoder method.

    If argument is not a text type, should do nothing and return the same type.
    """
    assert isinstance(pyDecoder(1), int)


def test_py3_encoder():
    """Test py encoder method.

    If python3 method should return a str if a str is passed.
    """
    if sys.version_info > (3, 0):
        assert isinstance(pyEncoder('hello'), str)


@pytest.mark.skipif(sys.version_info > (3, 0), reason='only for python2')
def test_py2_encoder(_py2_env):
    """Test py encoder method.

    If python2 method should return a str (bytes for py3) if a str is passed.
    """
    if sys.version_info < (3, 0):
        assert isinstance(pyEncoder('hello'), str)


def test_py_no_encoder():
    """Test py decoder method.

    If argument is not a text type, should do nothing and return the same type.
    """
    assert isinstance(pyEncoder(1), int)
