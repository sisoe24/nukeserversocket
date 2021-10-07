import pytest

from PySide2.QtWidgets import QCheckBox, QWidget

from src.widgets import settings_widget


@pytest.mark.usefixtures('myapp')
class TestSettingsWidget:

    @classmethod
    def setup_class(cls):
        cls.widget: QWidget = settings_widget.SettingsWidget()
        cls.checkboxes: QCheckBox = cls.widget.findChildren(QCheckBox)

    def test_checkboxes(self):
        checkbox: QCheckBox
        for checkbox in self.checkboxes:
            assert checkbox.isEnabled()
            assert checkbox.isCheckable()
