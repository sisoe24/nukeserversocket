from __future__ import annotations

import io

from nukeserversocket.utils import stdoutIO, exec_code


def test_stdoutIO_captures_output():
    with stdoutIO() as s:
        print('Hello, World!')
    output = s.getvalue()
    assert output == 'Hello, World!\n'


def test_stdoutIO_custom_stdout():
    custom_stdout = io.StringIO()
    with stdoutIO(custom_stdout) as s:
        print('Custom stdout test')
    output = s.getvalue()
    assert output == 'Custom stdout test\n'
    assert custom_stdout is s


def test_exec_code_print_statement():
    result = exec_code("print('Hello from exec_code')")
    assert result == 'Hello from exec_code\n'


def test_exec_code_variable_assignment():
    result = exec_code('a = 5\nprint(a)')
    assert result == '5\n'


def test_exec_code_runtime_error():
    result = exec_code('1/0')
    assert 'ZeroDivisionError' in result
    assert 'division by zero' in result


def test_exec_code_exception_traceback_excludes_current_file():
    result = exec_code("raise ValueError('Test error')")
    assert 'ValueError: Test error' in result
    assert f'File "{__file__}"' not in result


def test_exec_code_custom_filename_in_exception():
    result = exec_code("raise IndexError('Index error')", filename='custom_script.py')
    assert 'IndexError: Index error' in result
    assert 'File "custom_script.py"' in result
