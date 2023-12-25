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
    no_reply: bool = False


@pytest.mark.parametrize('data', [
    ReceivedTestData(
        '{"text": "Hello World", "file": "test.py", "noReply": "1"}',
        {'text': 'Hello World', 'file': 'test.py', 'noReply': '1'},
        'Hello World',
        'test.py',
        True
    ),
    ReceivedTestData(
        '{"text": "Hello World", "file": "test.py", "noReply": "0"}',
        {'text': 'Hello World', 'file': 'test.py', 'noReply': '0'},
        'Hello World',
        'test.py',
        False
    ),
    ReceivedTestData(
        '{"text": "Hello World", "file": ""}',
        {'text': 'Hello World', 'file': '', 'noReply': '0'},
        'Hello World',
        '',
        False
    ),
    ReceivedTestData(
        '{"text": "Hello World"}',
        {'text': 'Hello World', 'file': '', 'noReply': '0'},
        'Hello World',
        '',
        False
    ),
    ReceivedTestData(
        '{"text": "",',
        {'text': '', 'file': '', 'noReply': '0'},
        '',
        '',
        False
    )

])
def test_received_data(data: ReceivedTestData):
    received = ReceivedData(data.raw)

    assert received.raw == data.raw
    assert received.data == data.data
    assert received.text == data.text
    assert received.file == data.file
    assert received.no_reply == data.no_reply
