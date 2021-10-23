"""Test about widget."""
import os
import platform

import pytest
import requests

from src import about
from src.widgets import about_widget


def test_get_about_key():
    """Get a key from the about dictionary."""
    key = about.get_about_key('Python')
    assert key == platform.python_version()


def test_about_python_version():
    """Python version should be 3.7.7 for nuke 13 or 2.7.16 for nuke11/12."""
    version = about.get_about_key('Python')
    assert version <= '3.7.7'


def test_get_about_missing_key():
    """Get a key that is not present in about dictionary."""
    key = about.get_about_key('Maya')
    assert key == ''


def test_about_to_string():
    """Check if the about data is converted into a string."""
    keys = about.about_to_string()
    assert isinstance(keys, str)


def test_about_to_string_exclude_key():
    """Get the about data in string format and exclude one key."""
    keys = about.about_to_string(exclude=['Python'])
    assert 'Python' not in keys


LINKS = about.about_links()


@pytest.fixture()
def _about_widget(qtbot):
    """Initiate about widget class."""
    widget = about_widget.AboutWidget()
    qtbot.addWidget(widget)
    yield widget


def test_about_form(_about_widget):
    """Test if the form layout has the proper about information."""
    about_list = []
    for label in about.about():
        about_list.append(label.label)
        about_list.append(label.repr)

    for index, item in enumerate(about_list):
        _widget = _about_widget._form_layout.itemAt(index).widget()
        assert item == _widget.text()


def test_about_grid(_about_widget):
    """Test if grid layout has the proper about information."""
    for index, link in enumerate(LINKS):
        _widget = _about_widget._grid_layout.itemAt(index).widget()
        assert _widget.text() == link.label
        assert _widget.property('link') == link.repr


def test_about_buttons(_about_widget):
    """Test if about buttons are enabled."""
    for index, _ in enumerate(LINKS):
        _widget = _about_widget._grid_layout.itemAt(index).widget()
        assert _widget.isEnabled()


@pytest.mark.web
@pytest.mark.parametrize('link', LINKS, ids=[i.label for i in LINKS])
def test_about_links(link):
    """Test if about link are reachable."""
    # Logs is a system path
    if link.label == 'Logs':
        assert os.path.exists(link.repr.replace('file:///', ''))
    else:
        # TODO: would like to use only included modules
        assert requests.get(link.repr, allow_redirects=True).status_code == 200
