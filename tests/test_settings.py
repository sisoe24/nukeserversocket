from __future__ import annotations

from nukeserversocket.settings import _NssSettings, _nss_settings_path


def test_get_settings_default(mock_settings: _NssSettings):
    assert mock_settings.data == _NssSettings.defaults

    mock_settings.set('temp_value', True)
    assert mock_settings.get('temp_value') is True
    assert mock_settings.data['temp_value'] is True
    assert '"temp_value": true' in mock_settings.path.read_text()


def test_settings_path_creates_missing_nuke_dir(tmp_path, monkeypatch):
    monkeypatch.delenv('NSS_SETTINGS', raising=False)
    monkeypatch.setenv('HOME', str(tmp_path))
    monkeypatch.setenv('USERPROFILE', str(tmp_path))

    path = _nss_settings_path()

    assert path == tmp_path / '.nuke' / 'nukeserversocket.json'
    assert path.read_text() == '{}'
