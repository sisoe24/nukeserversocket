# nukeserversocket

[![Main Build](https://img.shields.io/github/v/release/sisoe24/nukeserversocket?label=stable)](https://github.com/sisoe24/nukeserversocket/releases)
[![Pre Release](https://img.shields.io/github/v/release/sisoe24/nukeserversocket?label=pre-release&include_prereleases)](https://github.com/sisoe24/nukeserversocket/releases)
![Last commit](https://img.shields.io/github/last-commit/sisoe24/nukeserversocket)
[![license](https://img.shields.io/github/license/sisoe24/nukeserversocket)](https://github.com/sisoe24/nukeserversocket/blob/main/LICENSE)

[![issues](https://img.shields.io/github/issues/sisoe24/nukeserversocket)](https://github.com/sisoe24/nukeserversocket/issues)
[![pull-request](https://img.shields.io/github/issues-pr/sisoe24/nukeserversocket)](https://github.com/sisoe24/nukeserversocket/pulls)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/5b59bd7f80c646a8b2b16ad4b8cba599)](https://www.codacy.com/gh/sisoe24/nukeserversocket/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=sisoe24/nukeserversocket&amp;utm_campaign=Badge_Grade)

![x](https://img.shields.io/badge/Nuke-✅-success)
![x](https://img.shields.io/badge/Houdini-✅-success)
![x](https://img.shields.io/badge/Python-3.*-success)

[![NukeTools](https://img.shields.io/github/v/release/sisoe24/Nuke-Tools?label=NukeTools)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools)

A PySide plugin that runs Python and BlinkScript in Nuke, sent from your code editor, your own script or an MCP client. It also works in Houdini.

## Installation

**With [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools):** run the command `Nuke: Add Packages`.

**Manually:**

1. Download from the [releases page](https://github.com/sisoe24/nukeserversocket/releases), or clone the repository.
2. Put it in `~/.nuke` or another folder on your Nuke path.
3. Add to your `menu.py`:

```python
from nukeserversocket import nukeserversocket
nukeserversocket.install_nuke()
```

**Houdini:** see [docs/houdini.md](docs/houdini.md).

## Usage

![Execute Code](resources/images/run_code.gif)

1. In Nuke, open the nukeserversocket panel and click **Connect**.
2. Send code from a client:
   - [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools): Visual Studio Code extension.
   - [nuketools.nvim](https://github.com/sisoe24/nuketools.nvim): Neovim plugin.
   - [Nuke Tools ST](https://packagecontrol.io/packages/NukeToolsST): Sublime Text package.
   - Your own client: see [docs/clients.md](docs/clients.md) for the request format.

The server accepts code only from your own machine by default.

>[!NOTE]
> If you get "_Server did not initiate. Error: The bound address is already in use_", change the **port** to a number between `49152` and `65535` and try again.

## MCP server

> **Experimental.** The MCP server and the tools file may change in a future release.

`nss_mcp/server.py` lets MCP clients, such as Claude Code, Codex and Gemini CLI, run Python in Nuke while the panel is connected.

To let your agent set it up, paste this into Claude Code, Codex, Gemini CLI or another agent:

```text
Set up the nukeserversocket MCP server by following https://github.com/sisoe24/nukeserversocket/blob/main/docs/mcp-agent-setup.md
```

Or set it up yourself. Claude Code:

```sh
claude mcp add -s user nuke -- python /path/to/nukeserversocket/nss_mcp/server.py
```

For Claude Desktop, Codex, Gemini CLI and other clients, see [docs/mcp.md](docs/mcp.md#install-in-a-client).

To give clients a fixed set of tools instead of arbitrary code, open **Settings** in the panel and click **Create sample...** next to **Tools file**. See [docs/mcp.md](docs/mcp.md) for the options, the tools file, and what it protects against.

## Settings

Open the settings from the panel toolbar. Hover over a setting to see what it does.

- **Server Timeout**: closes the server after this many minutes without a request. Default 60. 0 never closes it.
- **Auto Start**: starts the server when the panel opens. To start it when Nuke opens, also save a workspace with the panel and set it as your startup workspace (*Preferences > Behaviors > Startup*).
- **Allow LAN Connections**: accepts code from other machines on your network, with no authentication. Only turn it on for a network you trust.
- **Mirror Script Editor**: shows the code and its output in Nuke's Script Editor.
- **Format Output**: the format of the output in the Script Editor.
- **Clear Output**: clears the Script Editor output before each run.
- **Tools file**: limits clients to the tools in a JSON file. See [docs/mcp.md](docs/mcp.md#tools-file).

## Compatibility

Works with PySide6 (Nuke 16 and newer) and PySide2 (Nuke 15 and older), on Python 3. For Python 2.7, use version [0.6.2](https://github.com/sisoe24/nukeserversocket/releases/tag/v0.6.2) or older.

## Known Issues

- Changing the workspace while the server is listening makes Nuke load a new panel with the default state. The panel looks disconnected, but the old server is still listening. To close it, restart Nuke or wait for the Server Timeout.

## Contributing

For suggestions, bug reports or questions, open an issue or a pull request. Planned work is in the [Projects](https://github.com/users/sisoe24/projects/4) tab.
****