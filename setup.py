# -*- coding: utf-8 -*-
import io
import os

from setuptools import find_packages, setup

# Package meta-data.
NAME = 'NukeServerSocket'
DESCRIPTION = 'A Nuke that plugin that will allow code execution inside Nuke from the local network.'
URL = 'https://github.com/sisoe24/NukeServerSocket'
EMAIL = 'virgilsisoe@gmail.com'
AUTHOR = 'Virgil Sisoe'
REQUIRES_PYTHON = '>=2.7.16'
VERSION = '0.0.1'

REQUIRED = [
    'pyside2==5.12.2'
]

EXTRAS = {
    "test": ['pytest']
}

here = os.path.abspath(os.path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
try:
    with io.open(os.path.join(here, 'README.md'), encoding='utf-8') as f:
        long_description = '\n' + f.read()
except FileNotFoundError:
    long_description = DESCRIPTION


setup(
    name=NAME,
    version=about['__version__'],
    description=DESCRIPTION,
    long_description=long_description,
    long_description_content_type='text/markdown',
    author=AUTHOR,
    author_email=EMAIL,
    python_requires=REQUIRES_PYTHON,
    url=URL,
    packages=find_packages(
        exclude=["tests", "*.tests", "*.tests.*", "tests.*"]),

    # If your package is a single module, use this instead of 'packages':
    # py_modules=['mypackage'],

    install_requires=REQUIRED,
    extras_require=EXTRAS,
    include_package_data=True,
    license='MIT',
)
