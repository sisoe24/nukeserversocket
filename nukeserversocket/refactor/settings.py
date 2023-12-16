
from __future__ import annotations

import os
import json
import pathlib
from typing import Any, Dict


class _NssSettings:
    defaults = {
        'port': 54321,
        'server_timeout': 10,
        'format_output': False,
    }

    def __init__(self, settings_file: pathlib.Path):
        self._settings_file = settings_file
        self._settings = self.load(settings_file)

        for key, value in self.defaults.items():
            self._settings.setdefault(key, value)

    def load(self, settings_file: pathlib.Path) -> Dict[str, Any]:
        with settings_file.open() as f:
            return json.load(f)

    def save(self):
        with self._settings_file.open('w') as f:
            json.dump(self._settings, f)

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        self._settings[key] = value
        self.save()


def _nss_settings() -> pathlib.Path:
    runtime_settings = os.environ.get('NUKE_SERVER_SOCKET_SETTINGS')
    if runtime_settings:
        return pathlib.Path(runtime_settings)

    file = pathlib.Path().home() / '.nuke' / 'nukeserversocket.json'

    if not os.path.exists(file):
        file.write_text('{}')

    return file


_SETTINGS_CACHE: Dict[str, _NssSettings] = {}


def get_settings():
    if _SETTINGS_CACHE.get('settings') is None:
        _SETTINGS_CACHE['settings'] = _NssSettings(_nss_settings())
    return _SETTINGS_CACHE['settings']
