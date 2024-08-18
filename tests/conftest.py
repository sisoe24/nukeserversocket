from __future__ import annotations

import os
import sys
import logging
import pathlib

import pytest

# from nukeserversocket.settings import _NssSettings

SETTINGS_FILE = pathlib.Path(__file__).parent / 'tmp' / 'nss.json'
SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)

root = pathlib.Path(__file__).parent.parent / 'nukeserversocket'
print('➡ root:', root)
sys.path.append(str(root))
print('➡ root:', root)

print('Python version:', sys.version)
print('sys.path in conftest:', sys.path)
print('Current working directory:', os.getcwd())
print('Contents of current directory:', os.listdir())

try:
    import nukeserversocket
    print('nukeserversocket imported successfully')
    print('nukeserversocket.__file__:', nukeserversocket.__file__)

    from nukeserversocket import settings
    print('settings imported successfully')
    print('settings.__file__:', settings.__file__)

    from nukeserversocket.settings import _NssSettings
    print('_NssSettings imported successfully')
except ImportError as e:
    print('Import error:', str(e))
    print('Traceback:', e.__traceback__)


@pytest.fixture(scope='session', autouse=True)
def patch_logger():
    logger = logging.getLogger('nukeserversocket')
    logger.handlers.clear()


@pytest.fixture()
def mock_settings():
    SETTINGS_FILE.write_text('{}')

    os.environ['NSS_SETTINGS'] = str(SETTINGS_FILE)
    yield SETTINGS_FILE

    SETTINGS_FILE.write_text('{}')


@pytest.fixture()
def nss_settings(mock_settings: pathlib.Path):
    return _NssSettings(mock_settings)
