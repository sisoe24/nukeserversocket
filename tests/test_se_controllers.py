from enum import auto
import os
import subprocess

from textwrap import dedent
from subprocess import check_output

import pytest
from PySide2.QtWidgets import QPushButton

from .run_local import _MainWindowWidget

from src.utils import AppSettings
from src.main import init_settings
from src.script_editor import nuke_se
from src.widgets import fake_script_editor as fake_se
from src.script_editor import nuke_se_controllers as se


@pytest.fixture(autouse=True)
def init_fake_editor(qtbot):
    widget = fake_se.FakeScriptEditor()
    qtbot.addWidget(widget)
    yield widget


class TestCodeEditor:
    """Test the Code Editor class initialization"""

    @pytest.mark.parametrize('file', ['file.py', ''])
    def test_is_python_controller(self, file):
        """Check if is a valid PyController when passed a .py or no file"""
        editor = se.CodeEditor(file)
        assert isinstance(editor.controller, se._PyController)

    @pytest.mark.parametrize('file', ['file.cpp', 'file.blink'])
    def test_is_blink_controller(self, file):
        """Check if is a valid BlinkController when passed a .cpp|.blink file"""
        editor = se.CodeEditor(file)
        assert isinstance(editor.controller, se._BlinkController)

    def test_is_nodes_controller(self):
        """Check if is a valid CopyNodesController when passed a .tmp file"""
        editor = se.CodeEditor('file.tmp')
        assert isinstance(editor.controller, se._CopyNodesController)


class TestNodesCopyController:
    """Test the NodeCopyEditor class."""

    file_content = 'Test Msg'
    transfer_file = AppSettings().value('path/transfer_file')

    @pytest.fixture(autouse=True, scope='class')
    def clean_file(self):
        """Clean transfer file nodes."""
        path = self.transfer_file
        if os.path.exists(path):
            os.remove(path)

    @pytest.fixture(scope='class')
    def nodes_controller(self):
        """Init node controller class"""
        init_settings()

        controller = se._CopyNodesController()
        controller.set_input(self.file_content)

        yield controller

        se.ScriptEditorController().set_input('')

    def test_nodes_controller_input_result(self, nodes_controller):
        """Check if set input returns valid Nuke string."""
        expected = "nuke.nodePaste('{}')".format(self.transfer_file)
        result = nodes_controller._paste_nodes_wrapper(self.transfer_file)
        assert result == expected

    def test_nodes_controller_output(self, nodes_controller):
        """Check that the output method was overridden."""
        assert nodes_controller.output() == 'Nodes received.'

    def test_transfer_file_created(self):
        """Check if file gets created."""
        assert os.path.exists(self.transfer_file)

    def test_nodes_controller_file_content(self):
        """Check if file has the right content."""
        with open(self.transfer_file) as file:
            assert self.file_content in file.read()


class TestBlinkController:
    wrapper = dedent("""
    nodes = [n for n in nuke.allNodes() if "tmp.cpp" == n.name()]
    try:
        node = nodes[0]
    except IndexError:
        node = nuke.createNode('BlinkScript', 'name tmp.cpp')
    finally:
        knobs = node.knobs()
        knobs['kernelSourceFile'].setValue('file/to/tmp.cpp')
        knobs['kernelSource'].setText("TEST CODE")
        knobs['recompile'].execute()
    """).strip()

    @pytest.fixture(scope='class')
    def blink_controller(self):
        controller = se._BlinkController('file/to/tmp.cpp')
        yield controller
        se.ScriptEditorController().set_input('')

    def test_blink_output(self, blink_controller):
        """Check that the output method was overridden."""
        assert blink_controller.output() == 'Recompiling'

    def test_blink_wrapper(self, blink_controller):
        """Check the blink wrapper nuke commands."""
        wrapper = blink_controller._blink_wrapper("TEST CODE")
        assert self.wrapper == wrapper

    def test_set_input(self, blink_controller):
        blink_controller.set_input('TEST CODE')
        assert blink_controller.input() == self.wrapper


@pytest.mark.quicktest
class TestNukeSe:
    """Test base Nuke Script editor class"""

    @pytest.fixture()
    def editor(self, monkeypatch):
        """Initialize the editor"""
        se_editor = nuke_se.NukeScriptEditor()
        monkeypatch.setattr(nuke_se, 'editors_widgets', {})

        yield se_editor

    def test_get_run_button(self, editor):
        """Check if run button was found."""
        assert isinstance(editor.get_run_button('Run'), QPushButton)

    def test_run_button_not_found(self, editor):
        """Check if run button was not found."""
        assert editor.get_run_button('test') is None

    def test_execute_shortcut(self, editor):
        """Check if execute shortcut is working when run button is not found."""
        se_controller = se.ScriptEditorController()
        input_text = se_controller.input()

        editor._run_button = None
        editor.execute()

        assert se_controller.output() == subprocess.check_output(
            ['python', '-c', input_text], encoding='utf-8')

    def test_get_script_editor(self, editor):
        """Check if script editor was found."""
        assert isinstance(editor.script_editor, fake_se.FakeScriptEditor)

    def test_script_editor_not_found(self, editor):
        """Check if script editor was not found."""
        with pytest.raises(RuntimeWarning, match='NukeServerSocket: Script Editor panel not found.+'):
            editor.get_script_editor('scripteditor.3')
