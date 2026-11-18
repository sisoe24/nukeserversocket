# Houdini

nukeserversocket also runs code in Houdini. You do not need Nuke installed.

These instructions assume nukeserversocket was installed with NukeTools in `$HOME/.nuke/NukeTools`. If you installed it manually, adjust the paths.

## Install with HOUDINI_PACKAGE_DIR

Add this line to your shell configuration file.

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

## Use

1. In a Houdini pane, click the tab menu (**+**).
2. Choose **NukeServerSocket**.
3. Click **Connect**.
4. Send code from a client, as you do for Nuke. See [clients.md](clients.md).

## Notes

- Houdini runs the code with Python's `exec`. Nuke runs it in its Script Editor.
- The Mirror Script Editor, Format Output and Clear Output settings apply only to Nuke.
- A tools file works in Houdini, but **Create sample...** makes a Nuke sample. Its adapter module imports `nuke`, so its tools do not load in Houdini. Adapters for Houdini must use `hou`.
- The [MCP server](mcp.md) supports only Nuke for now. Its tool and its instructions to the agent are written for Nuke.
