"""
The only way I found to safely test the app inside Nuke and in an isolate environment
is by adding the parent directory to sys.path (Equivalent to add do PYTHONPATH but less hardcoded).

When Nuke is loaded from CLI or from icon, will not properly load the modules if
they are not absolute imports with the name of the plugin.
When Nuke is loaded in CLI mode from the plug-in working directory it works fine
but obviously this will almost never be the case for external users.

Needs from investigation as I don't like to mess with sys path but it works for now.

Also should be noted that the app is launched in "module mode": (use vscode task RunApp)

    `python -m tests.test_app`

"""
import os
import sys

# HACK: The only way I found to safely test the app in isolate environment
# sys.path.insert(0, os.path.dirname(os.getcwd()))

# Don't write pyc files when testing, they just create problems
# XXX: doesn't seem to work?
sys.dont_write_bytecode = True
