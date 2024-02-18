from __future__ import annotations

from nukeserversocket.settings import _NssSettings


def test_get_settings_default(settings: _NssSettings):
    assert isinstance(settings, _NssSettings)
    assert settings.data == _NssSettings.defaults

    settings.set('temp_value', True)
    assert settings.get('temp_value') is True
    assert settings.data['temp_value'] is True
    assert '"temp_value": true' in settings.path.read_text()
