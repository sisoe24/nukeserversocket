from __future__ import annotations

from nukeserversocket.settings import _NssSettings


def test_get_settings_default(nss_settings: _NssSettings):
    assert isinstance(nss_settings, _NssSettings)
    assert nss_settings.data == _NssSettings.defaults

    nss_settings.set('temp_value', True)
    assert nss_settings.get('temp_value') is True
    assert nss_settings.data['temp_value'] is True
    assert '"temp_value": true' in nss_settings.path.read_text()
