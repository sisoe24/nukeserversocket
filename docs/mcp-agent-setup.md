# Set up the nukeserversocket MCP server (for agents)

You are an agent setting up the nukeserversocket MCP server for the user, in the client you run in. The client commands and config formats are in [mcp.md](mcp.md#install-in-a-client), next to this file. Done means: the server is registered in your client, and the panel in Nuke answers a `list_tools` request.

Keep setup read-only toward Nuke: register the server, check the connection, and leave Nuke's files and settings as they are. Ask the user before you write into `~/.nuke`, edit `menu.py` or `init.py`, turn on Allow LAN Connections, change the tools file, or send code to Nuke.

## 1. Find the plugin

The plugin folder is the outer `nukeserversocket` folder: it holds `__init__.py`, an inner `nukeserversocket/` package, and `nss_mcp/server.py`, the MCP server. Look for `nss_mcp/server.py` in:

- `~/.nuke/NukeTools/nukeserversocket` (installed with Nuke Tools)
- `~/.nuke/nukeserversocket`
- every folder on the Nuke path: the folders in the `NUKE_PATH` environment variable, and the folders passed to `nuke.pluginAddPath(...)` in `~/.nuke/init.py` (read the file; resolve any environment variables it uses)

If you find exactly one, use it. If you find several, list them and ask the user which one Nuke loads. An outer `nukeserversocket` folder without `nss_mcp/` is a version older than the MCP server: offer to install a new one with step 1a.

Done when you have the absolute path to `nss_mcp/server.py`, or the user agreed to step 1a.

### 1a. Install the plugin

Ask the user first, as for any write into `~/.nuke`. Install the latest release by default; install the development version only when the user asks for it.

**Latest release:**

1. Download `https://github.com/sisoe24/nukeserversocket/releases/latest/download/nukeserversocket.zip` to a temporary folder.
2. List the zip contents. If no entry is `nss_mcp/server.py`, the latest release does not include the MCP server yet: stop before extracting, and offer the development version instead.
3. Extract the zip into `~/.nuke/nukeserversocket`. The zip has no top folder, so its files land directly in that folder.

**Development version:**

```sh
git clone https://github.com/sisoe24/nukeserversocket ~/.nuke/nukeserversocket
```

The user updates it later with `git pull` in that folder.

**Then, for both:**

1. Show the user these lines, and add them to `~/.nuke/menu.py` when they agree:

   ```python
   from nukeserversocket import nukeserversocket
   nukeserversocket.install_nuke()
   ```

2. Ask the user to restart Nuke, open the NukeServerSocket panel, and click **Connect**.

Done when `~/.nuke/nukeserversocket/nss_mcp/server.py` exists and the user confirms the panel is connected.

## 2. Find Python 3

Ask Python for its own path, so the client does not depend on your shell's setup (pyenv shims, virtual environments):

```sh
python3 -c "import sys; print(sys.executable, sys.version_info[0])"
```

If `python3` is missing, try `python`. Done when you have an absolute interpreter path whose version is 3.

## 3. Register the server

Register a stdio server named `nuke`: the command is the interpreter from step 2, and the argument is the `server.py` path from step 1. Register it for the user, so it works in every project: for Claude Code, use `claude mcp add -s user`; for Gemini CLI, `gemini mcp add -s user`. Codex has one global config. Use your client's own `mcp add` command when it has one; otherwise edit its config file as [mcp.md](mcp.md#install-in-a-client) shows. Use absolute paths only.

The panel listens on `127.0.0.1:54321` by default. If the user says it uses another port or machine, add `--port` or `--host` after the `server.py` path.

If a server named `nuke` already exists, show it to the user and ask before you replace it.

Done when your client's list command (`claude mcp list`, `codex mcp list`, `gemini mcp list`) shows `nuke` with your command.

## 4. Check the connection

Ask Nuke for its tools. Replace `PYTHON` with the interpreter from step 2, and `HOST` and `PORT` with the values from step 3 (`127.0.0.1` and `54321` by default). This request runs no code in Nuke:

```sh
PYTHON -c "import socket; s = socket.create_connection(('HOST', PORT), 5); s.sendall(b'{\"list_tools\": true}'); print(s.makefile().read())"
```

- A JSON reply with `allow_arbitrary_code` and `tools`: the check passes.
- Connection refused: Nuke is closed or the panel is not connected. Ask the user to open the NukeServerSocket panel in Nuke and click **Connect**, then run the check again.

Done when the check passes.

## 5. Report

Tell the user:

- the command you ran or the config file you changed, and the exact entry
- whether clients may run code: `allow_arbitrary_code` true means `nuke_execute_code` works; false means only the listed tools do
- the tools Nuke listed. An empty list is normal without a tools file
- any entries in `skipped`, with their reasons
- that they may need to restart the client, or start a new session, before the `nuke` tools appear
