from __future__ import annotations

import pathlib


def _get_root(max_depth: int = 5):
    """Get the root package directory.

    Simple function to get the root package directory. This is used to find the
    root package without having to worry if any changes are made to the package
    directory structure.

    """
    path = pathlib.Path(__file__).parent
    for _ in range(max_depth):
        if path.name == 'NukeServerSocket' and (path / 'pyproject.toml').exists():
            return path
        path = path.parent
    raise FileNotFoundError('Root package not found within the depth limit.')


ROOT = _get_root()
