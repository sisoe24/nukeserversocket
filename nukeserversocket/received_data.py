from __future__ import annotations

import json
from typing import Dict
from dataclasses import field, dataclass

from .logger import get_logger

LOGGER = get_logger()


@dataclass
class ReceivedData:
    """Data received from the client.

    Data is expected to be a json string with the following format:

    {
        "text": "Text to run in the script editor",
        "file": "File name to show in the output (optional))"
        "no_output": "0" or "1" To disable output in the script editor (optional)"
    }

    Raises:
        ValueError: If the data is not a valid json string or if it does not contain a `text` field.

    """

    raw: str

    data: Dict[str, str] = field(init=False)
    file: str = field(init=False)
    text: str = field(init=False)
    no_output: bool = field(init=False)

    def __post_init__(self):

        try:
            self.data = json.loads(self.raw)
            self.data.setdefault('file', '')
            self.data.setdefault('no_output', '0')
        except Exception as e:
            LOGGER.error(f'An exception occurred while decoding the data. {e}')
            self.data = {'text': '', 'file': '', 'no_output': '0'}

        LOGGER.debug('Received data: %s', self.data)

        self.text = self.data.get('text', '')
        if not self.text:
            LOGGER.critical('Data does not contain a text field.')

        self.file = self.data['file']
        self.no_output = bool(int(self.data['no_output']))
