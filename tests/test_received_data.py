from __future__ import annotations

from typing import Dict
from dataclasses import dataclass

import pytest

from nukeserversocket.received_data import ReceivedData


@dataclass
class ReceivedTestData:
    name: str
    raw: str
    data: Dict[str, str]
    text: str
    file: str
    format_text: bool = False


@pytest.mark.parametrize('data', [
    ReceivedTestData(
        name='Valid data with formatText as "1"',
        raw='{"text": "Hello World", "file": "test.py", "formatText": "1"}',
        data={'text': 'Hello World', 'file': 'test.py', 'formatText': '1'},
        text='Hello World',
        file='test.py',
        format_text=True
    ),
    ReceivedTestData(
        name='Valid data with formatText as "0"',
        raw='{"text": "Hello World", "file": "test.py", "formatText": "0"}',
        data={'text': 'Hello World', 'file': 'test.py', 'formatText': '0'},
        text='Hello World',
        file='test.py',
        format_text=False
    ),
    ReceivedTestData(
        name='Valid data with wrong formatText',
        raw='{"text": "Hello World", "formatText": "None"}',
        data={'text': 'Hello World', 'file': '', 'formatText': 'None'},
        text='Hello World',
        file='',
        format_text=True
    ),
    ReceivedTestData(
        name='Validata data with missing file',
        raw='{"text": "Hello World", "file": ""}',
        data={'text': 'Hello World', 'file': '', 'formatText': '1'},
        text='Hello World',
        file='',
        format_text=True
    ),
    ReceivedTestData(
        name='Validata data only text',
        raw='{"text": "Hello World"}',
        data={'text': 'Hello World', 'file': '', 'formatText': '1'},
        text='Hello World',
        file='',
        format_text=True
    ),
    ReceivedTestData(
        name='Invalid data with missing text',
        raw='{"text": "",',
        data={'text': '', 'file': '', 'formatText': '1'},
        text='',
        file='',
        format_text=True
    )
], ids=lambda data: data.name)
def test_received_data(data: ReceivedTestData):
    received = ReceivedData(data.raw)

    assert received.raw == data.raw
    assert received.data == data.data
    assert received.text == data.text
    assert received.file == data.file
    assert received.format_text == data.format_text
