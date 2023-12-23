from __future__ import annotations

import pathlib

import pytest
from pytestqt.qtbot import QtBot

from nukeserversocket.settings import _NssSettings
from nukeserversocket.settings_ui import (NssSettingsView, NssSettingsModel,
                                          NssSettingsController)

View = NssSettingsView
Controller = NssSettingsController
Model = NssSettingsModel


@pytest.fixture()
def model(tmp_settings: pathlib.Path):
    return Model(_NssSettings(tmp_settings))


@pytest.fixture()
def view(qtbot: QtBot) -> View:
    view = View()
    qtbot.addWidget(view)
    return view


@pytest.fixture()
def controller(model: Model, view: View) -> Controller:
    return Controller(view, model)


def test_settings(controller: Controller, model: Model, view: View):

    controller.init()

    # default values
    assert model.settings.data['server_timeout'] == 60000
    assert model.settings.data['mirror_script_editor'] is False
    assert model.settings.data['clear_output'] is True
    assert model.settings.data['format_output'] == '[%d NukeTools] %F%n%t'

    assert controller._view.timeout.value() == 1
    assert controller._view.mirror_script_editor.isChecked() is False
    assert controller._view.clear_output.isChecked() is True
    assert controller._view.format_output.text() == '[%d NukeTools] %F%n%t'

    # change values
    view.timeout.setValue(2)
    view.mirror_script_editor.setChecked(True)
    view.clear_output.setChecked(False)
    view.format_output.setText('nuketools')

    assert model.settings.data['server_timeout'] == 120000
    assert model.settings.data['mirror_script_editor'] is True
    assert model.settings.data['clear_output'] is False
    assert model.settings.data['format_output'] == 'nuketools'

    assert controller._view.timeout.value() == 2
    assert controller._view.mirror_script_editor.isChecked() is True
    assert controller._view.clear_output.isChecked() is False
    assert controller._view.format_output.text() == 'nuketools'
