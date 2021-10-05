import pytest

from tests.run_app import _MainWindow


@pytest.fixture()
def main_app(qtbot):

    widget = _MainWindow()
    widget.show()
    qtbot.addWidget(widget)

    yield widget.main_window.main_app


@pytest.fixture()
def connection_widgets(main_app):
    yield main_app.connections
