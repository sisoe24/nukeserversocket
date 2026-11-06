# Houdini

nukeserversocket also runs code in Houdini. You do not need Nuke installed.

These instructions assume nukeserversocket was installed with NukeTools in `$HOME/.nuke/NukeTools`. If you installed it manually, adjust the paths.

## Install with HOUDINI_PACKAGE_DIR

Add to your shell configuration.

**Mac/Linux** (`.bashrc` or `.zshrc`):

```bash
export HOUDINI_PACKAGE_DIR=$HOME/.nuke/NukeTools/nukeserversocket
```

**Windows:**

- Add `HOUDINI_PACKAGE_DIR` to Environment Variables (start menu).
- Set the value to `%USERPROFILE%\.nuke\NukeTools\nukeserversocket`.

For CMD or PowerShell, see Microsoft's documentation on environment variables.

## Install with a Houdini package file

1. Go to your Houdini packages folder:
   - Windows: `C:/Users/YourName/Documents/houdiniXX.X/packages`
   - Mac: `~/Library/Preferences/houdini/XX.X/packages`
   - Linux: `~/houdiniXX.X/packages`

2. Create `nukeserversocket.json`:

```json
{
    "hpath": [
        "$HOME/.nuke/NukeTools/nukeserversocket/nukeserversocket/controllers/houdini"
    ],
    "env": [
        {
            "PYTHONPATH": "$HOME/.nuke/NukeTools/nukeserversocket"
        }
    ]
}
```

## Notes

Only the Server Timeout, Auto Start and Allow LAN Connections settings apply to Houdini.

Houdini runs the code with Python's `exec`. Nuke runs it in its Script Editor.
