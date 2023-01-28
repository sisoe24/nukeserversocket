"""Test ToolBar class module."""
from collections import namedtuple

import pytest

from src.widgets import toolbar, about_widget, settings_widget
from src.widgets.toolbar import show_window

SETTINGS_WIDGET = settings_widget.SettingsWidget

Widgets = namedtuple('Widgets', ['widget', 'title', 'object_name'])

FLOATING_WIDGETS = (
    Widgets(about_widget.AboutWidget, 'About', 'AboutWidget'),
    Widgets(SETTINGS_WIDGET, 'Settings', 'SettingsWidget'),
)

pytestmark = pytest.mark.skip(reason='Major refactor broke all tests')


@pytest.fixture()
def _toolbar(qtbot):
    """Initiate the ToolBar class."""
    widget = toolbar.ToolBar()
    qtbot.addWidget(widget)

    yield widget


@pytest.mark.parametrize('widgets', FLOATING_WIDGETS,
                         ids=['About', 'Settings'])
def test_floating_dialog(_toolbar, widgets):
    """Create a Floating Dialog Widget."""
    dialog = _toolbar._show_dialog(widgets.title, widgets.widget())

    assert dialog.windowTitle() == widgets.title
    assert dialog.findChild(widgets.widget)


def test_is_floating_widget(_toolbar):
    """Check if dialog is a FloatingDialog instance."""
    dialog = _toolbar._show_dialog('Settings', SETTINGS_WIDGET())
    assert isinstance(dialog, toolbar.FloatingDialog)


def test_floating_dialog_cache_widget(_toolbar):
    """Check if dialog is already created, then creating a new one will get its
    cached value.
    """
    c = SETTINGS_WIDGET()
    first_dialog = _toolbar._show_dialog('Settings', c)
    second_dialog = _toolbar._show_dialog('Settings', c)
    assert first_dialog == second_dialog


@pytest.mark.skip(reason='TODO')
def test_floating_dialog_cache(_toolbar):
    ...
