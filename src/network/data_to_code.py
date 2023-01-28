"""Module that deals with the data received from the network."""
# coding: utf-8

import json
import logging

from ..util import pyEncoder

LOGGER = logging.getLogger('nukeserversocket')


class InvalidData(Exception):
    """Custom exception class to indicate that data received is invalid."""


class DataCode:
    """Data code class that deals with the received data from the socket."""

    def __init__(self, data):  # type: (str) -> None
        """`DataCode("{'text': text, 'file': file}")`

        Convert the data to a valid python dictionary and Verify if is valid.

        Args:
            data (str): string of the data received from the socket.
        """
        self._raw_data = data
        self._dict_data = self.to_dict()
        self._is_valid()

    @property
    def text(self):
        """Get the text from the data array if any."""
        return self._dict_data.get('text', '')

    @property
    def file(self):
        """Get the file from the data array if any."""
        return self._dict_data.get('file', '')

    def data_is_array(self):
        """Return True if data is a stringified array, False otherwise."""
        return self._raw_data.startswith('{')

    def to_dict(self):
        """Convert the data into a valid dictionary type."""
        if self.data_is_array():
            return self._convert_with_json()
        return {'text': self._raw_data}

    def _is_valid(self):
        """Check if data text is valid.

        If data has no text, it is not a string or is a space, is considered
        not valid.

        Returns:
            bool: Returns True if data is valid.

        Raises:
            InvalidData: if data is invalid.
        """
        text = pyEncoder(self.text)
        if not text or not isinstance(text, str) or text.isspace():
            raise InvalidData(text)
        return True

    def _convert_with_json(self):
        """Convert data with json loads method.

        Returns:
            (dict): data receive in a dictionary type.

        Raises:
            InvalidData: when is unable to process the conversion.
        """
        try:
            LOGGER.debug('DataCode :: Message is stringified array.')
            data = json.loads(self._raw_data)

        # I could raise json.decoder.JSONDecodeError but if other errors will
        # occur, they will break the execution and I would like to ignore them
        except Exception as err:
            msg = 'Error json deserialization. %s: %s' % (err, self._raw_data)
            LOGGER.critical(msg)
            raise InvalidData(msg)
        else:
            LOGGER.debug('DataCode :: Message is valid data: %s', data)
            return data
