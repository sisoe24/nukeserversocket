from __future__ import annotations

import json

import pytest

from nukeserversocket.received_data import ReceivedData


@pytest.fixture()
def data():
    return json.dumps({'text': 'Hello World', 'file': 'test.py'})


def test_received_data(data: str):

    received = ReceivedData(data)

    assert received.raw == data
    assert received.data == {'text': 'Hello World', 'file': 'test.py'}
    assert received.text == 'Hello World'
    assert received.file == 'test.py'


def test_received_data_without_file():

    data = json.dumps({'text': 'Hello World'})
    received = ReceivedData(data)

    assert received.raw == data
    assert received.data == {'text': 'Hello World', 'file': ''}
    assert received.text == 'Hello World'
    assert received.file == ''


def test_received_data_with_empty_file():

    data = json.dumps({'text': 'Hello World', 'file': ''})
    received = ReceivedData(data)

    assert received.raw == data
    assert received.data == {'text': 'Hello World', 'file': ''}
    assert received.text == 'Hello World'
    assert received.file == ''


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
