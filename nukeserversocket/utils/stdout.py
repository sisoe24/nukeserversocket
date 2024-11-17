from __future__ import annotations

import io
import sys
import contextlib
from typing import Any, Generator


@contextlib.contextmanager
def stdoutIO(stdout: Any = None) -> Generator[Any, Any, None]:
    """Get output from sys.stdout after executing code from `exec`.

    ```
    with stdoutIO() as s:
        exec(text, globals())
        return s.getvalue()
    ```

    ref: https://stackoverflow.com/a/3906390/9392852

    """
    old = sys.stdout
    if stdout is None:
        stdout = io.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old
