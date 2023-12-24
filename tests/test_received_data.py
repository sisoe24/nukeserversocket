from __future__ import annotations

from typing import Dict
from dataclasses import dataclass

import pytest

from nukeserversocket.received_data import ReceivedData

pytestmark = pytest.mark.quick


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
    ReceivedTestData(
        '{"text": "",',
        {'text': '', 'file': ''},
        '',
        ''
    )

])
def test_received_data(data: ReceivedTestData):
    received = ReceivedData(data.raw)

    assert received.raw == data.raw
    assert received.data == data.data
    assert received.text == data.text
    assert received.file == data.file
