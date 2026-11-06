
from __future__ import annotations

import os
import json
import pathlib
from pprint import pformat
from typing import Any, Dict, Tuple


class _NssSettings:
    defaults = {
        'port': 54321,
        'server_timeout': 3600000,
        'auto_start': False,
        'allow_lan': False,
        'mirror_script_editor': False,
        'clear_output': True,
        'format_output': '[%d NukeTools] %F%n%t',
        # NSS_TOOLS overrides it, see tools_file()
        'tools_file': '',
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

    def tools_file(self) -> Tuple[str, bool]:
        """Return the tools file path ('' for none) and whether NSS_TOOLS set it.

        NSS_TOOLS wins, so a studio can set the file where artists cannot change it.
        """
        env = os.environ.get('NSS_TOOLS', '')
        return (env, True) if env else (self.get('tools_file') or '', False)


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
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text('{}')

    return file


def get_settings() -> _NssSettings:
    """Load the settings from the settings file."""
    return _NssSettings(_nss_settings_path())
