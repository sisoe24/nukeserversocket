from __future__ import annotations

import sys
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).parent.parent


def test_import_from_repo_folder_on_nuke_path(tmp_path: Path):
    """The README install puts the repo folder on the path, so the code is one package deeper."""
    repo = tmp_path / 'nukeserversocket'
    shutil.copytree(ROOT / 'nukeserversocket', repo / 'nukeserversocket')
    shutil.copy(ROOT / '__init__.py', repo)

    result = subprocess.run(
        [sys.executable, '-c', 'from nukeserversocket import nukeserversocket; nukeserversocket.install_nuke'],
        cwd=tmp_path,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
