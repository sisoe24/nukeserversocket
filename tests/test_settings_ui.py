from __future__ import annotations

import pytest
from pytestqt.qtbot import QtBot

from nukeserversocket.settings import _NssSettings
from nukeserversocket.settings_ui import (NssSettingsView, NssSettingsModel,
                                          NssSettingsController)

View = NssSettingsView
Controller = NssSettingsController
Model = NssSettingsModel


@pytest.fixture()
def model(mock_settings: _NssSettings):
    return Model(mock_settings)


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
    assert controller._view.timeout.value() == 60
    assert controller._view.auto_start.isChecked() is False
    assert controller._view.allow_lan.isChecked() is False
    assert controller._view.vision.isChecked() is True
    assert controller._view.mirror_script_editor.isChecked() is False
    assert controller._view.clear_output.isChecked() is True
    assert controller._view.format_output.text() == '[%d NukeTools] %F%n%t'

    # change values
    view.timeout.setValue(2)
    view.auto_start.setChecked(True)
    view.allow_lan.setChecked(True)
    view.vision.setChecked(False)
    view.mirror_script_editor.setChecked(True)
    view.clear_output.setChecked(False)
    view.format_output.setText('nuketools')

    assert model.settings.data['server_timeout'] == 120000
    assert model.settings.data['auto_start'] is True
    assert model.settings.data['allow_lan'] is True
    assert model.settings.data['vision'] is False
    assert model.settings.data['mirror_script_editor'] is True
    assert model.settings.data['clear_output'] is False
    assert model.settings.data['format_output'] == 'nuketools'


def test_tools_file_is_saved(controller: Controller, model: Model, view: View, monkeypatch):
    monkeypatch.delenv('NSS_TOOLS', raising=False)
    controller.init()
    assert view.tools_file.text() == ''
    assert view.tools_file.isEnabled() is True

    view.tools_file.setText(' /home/me/nss_tools.json ')
    view.tools_file.editingFinished.emit()

    assert model.settings.data['tools_file'] == '/home/me/nss_tools.json'
    assert model.settings.tools_file() == ('/home/me/nss_tools.json', False)


def test_tools_file_from_nss_tools_is_read_only(controller: Controller, model: Model,
                                                view: View, monkeypatch):
    model.settings.set('tools_file', '/home/me/nss_tools.json')
    monkeypatch.setenv('NSS_TOOLS', '/studio/nss_tools.json')

    controller.init()

    assert view.tools_file.text() == '/studio/nss_tools.json'
    assert view.tools_file.isEnabled() is False
    assert view.tools_file_browse.isEnabled() is False
    assert view.tools_file_sample.isEnabled() is False
    assert view.tools_file_note.isVisibleTo(view) is True
    assert model.settings.tools_file() == ('/studio/nss_tools.json', True)


def test_create_sample_uses_the_new_file(controller: Controller, model: Model, view: View,
                                         monkeypatch, tmp_path):
    monkeypatch.delenv('NSS_TOOLS', raising=False)
    monkeypatch.setattr(view, 'choose_sample_folder', lambda: str(tmp_path))

    view.tools_file_sample.click()

    path = str(tmp_path / 'nss_tools.json')
    assert view.tools_file.text() == path
    assert model.settings.tools_file() == (path, False)


def test_open_folder_opens_the_tools_file_folder(controller: Controller, view: View, monkeypatch):
    opened = []
    monkeypatch.setattr('nukeserversocket.settings_ui.QDesktopServices.openUrl', opened.append)
    view.tools_file.setText('/studio/tools/nss_tools.json')

    view.tools_file_open.click()

    assert [url.toLocalFile() for url in opened] == ['/studio/tools']
