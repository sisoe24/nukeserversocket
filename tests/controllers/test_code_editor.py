"""Test the CodeEditor class."""
import json

import pytest

from nukeserversocket.network import DataCode
from nukeserversocket.controllers import nuke_controllers as se


def _data_code(code='test', file=''):
    """Return a initialized DataCode object."""
    return DataCode(json.dumps({'text': code, 'file': file}))


@pytest.mark.usefixtures('_init_fake_editor')
class TestCodeEditor:
    """Test the Code Editor class initialization.

    Each CodeEditor must be initialized with a DataCode object.
    """

    @pytest.mark.parametrize('file', ['file.py', ''])
    def test_is_python_controller(self, file):
        """Check if is a valid PyController when file ends .py, None."""
        controller = se.controllers_factory(_data_code(file=file))
        assert isinstance(controller, se._PyController)

    @pytest.mark.parametrize('file', ['file.cpp', 'file.blink'])
    def test_is_blink_controller(self, file):
        """Check if is a valid BlinkController when file ends .cpp, .blink."""
        controller = se.controllers_factory(_data_code(file=file))
        assert isinstance(controller, se._BlinkController)

    def test_is_nodes_controller(self):
        """Check if is a valid CopyNodesController when file ends .tmp."""
        controller = se.controllers_factory(_data_code(file='file.tmp'))
        assert isinstance(controller, se._CopyNodesController)

    def test_execute_script_editor_code(self):
        """Test executing code from the script editor instead of nuke internal."""
        code = 'print("hello".upper())'
        controller = se.controllers_factory(_data_code(code, file='tmp.py'))

        # when bypassing the main execute function, need to set the input
        controller.set_input(code)
        controller._execute_script_editor()
        assert controller.output() == 'HELLO\n'
