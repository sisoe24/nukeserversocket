"""Module that deals with the data received from the network."""
# coding: utf-8
from __future__ import print_function

import json
import logging

from ..utils import pyEncoder

LOGGER = logging.getLogger('NukeServerSocket.socket')


class InvalidData(Exception):
    """Custom exception class to indicate that data received is invalid."""


class DataCode:
    """Data code class that deals with the received data from the socket."""

    def __init__(self, data):  # type: (str) -> None
        """Init method for the DataCode class.

        Data will be converted to a valid dictionary object and verified if it
        is valid.

        Args:
            data (str): string of the data received from the socket.
        """
        self._raw_data = data

        self._data = self.convert_data()
        self.is_valid_data()

    @property
    def text(self):
        """Get the text from the data array if any."""
        return self._data.get('text', '')

    @property
    def file(self):
        """Get the file from the data array if any."""
        return self._data.get('file', '')

    def data_is_array(self):
        """Return True if data is a stringified array, False otherwise."""
        return self._raw_data.startswith('{')

    def convert_data(self):
        """Convert the data into a valid dictionary type."""
        if self.data_is_array():
            return self._convert_with_json()
        return {'text': self._raw_data}

    def is_valid_data(self):
        """Check if data text is valid.

        Check if text has a value, if is a string or just a space.

        Raises:
            InvalidData: if data is invalid.
        """
        text = pyEncoder(self.text)
        if not text or not isinstance(text, str) or text.isspace():
            raise InvalidData(text)

    def _convert_with_json(self):
        """Convert data with json loads method.

        Returns:
            (dict): data receive in a dictionary type.

        Raises:
            InvalidData: when is unable to process the conversion.
        """
        data = self._raw_data
        try:
            LOGGER.debug('DataCode :: Message is stringified array.')
            data = json.loads(data)

        # could raise json.decoder.JSONDecodeError when decoding problems
        # but if other errors happens will break the script, and I would like
        # to just "ignore" and not execute any code
        except Exception as err:
            msg = "Error json deserialization. %s: %s" % (err, data)
            LOGGER.critical(msg)
            raise InvalidData(msg)

        else:
            LOGGER.debug('DataCode :: Message is valid data: %s', data)
            return data
