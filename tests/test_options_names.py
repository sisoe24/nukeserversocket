import os
import re

from src.widgets import settings_widget


def options_name():
    settings = settings_widget.SettingsWidget()
    checkboxes = settings.findChildren(settings_widget.CheckBox)
    return [x.text().lower().replace(' ', '_') for x in checkboxes]


def travers_dir(package):
    for dirpath, _, filenames in os.walk(package):
        for filename in filenames:
            if filename.endswith('py'):
                fp = os.path.join(dirpath, filename)
                yield fp


def test_options_names(package):
    """Search for all of the files that are using the settings system, and confirm
    that the options name are valid.

    Because the settings is referenced with a string and usually if no settings is
    found, will be replaced with a default value, is handy to check if names are
    in line with the default checkboxes text.
    """
    options = options_name()

    for file in travers_dir(package):
        with open(file) as f:
            content = f.read()
            if re.search(r'AppSettings', content):
                opts = re.findall(r'(?<=options/)\w+', content)
                for opt in opts:
                    msg = 'Option name was not update in file: {}'.format(file)
                    assert opt in options, msg
