from __future__ import annotations

import os
import pathlib

import pytest

from nukeserversocket.utils.cache import clear_cache
from nukeserversocket.controllers.local_app import LocalEditor


@pytest.fixture()
def tmp_settings():
    f = pathlib.Path(__file__).parent / 'tmp' / 'nss.json'
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text('{}')

    os.environ['NSS_SETTINGS'] = str(f)

    yield f
    clear_cache('settings')

    f.unlink()
