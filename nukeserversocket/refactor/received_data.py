from __future__ import annotations

import json
from dataclasses import field, dataclass


@dataclass
class ReceivedData:
    data: str
    file: str = field(init=False)
    text: str = field(init=False)

    def __post_init__(self):

        try:
            d = json.loads(self.data)
        except json.JSONDecodeError as e:
            raise ValueError('Data is not a valid json.') from e

        self.text = d.get('text')
        if not self.text:
            raise ValueError('Data does not contain a text field.')

        # file is optional as is only used to show the file name in the output
        self.file = d.get('file')
