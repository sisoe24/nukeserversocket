from __future__ import annotations

import io
import sys
import traceback
import contextlib
from typing import Any, List, Generator


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


def exec_code(input_text: str, filename: str = '<user_code>') -> str:
    """Execute code with exec and returns its output.

    Accepts an optional filename argument for the source file is executing if
    there is an exception.

    ```
    result = exec_code("print('hello'.upper())")
    ```

    """
    with stdoutIO() as s:
        try:
            code_object = compile(input_text, filename, 'exec')
            exec(code_object, globals())
        except Exception:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            tb_lines = traceback.format_exception(exc_type, exc_value, exc_traceback)

            # remove the codebase line exec
            lines: List[str] = [
                line for line in tb_lines if f'File "{__file__}"' not in line
            ]
            return ''.join(lines)
        return s.getvalue()
