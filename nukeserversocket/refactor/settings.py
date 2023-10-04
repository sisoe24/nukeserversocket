
import os
import json
from typing import Any, Dict


class Settings:
    def __init__(self, settings_file: str):
        self._settings_file = settings_file
        self._settings = self.load(settings_file)

    def load(self, settings_file: str):
        with open(settings_file) as f:
            return json.load(f)

    def save(self):
        with open(self._settings_file, 'w') as f:
            json.dump(self._settings, f)

    def get(self, key: str, default: Any = None) -> Any:
        return self._settings.get(key, default)

    def set(self, key: str, value: Any):
        self._settings[key] = value
        self.save()


def nuke_settings():
    return os.path.join(os.path.expanduser('~/.nuke'), 'nukeserversocket.json')


_SETTINGS_CACHE: Dict[str, Settings] = {}


def get_settings():
    if _SETTINGS_CACHE.get('settings') is None:
        _SETTINGS_CACHE['settings'] = Settings(nuke_settings())
    return _SETTINGS_CACHE['settings']
