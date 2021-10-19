"""Test the Nuke Script Editor controller classes."""
import os
import json
import subprocess

from textwrap import dedent

import pytest
from PySide2.QtWidgets import (
    QPushButton,
    QPlainTextEdit,
    QTextEdit,
    QSplitter,
    QWidget
)

from src.main import init_settings
from src.connection import DataCode
from src.script_editor import nuke_se
from src.utils import AppSettings, pyDecoder
from src.widgets import fake_script_editor as fake_se
from src.script_editor import nuke_se_controllers as se


@pytest.fixture(autouse=True)
def init_fake_editor(qtbot):
    """Initialize the Fake Script Editor."""
    # TODO why is this auto use
    widget = fake_se.FakeScriptEditor()
    qtbot.addWidget(widget)
    yield widget


def code(file):
    return DataCode(json.dumps({'text': 'test', 'file': file}))


class TestCodeEditor:
    """Test the Code Editor class initialization.

    Each Editor must be initialized with a DataCode object.
    """

    @pytest.mark.parametrize('file', ['file.py', ''])
    def test_is_python_controller(self, file):
        """Check if is a valid PyController when file ends .py or none."""
        editor = se.CodeEditor(code(file))
        assert isinstance(editor._controller, se._PyController)

    @pytest.mark.parametrize('file', ['file.cpp', 'file.blink'])
    def test_is_blink_controller(self, file):
        """Check if is a valid BlinkController when file ends .cpp|.blink."""
        editor = se.CodeEditor(code(file))

        assert isinstance(editor._controller, se._BlinkController)

    def test_is_nodes_controller(self):
        """Check if is a valid CopyNodesController when file ends .tmp."""
        editor = se.CodeEditor(code('file.tmp'))

        assert isinstance(editor._controller, se._CopyNodesController)


class TestNodesCopyController:
    """Test the NodeCopyEditor class."""

    file_content = 'Test Msg'

    @pytest.fixture()
    def transfer_file(self):
        """Get the transfer file path from the settings."""
        settings = AppSettings()
        yield settings.value('path/transfer_file')

    @pytest.fixture()
    def nodes_controller(self):
        """Init node controller class."""
        init_settings()

        controller = se._CopyNodesController()
        controller.set_input(self.file_content)

        yield controller

        se.ScriptEditorController().set_input('')

    def test_nodes_controller_input_result(self, nodes_controller, transfer_file):
        """Check if set input returns valid Nuke string."""
        if os.path.exists(transfer_file):
            os.remove(transfer_file)

        expected = "nuke.nodePaste('{}')".format(transfer_file)
        result = nodes_controller._paste_nodes_wrapper(transfer_file)
        assert result == expected

    def test_nodes_controller_output(self, nodes_controller):
        """Check that the output method was overridden."""
        assert nodes_controller.output() == 'Nodes received.'

    def test_transfer_file_created(self, transfer_file):
        """Check if file gets created."""
        assert os.path.exists(transfer_file)

    def test_nodes_controller_file_content(self, transfer_file):
        """Check if file has the right content."""
        with open(transfer_file) as file:
            assert self.file_content in file.read()


class TestBlinkController:
    """Test the blink controller class."""

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
        """Get the blink controller class."""
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
        """Check if input was set correctly."""
        blink_controller.set_input('TEST CODE')
        assert blink_controller.input() == self.wrapper


class TestNukeSe:
    """Test base Nuke Script editor class."""

    @pytest.fixture()
    def editor(self, monkeypatch):
        """Initialize the editor.

        Tests in this class need to clean the editor cache each time.
        """
        se_editor = nuke_se.NukeScriptEditor()
        monkeypatch.setattr(nuke_se, 'editors_widgets', {})

        yield se_editor

    def test_get_run_button(self, editor):
        """Check if script editor was found."""
        assert isinstance(editor._find_script_editor(), QWidget)

    def test_get_run_button(self, editor):
        """Check if run button was found."""
        assert isinstance(editor._find_run_button('Run'), QPushButton)

    def _find_input_widget(self, editor):
        """Check if input editor widget was found."""
        assert isinstance(editor._find_input_widget(), QPlainTextEdit)

    def _find_output_widget(self, editor):
        """Check if output editor widget was found."""
        assert isinstance(editor._find_output_widget(), QTextEdit)

    def _find_console(self, editor):
        """Check if run button was found."""
        assert isinstance(editor._find_console(), QSplitter)

    def test_run_button_not_found(self, editor):
        """Check if run button was not found."""
        assert editor._find_run_button('test') is None

    def test_execute_shortcut(self, editor):
        """Check if shortcut is working when run button is not found."""
        se_controller = se.ScriptEditorController()
        input_text = se_controller.input()

        editor._run_button = None
        editor.execute()

        code = subprocess.check_output(['python', '-c', input_text])
        assert se_controller.output() == pyDecoder(code)

    def test_get_script_editor(self, editor):
        """Check if script editor was found."""
        assert isinstance(editor.script_editor, fake_se.FakeScriptEditor)

    def test_script_editor_not_found(self, editor):
        """Check if script editor was not found."""
        with pytest.raises(RuntimeWarning, match='NukeServerSocket: Script Editor panel not found.+'):
            editor._find_script_editor('scripteditor.3')
