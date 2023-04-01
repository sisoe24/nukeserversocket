"""Test the CodeEditor class."""
import json

import pytest

from nukeserversocket.network import DataCode
from nukeserversocket.controllers import nuke_controllers as se


@pytest.mark.usefixtures('_init_fake_editor')
class TestCodeEditor:
    """Test the Code Editor class initialization.

    Each CodeEditor must be initialized with a DataCode object.
    """

    @pytest.mark.parametrize('file', ['file.py', ''])
    def test_is_python_controller(self, file):
        """Check if is a valid PyController when file ends .py, None."""
        controller = se.get_controllers(file)
        assert isinstance(controller, se._PyController)

    @pytest.mark.parametrize('file', ['file.cpp', 'file.blink'])
    def test_is_blink_controller(self, file):
        """Check if is a valid BlinkController when file ends .cpp, .blink."""
        controller = se.get_controllers(file)
        assert isinstance(controller, se._BlinkController)

    def test_is_nodes_controller(self):
        """Check if is a valid CopyNodesController when file ends .tmp."""
        controller = se.get_controllers(file='file.tmp')
        assert isinstance(controller, se._CopyNodesController)

    def test_execute_script_editor_code(self):
        """Test executing code from the script editor instead of nuke internal."""
        code = 'print("hello".upper())'
        controller = se.get_controllers(file='tmp.py')

        # when bypassing the main execute function, need to set the input
        controller.set_input(code)
        controller._execute_script_editor()
        assert controller.output() == 'HELLO\n'
