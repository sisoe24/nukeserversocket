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
    no_output: bool = False


@pytest.mark.parametrize('data', [
    ReceivedTestData(
        '{"text": "Hello World", "file": "test.py", "no_output": "1"}',
        {'text': 'Hello World', 'file': 'test.py', 'no_output': '1'},
        'Hello World',
        'test.py',
        True
    ),
    ReceivedTestData(
        '{"text": "Hello World", "file": "test.py", "no_output": "0"}',
        {'text': 'Hello World', 'file': 'test.py', 'no_output': '0'},
        'Hello World',
        'test.py',
        False
    ),
    ReceivedTestData(
        '{"text": "Hello World", "file": ""}',
        {'text': 'Hello World', 'file': '', 'no_output': '0'},
        'Hello World',
        '',
        False
    ),
    ReceivedTestData(
        '{"text": "Hello World"}',
        {'text': 'Hello World', 'file': '', 'no_output': '0'},
        'Hello World',
        '',
        False
    ),
    ReceivedTestData(
        '{"text": "",',
        {'text': '', 'file': '', 'no_output': '0'},
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
    assert received.no_output == data.no_output
