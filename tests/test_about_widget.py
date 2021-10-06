import os
import requests

import pytest

from src import about
from src.widgets import about_widget


@pytest.mark.usefixtures('myapp')
class TestAboutWidget:

    @classmethod
    def setup_class(cls):
        cls.widget = about_widget.AboutWidget()
        cls._form_layout = cls.widget._form_layout
        cls._grid_layout = cls.widget._grid_layout

    def test_about_form(self):
        """Test if the form layout has the proper about information."""
        about_list = []
        for i in about.about():
            about_list.append(i.label)
            about_list.append(i.repr)

        for index, item in enumerate(about_list):
            widget = self._form_layout.itemAt(index).widget()
            assert item == widget.text()

    def test_about_grid(self):
        """Test if grid layout has the proper about information."""
        for index, link in enumerate(about.about_links()):
            widget = self._grid_layout.itemAt(index).widget()
            assert widget.text() == link.label
            assert widget.property('link') == link.repr

    def test_about_buttons(self):
        """Test if about buttons are enabled"""
        for index, _ in enumerate(about.about_links()):
            widget = self._grid_layout.itemAt(index).widget()
            assert widget.isEnabled()


@pytest.mark.skip(reason='should be done once in a while')
def test_about_links():
    """Test if about links are reachable."""
    for link in about.about_links():

        # Logs is a system path
        if link.label == 'Logs':
            assert os.path.exists(link.repr.replace('file:///', ''))
            continue

        # TODO: would like to use only included modules
        assert requests.get(link.repr, allow_redirects=True).status_code == 200
