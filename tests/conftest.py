from __future__ import annotations

import os
import logging
import pathlib

import pytest

from nukeserversocket.settings import _NssSettings

SETTINGS_FILE = pathlib.Path(__file__).parent / 'tmp' / 'nss.json'
SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope='session', autouse=True)
def patch_logger():
    logger = logging.getLogger('nukeserversocket')
    logger.handlers.clear()


@pytest.fixture()
def mock_settings():
    SETTINGS_FILE.write_text('{}')

    os.environ['NSS_SETTINGS'] = str(SETTINGS_FILE)
    yield SETTINGS_FILE

    SETTINGS_FILE.write_text('{}')


@pytest.fixture()
def nss_settings(mock_settings: pathlib.Path):
    return _NssSettings(mock_settings)
