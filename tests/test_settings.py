from __future__ import annotations

from nukeserversocket.settings import _NssSettings


def test_get_settings_default(mock_settings: _NssSettings):
    assert isinstance(mock_settings, _NssSettings)
    assert mock_settings.data == _NssSettings.defaults

    mock_settings.set('temp_value', True)
    assert mock_settings.get('temp_value') is True
    assert mock_settings.data['temp_value'] is True
    assert '"temp_value": true' in mock_settings.path.read_text()
