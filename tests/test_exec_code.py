from __future__ import annotations

import sys

import pytest

from nukeserversocket.utils import exec_code


def test_exec_code_print_statement():
    result = exec_code("print('Hello from exec_code')")
    assert result == 'Hello from exec_code\n'


def test_exec_code_runtime_error():
    result = exec_code('1/0')
    assert 'ZeroDivisionError' in result
    assert 'division by zero' in result


def test_exec_code_exception_traceback_excludes_exec_code_file():
    result = exec_code("raise ValueError('Test error')")
    assert 'ValueError: Test error' in result
    assert f'File "{exec_code.__code__.co_filename}"' not in result


def test_exec_code_custom_filename_in_exception():
    result = exec_code("raise IndexError('Index error')", filename='custom_script.py')
    assert 'IndexError: Index error' in result
    assert 'File "custom_script.py"' in result


def test_stdoutIO_restores_stdout_on_system_exit():
    old = sys.stdout
    with pytest.raises(SystemExit):
        exec_code('import sys; sys.exit(0)')
    assert sys.stdout is old
