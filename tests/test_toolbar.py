from PySide2.QtWidgets import QDialog
import pytest

from src.widgets import toolbar, settings_widget

DIALOG = ('test', 'test', settings_widget.SettingsWidget)


@pytest.fixture()
def toolbar_obj(scope='module'):
    yield toolbar.ToolBar()


def test_toolbar_floating_dialog(toolbar_obj):
    """Create a Floating Dialog Widget"""
    dialog = toolbar_obj._show_dialog(*DIALOG)

    assert dialog.objectName() == 'test'
    assert dialog.windowTitle() == 'test'
    assert dialog.findChild(settings_widget.SettingsWidget)


def test_toolbar_floating_dialog_already_on(toolbar_obj):
    """Check if dialog gets only once instance."""
    toolbar_obj._show_dialog(*DIALOG)
    dialog = toolbar_obj._show_dialog(*DIALOG)
    assert dialog == 'Already active'


def test_toolbar_floating_is_deleted(toolbar_obj):
    """Check if dialog gets closed."""
    dialog = toolbar_obj._show_dialog(*DIALOG)
    dialog.close()
    assert dialog.isVisible() is False
