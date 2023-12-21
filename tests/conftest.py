from __future__ import annotations

import os
import pathlib

import pytest


@pytest.fixture()
def tmp_settings():
    f = pathlib.Path(__file__).parent / 'tmp' / 'nss.json'
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text('{}')

    os.environ['NSS_SETTINGS'] = str(f)
    yield f
    f.unlink()
