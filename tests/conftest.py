from __future__ import annotations

import os
import pathlib

import pytest

from nukeserversocket.settings import _NssSettings

SETTINGS_FILE = pathlib.Path(__file__).parent / 'tmp' / 'nss.json'
SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)


@pytest.fixture()
def mock_settings():
    SETTINGS_FILE.write_text('{}')

    os.environ['NSS_SETTINGS'] = str(SETTINGS_FILE)
    yield _NssSettings(SETTINGS_FILE)

    SETTINGS_FILE.write_text('{}')
