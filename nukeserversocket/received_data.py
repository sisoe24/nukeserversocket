from __future__ import annotations

import json
from typing import Dict
from dataclasses import field, dataclass


@dataclass
class ReceivedData:
    """Data received from the client.

    Data is expected to be a json string with the following format:

    {
        "text": "Text to run in the script editor",
        "file": "File name to show in the output"
    }

    NOTE: From version 1.0.0, the `file` field is mandatory but it can be an empty string.

    Raises:
        ValueError: If the data is not a valid json string or if it does not contain a `text` field.

    """

    raw: str
    data: Dict[str, str] = field(init=False)
    file: str = field(init=False)
    text: str = field(init=False)

    def __post_init__(self):

        try:
            self.data = json.loads(self.raw)
            self.data.setdefault('file', '')
        except Exception as e:
            raise ValueError(f'An exception occurred while decoding the data. {e}') from e

        self.text = self.data.get('text')
        if not self.text:
            raise ValueError('Data does not contain a text field.')

        # file is optional as is only used to show the file name in the output
        self.file = self.data.get('file')
