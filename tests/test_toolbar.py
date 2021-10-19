import pytest
from collections import namedtuple


from PySide2.QtWidgets import QWidget
from src.widgets import toolbar, settings_widget, about_widget

SETTINGS_WIDGET = settings_widget.SettingsWidget

Widgets = namedtuple('Widgets', ['widget', 'title', 'object_name'])

FLOATING_WIDGETS = (
    Widgets(about_widget.AboutWidget, 'About', 'AboutWidget'),
    Widgets(SETTINGS_WIDGET, 'Settings', 'SettingsWidget'),
)


@pytest.fixture()
def toolbar_obj(qtbot):
    widget = toolbar.ToolBar()
    qtbot.addWidget(widget)

    yield widget


def test_widget_no_obj_name(toolbar_obj):
    """If widget used to create a floating dialog has no object name raise Error."""
    with pytest.raises(RuntimeWarning):
        toolbar_obj._show_dialog(QWidget)


@pytest.mark.parametrize('widgets', FLOATING_WIDGETS, ids=['About', 'Settings'])
def test_toolbar_floating_dialog(toolbar_obj, widgets):
    """Create a Floating Dialog Widget"""
    dialog = toolbar_obj._show_dialog(widgets.widget)

    assert dialog.objectName() == widgets.object_name
    assert dialog.windowTitle() == widgets.title
    assert dialog.findChild(widgets.widget)


def test_toolbar_floating_dialog_already_on(toolbar_obj):
    """Check if dialog gets only once instance."""
    toolbar_obj._show_dialog(SETTINGS_WIDGET)
    dialog = toolbar_obj._show_dialog(SETTINGS_WIDGET)
    assert dialog == 'Already active'


def test_toolbar_floating_is_deleted(toolbar_obj):
    """Check if dialog gets closed."""
    dialog = toolbar_obj._show_dialog(SETTINGS_WIDGET)
    dialog.close()
    assert dialog.isVisible() is False
