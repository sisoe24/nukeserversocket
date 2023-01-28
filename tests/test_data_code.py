"""Test the CodeEditor class."""

import pytest

from src.network.data_to_code import DataCode, InvalidData

valid_data = (
    '{"text": "hello"}',
    '{"text": "hello", "file": "file"}',
    '{"text": "hello", "file": ""}',
    'text'
)


@pytest.mark.parametrize('data', valid_data)
def test_data_code_is_valid(data):
    assert DataCode(data)._is_valid()


not_valid_data = (
    '{"text": ""}',
    '{"text": "", "file": "file"}',
    '{}',
    '{""}',
    '{" "}',
    '',
    ' '
)


@pytest.mark.parametrize('data', not_valid_data)
def test_data_code_is_invalid(data):
    with pytest.raises(InvalidData):
        DataCode(data)._is_valid()


def test_data_code_is_array():
    assert DataCode('{"text":"text"}').data_is_array()


def test_data_code_is_not_array():
    assert not DataCode('text').data_is_array()


def test_data_code_text():
    assert DataCode('{"text":"hello"}').text == 'hello'


def test_data_code_file():
    assert DataCode('{"text":"hello", "file":"file.py"}').file == 'file.py'


def test_data_code_no_file():
    assert DataCode('{"text":"hello", "file":""}').file == ''


def test_convert_data_array():
    data = DataCode('{"text":"text", "file":"file"}')
    assert isinstance(data._dict_data, dict)


def test_convert_data_string():
    data = DataCode('text')
    assert isinstance(data._dict_data, dict)
