"""Test ToolBar class module."""
from collections import namedtuple

import pytest

from PySide2.QtWidgets import QWidget
from src.widgets import toolbar, settings_widget, about_widget

SETTINGS_WIDGET = settings_widget.SettingsWidget

Widgets = namedtuple('Widgets', ['widget', 'title', 'object_name'])

FLOATING_WIDGETS = (
    Widgets(about_widget.AboutWidget, 'About', 'AboutWidget'),
    Widgets(SETTINGS_WIDGET, 'Settings', 'SettingsWidget'),
)


@pytest.fixture()
def _toolbar(qtbot):
    """Initiate the ToolBar class."""
    widget = toolbar.ToolBar()
    qtbot.addWidget(widget)

    yield widget


def test_widget_no_obj_name(_toolbar):
    """Raise error if widget used for floating dialog has no object name."""
    with pytest.raises(RuntimeWarning):
        _toolbar._show_dialog(QWidget)


@pytest.mark.parametrize('widgets', FLOATING_WIDGETS,
                         ids=['About', 'Settings'])
def test_floating_dialog(_toolbar, widgets):
    """Create a Floating Dialog Widget."""
    dialog = _toolbar._show_dialog(widgets.widget)

    assert dialog.objectName() == widgets.object_name
    assert dialog.windowTitle() == widgets.title
    assert dialog.findChild(widgets.widget)


def test_is_floating_widget(_toolbar):
    """Check if dialog is a FloatingDialog instance."""
    dialog = _toolbar._show_dialog(SETTINGS_WIDGET)
    assert isinstance(dialog, toolbar.FloatingDialog)


def test_floating_dialog_already_active(_toolbar):
    """Check if toolbar action creates only once instance."""
    _toolbar._show_dialog(SETTINGS_WIDGET)
    dialog = _toolbar._show_dialog(SETTINGS_WIDGET)
    assert dialog == 'Already active'


@pytest.mark.skip(reason='need to find a proper way.')
def test_toolbar_floating_is_deleted(_toolbar):
    """Check if dialog triggers closeEvent."""
    dialog = _toolbar._show_dialog(SETTINGS_WIDGET)
    dialog.close()
    # assert that dialog gets deleted
