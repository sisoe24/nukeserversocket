"""Test the _BlinkController class."""
from textwrap import dedent

import pytest

from src.controllers.nuke_controllers import _BlinkController


NUKE_CMD = dedent("""
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


pytestmark = pytest.mark.controllers


@pytest.fixture()
def _blink_controller(_init_fake_editor):
    """Initialize the _BlinkController class.

    Before and after each tests, clear the text widgets.
    """
    controller = _BlinkController('file/to/tmp.cpp')
    yield controller


def test_blink_output(_blink_controller):
    """Check that the output method was overridden."""
    assert _blink_controller.output() == 'Recompiling'


def test_blink_wrapper(_blink_controller):
    """Check the blink NUKE_CMD nuke command."""
    nuke_cmd = _blink_controller._blink_wrapper("TEST CODE")
    assert nuke_cmd == NUKE_CMD


def test_set_input(_blink_controller):
    """Check if input was set correctly."""
    _blink_controller.set_input('TEST CODE')
    assert _blink_controller.input() == NUKE_CMD
