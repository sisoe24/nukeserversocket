from __future__ import annotations

import os
import pathlib

import pytest

from nukeserversocket.settings import _NssSettings, get_settings


@pytest.fixture(scope='module', autouse=True)
def runtime_settings():
    f = pathlib.Path(__file__).parent / 'tmp' / 'nss.json'
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text('{}')

    os.environ['NSS_SETTINGS'] = str(f)
    yield f
    f.unlink()


def test_get_settings(runtime_settings: pathlib.Path):
    settings = get_settings()
    assert isinstance(settings, _NssSettings)
    assert settings.data == _NssSettings.defaults

    assert settings.get('temp_value') is None
    settings.set('temp_value', True)
    assert settings.get('temp_value') is True

    assert '"temp_value": true' in runtime_settings.read_text()
