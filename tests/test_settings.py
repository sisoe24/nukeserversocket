from __future__ import annotations

from nukeserversocket.settings import _NssSettings


def test_get_settings_default(get_settings: _NssSettings):
    assert isinstance(get_settings, _NssSettings)
    assert get_settings.data == _NssSettings.defaults

    get_settings.set('temp_value', True)
    assert get_settings.get('temp_value') is True
    assert get_settings.data['temp_value'] is True
    assert '"temp_value": true' in get_settings.path.read_text()
