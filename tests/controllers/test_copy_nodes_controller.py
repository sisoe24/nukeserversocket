"""Test the _CopyNodesController class."""
import os

import pytest

from src.main import init_settings
from src.settings import AppSettings
from src.controllers import nuke_controllers as se

pytestmark = pytest.mark.controllers


@pytest.fixture()
def _transfer_file():
    """Get the transfer file path from the settings value.

    Before and after tests, will delete the file if it exists already.
    """
    def _delete_file():
        """If transfer_file exists, delete it."""
        if os.path.exists(path):
            os.remove(path)

    init_settings()

    settings = AppSettings()
    path = settings.value('path/transfer_file')

    _delete_file()

    yield path

    _delete_file()


@pytest.fixture()
def _nodes_controller(_init_fake_editor):
    """Init _CopyNodesController class.

    Before and after each tests, clear the text widgets.
    """
    controller = se._CopyNodesController()

    yield controller


def test_nodes_controller_output(_nodes_controller):
    """Check that the output method was overridden."""
    assert _nodes_controller.output() == 'Nodes received.'


def test_nodes_controller_wrapper(_nodes_controller, _transfer_file):
    """Check nodes controller wrapper command.

    Wrapper should be a valid stringified nuke command.
    """
    expected = "nuke.nodePaste('{}')".format(_transfer_file)
    result = _nodes_controller._paste_nodes_wrapper(_transfer_file)

    assert result == expected


def test_nodes_controller_file_content(_nodes_controller, _transfer_file):
    """Check if file gets created and has the right content."""
    _nodes_controller.set_input('random')

    with open(_transfer_file) as file:
        assert 'random' in file.read()
