from __future__ import annotations

from typing import Dict
from dataclasses import dataclass

import pytest

from nukeserversocket.received_data import ReceivedData


@dataclass
class ReceivedTestData:
    raw: str
    data: Dict[str, str]
    text: str
    file: str


@pytest.mark.parametrize('data', [
    ReceivedTestData(
        '{"text": "Hello World", "file": "test.py"}',
        {'text': 'Hello World', 'file': 'test.py'},
        'Hello World',
        'test.py'
    ),
    ReceivedTestData(
        '{"text": "Hello World", "file": ""}',
        {'text': 'Hello World', 'file': ''},
        'Hello World',
        ''
    ),
    ReceivedTestData(
        '{"text": "Hello World"}',
        {'text': 'Hello World', 'file': ''},
        'Hello World',
        ''
    ),
])
def test_received_data(data: ReceivedTestData):
    received = ReceivedData(data.raw)

    assert received.raw == data.raw
    assert received.data == data.data
    assert received.text == data.text
    assert received.file == data.file


def test_received_data_no_text():
    with pytest.raises(ValueError) as e:
        ReceivedData('{"file": "test.py"}')
    assert str(e.value) == 'Data does not contain a text field.'


@pytest.mark.parametrize('invalid_data', [
    '{"text": "Hello World", "file", ""}',
    'hello world',
    {'text': 'Hello World', 'file': 'test.py'}
])
def test_received_invalid_data(invalid_data: str):
    with pytest.raises(ValueError) as e:
        ReceivedData(invalid_data)
    assert str(e.value).startswith('An exception occurred while decoding the data.')
