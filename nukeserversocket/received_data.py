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
        "formatText": "0" or "1" To format the text or not. Defaults to "1" (True) (optional)
    }

    """

    raw: str

    data: Dict[str, str] = field(init=False)
    file: str = field(init=False)
    text: str = field(init=False)
    format_text: bool = field(init=False)

    def __post_init__(self):

        try:
            self.data = json.loads(self.raw)
            self.data.setdefault('file', '')
            self.data.setdefault('formatText', '1')
        except Exception as e:
            LOGGER.error(f'An exception occurred while decoding the data. {e}')
            self.data = {'text': '', 'file': '', 'formatText': '1'}

        LOGGER.debug('Received data: %s', self.data)

        self.text = self.data.get('text', '')
        if not self.text:
            LOGGER.critical('Data has invalid text.')

        self.file = self.data['file']

        try:
            self.format_text = bool(int(self.data['formatText']))
        except ValueError:
            LOGGER.error(
                'formatText must be either "0" or "1". Got "%s". Fallback to "1".',
                self.data['formatText']
            )
            self.format_text = True
