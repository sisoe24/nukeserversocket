"""Configuration file for controller tests."""

import pytest

from src.widgets.fake_script_editor import FakeScriptEditor


@pytest.fixture()
def _init_fake_editor(qtbot):
    """Initialize the FakeScriptEditor class."""
    widget = FakeScriptEditor()
    qtbot.addWidget(widget)
    yield widget
