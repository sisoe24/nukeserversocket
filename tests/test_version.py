from __future__ import annotations

import re
from pathlib import Path

from nukeserversocket.version import __version__


def test_version_match():
    pyproject = Path(__file__).parent.parent / 'pyproject.toml'
    version = re.search(r'version = "(.*)"', pyproject.read_text())
    version = version[1] if version else 'unknown'
    assert __version__ == version, 'Version does not match pyproject.toml'
