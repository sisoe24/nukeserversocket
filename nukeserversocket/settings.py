
from __future__ import annotations

import os
import json
import pathlib
from pprint import pformat
from typing import Any, Dict

from .utils import cache


class _NssSettings:
    defaults = {
        'port': 54321,
        'server_timeout': 60000,
        'mirror_script_editor': False,
        'clear_output': True,
        'format_output': '[%d NukeTools] %F%n%t',
    }

    def __init__(self, settings_file: pathlib.Path):
        self.path = settings_file
        self.data = self.load(settings_file)

        for key, value in self.defaults.items():
            self.data.setdefault(key, value)

    def __str__(self) -> str:
        return pformat(self.data)

    def load(self, settings_file: pathlib.Path) -> Dict[str, Any]:
        with settings_file.open() as f:
            return json.load(f)

    def save(self):
        with self.path.open('w') as f:
            json.dump(self.data, f, indent=4)

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set(self, key: str, value: Any):
        self.data[key] = value
        self.save()


def _nss_settings_path() -> pathlib.Path:
    """Return the path to the settings file.

    The settings file is located in the user home directory under the .nuke folder
    but can be overridden by setting the `NSS_SETTINGS` environment

    """
    runtime_settings = os.environ.get('NSS_SETTINGS')
    if runtime_settings:
        return pathlib.Path(runtime_settings)

    file = pathlib.Path().home() / '.nuke' / 'nukeserversocket.json'

    if not os.path.exists(file):
        file.write_text('{}')

    return file


@cache('settings')
def get_settings():
    """A singleton instance of the settings.

    Always use this function to get the settings.

    """
    return _NssSettings(_nss_settings_path())
