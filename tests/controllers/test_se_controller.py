"""Test the Nuke Script Editor controller classes."""
import sys
import subprocess

import pytest
from PySide2.QtWidgets import (
    QPushButton,
    QPlainTextEdit,
    QTextEdit,
    QSplitter,
    QWidget
)

from src.script_editor import nuke_se
from src.utils import pyDecoder
from src.widgets import fake_script_editor as fake_se
from src.script_editor import nuke_se_controllers as se


@pytest.fixture()
def _nuke_editor(_init_fake_editor):
    """Initialize NukeScriptEditor.

    Tests in this class need to clean the editor cache each time.
    """
    se_editor = nuke_se.NukeScriptEditor()
    nuke_se.editors_widgets.clear()

    yield se_editor

    nuke_se.editors_widgets.clear()


def test_script_editor_is_widget(_nuke_editor):
    """Check if script editor was found and is a QWidget."""
    assert isinstance(_nuke_editor._find_script_editor(), QWidget)


def test_get_script_editor(_nuke_editor):
    """Check if script editor was found and is a FakeScriptEditor."""
    assert isinstance(_nuke_editor.script_editor, fake_se.FakeScriptEditor)


def test_script_editor_not_found(_nuke_editor):
    """Check if script editor was not found."""
    msg = 'NukeServerSocket: Script Editor panel not found.+'
    with pytest.raises(RuntimeWarning, match=msg):
        _nuke_editor._find_script_editor('scripteditor.3')


def test_get_run_button(_nuke_editor):
    """Check if run button was found and is a QPushButton."""
    assert isinstance(_nuke_editor._find_run_button('Run'), QPushButton)


def test_find_input_widget(_nuke_editor):
    """Check if input editor widget was found and is a QPlainTextEdit."""
    assert isinstance(_nuke_editor._find_input_widget(), QPlainTextEdit)


def test_find_output_widget(_nuke_editor):
    """Check if output editor widget was found and is a QTextEdit."""
    assert isinstance(_nuke_editor._find_output_widget(), QTextEdit)


def test_find_console(_nuke_editor):
    """Check if console was found and is a QSplitter."""
    assert isinstance(_nuke_editor._find_console(), QSplitter)


def test_run_button_not_found(_nuke_editor):
    """Check if run button returns None if not found."""
    assert _nuke_editor._find_run_button('test') is None


def test_execute_shortcut(_init_fake_editor):
    """Check if shortcut will execute the code when run button is not found."""
    se_controller = se.ScriptEditorController()
    se_controller.set_input('print("hello".upper())')

    input_text = se_controller.input()

    se_controller.script_editor._run_button = None
    se_controller.execute()

    code = subprocess.check_output([sys.executable, '-c', input_text])
    assert se_controller.output() == pyDecoder(code)
