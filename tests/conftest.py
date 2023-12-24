from __future__ import annotations

import os
import logging
import pathlib

import pytest

from nukeserversocket.settings import _NssSettings
from nukeserversocket.utils.cache import clear_cache
from nukeserversocket.controllers.local_app import LocalEditor

SETTINGS_FILE = pathlib.Path(__file__).parent / 'tmp' / 'nss.json'
SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)


@pytest.fixture(autouse=True)
def editor():
    LOGGER = logging.getLogger('nukeserversocket')
    LOGGER.propagate = False
    LOGGER.handlers.clear()


@pytest.fixture(autouse=True)
def mock_settings():
    SETTINGS_FILE.write_text('{}')

    os.environ['NSS_SETTINGS'] = str(SETTINGS_FILE)
    yield SETTINGS_FILE

    clear_cache('settings')
    SETTINGS_FILE.write_text('{}')


@pytest.fixture()
def settings(mock_settings: pathlib.Path):
    return _NssSettings(mock_settings)
