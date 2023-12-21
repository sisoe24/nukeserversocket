from __future__ import annotations

import pathlib

from nukeserversocket.settings import _NssSettings, get_settings


def test_get_settings(tmp_settings: pathlib.Path):
    settings = get_settings()
    assert isinstance(settings, _NssSettings)
    assert settings.data == _NssSettings.defaults

    assert settings.get('temp_value') is None
    settings.set('temp_value', True)
    assert settings.get('temp_value') is True

    assert '"temp_value": true' in tmp_settings.read_text()
