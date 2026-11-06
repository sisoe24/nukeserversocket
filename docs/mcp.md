# MCP server

> **Experimental.** The MCP server and the tools file may change in a future release, including the tools file format and the requests they send to the panel.

`nss_mcp/server.py` is a small [MCP](https://modelcontextprotocol.io) server that lets MCP clients (Claude Desktop, Claude Code, etc.) run Python inside a running Nuke session. It has no dependencies: the client speaks JSON-RPC 2.0 over stdio, and the server forwards each request to the nukeserversocket panel over TCP. Each request appears in the panel's Logs, marked `(MCP)`.

## Install in a client

Each client starts the server with `python /path/to/nukeserversocket/nss_mcp/server.py`. Use the absolute path to the file: some clients do not expand `~`. Add the [options](#options) after the path when the panel does not use the defaults.

**Claude Code:**

```sh
claude mcp add nuke -- python /path/to/nukeserversocket/nss_mcp/server.py
```

**Claude Desktop** (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "nuke": {
      "command": "python",
      "args": ["/path/to/nukeserversocket/nss_mcp/server.py"]
    }
  }
}
```

**Codex:**

```sh
codex mcp add nuke -- python /path/to/nukeserversocket/nss_mcp/server.py
```

Or in `~/.codex/config.toml`:

```toml
[mcp_servers.nuke]
command = "python"
args = ["/path/to/nukeserversocket/nss_mcp/server.py"]
```

**Gemini CLI:**

```sh
gemini mcp add nuke python /path/to/nukeserversocket/nss_mcp/server.py
```

Or in `~/.gemini/settings.json`, with the same `mcpServers` entry as Claude Desktop.

**Other clients:** add a stdio server with the command `python` and the arguments `/path/to/nukeserversocket/nss_mcp/server.py`. Most clients use the same `mcpServers` JSON as Claude Desktop.

## Options

| Option      | Environment variable | Default     | Meaning                                   |
| ----------- | -------------------- | ----------- | ----------------------------------------- |
| `--port`    | `NSS_MCP_PORT`       | `54321`     | Port of the nukeserversocket panel.       |
| `--host`    | `NSS_MCP_HOST`       | `127.0.0.1` | Machine that runs Nuke.                   |
| `--timeout` | `NSS_MCP_TIMEOUT`    | `60`        | Seconds to wait for Nuke to answer.       |

To reach Nuke on another machine, pass `--host` and turn on **Allow LAN Connections** in the panel. The panel then runs code from any machine on your network with no authentication, so only do this on a network you trust.

## Tools

The server exposes `nuke_execute_code`, plus any tools the panel's tools file declares. It asks Nuke for its tools each time the client lists them. If the client starts before Nuke, it sees only `nuke_execute_code` at first; when Nuke answers, the server tells the client to list the tools again.

## Tools file

By default any client can run any code in Nuke. A studio can instead give clients a fixed set of tools, such as "render this Write node", and turn arbitrary code off. Whoever sets up the plugin decides this, not the client.

1. In the panel, open **Settings** and click **Create sample...** next to **Tools file**. Choose a folder. The panel copies [nss_tools.json](../resources/sample/nss_tools.json) and its adapter module [nss_tools_example.py](../resources/sample/nss_tools_example.py) there, and sets **Tools file** to the new JSON file.
2. Edit the adapter functions and declare them in the JSON file. Nuke can import any module in the JSON file's folder.
3. To set the file for a whole studio, set `NSS_TOOLS` to its path before Nuke starts. `NSS_TOOLS` wins over the setting and makes the field read-only, so artists cannot change it from the panel.

The tools load each time the panel connects, and the panel shows whether code is allowed and which tools loaded. To pick up a change to the JSON file, disconnect and connect the panel. A change to the adapter module needs a Nuke restart, because Python keeps the module it imported.

Clients other than MCP can use the tools too: see [Tool requests](clients.md#tool-requests).

### Fields

```json
{
    "allow_code": false,
    "tools": [
        {
            "name": "render_write",
            "description": "Render one Write node by name.",
            "function": "nss_tools_example:render_write",
            "timeout": 3600,
            "inputSchema": {
                "type": "object",
                "properties": {"node": {"type": "string"}},
                "required": ["node"]
            }
        }
    ]
}
```

| Field         | Meaning                                                                                                                                                       |
| ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `allow_code`  | `true` (default) keeps code execution on. `false` refuses every code request.                                                                                 |
| `name`        | Letters, digits, `_`, `-` or `.`, up to 128 characters. `execute_code` is reserved.                                                                           |
| `description` | What the tool does. LLM clients read it to decide when to call the tool.                                                                                      |
| `function`    | `module:function`, imported when the panel connects. Dots reach nested attributes, such as `module:Class.static_method`.                                      |
| `timeout`     | Optional. Seconds the MCP server waits for this tool, instead of its `--timeout`.                                                                             |
| `inputSchema` | Optional for tools without arguments. A JSON Schema object whose properties match the function's parameters. Parameters without a default must be `required`. |

An entry that cannot load (bad field, failed import, signature that does not match the schema) is skipped with the reason, and the other tools still load. If a tools file is set but is missing or is not valid JSON, no tools load and code execution is off.

Before calling a function, the server checks that required arguments are present, that no unknown arguments are sent (unless the function takes `**kwargs`), and each argument's `type` and `enum`. It does not check nested values or other schema keywords, so the adapter must check those itself. Arguments are passed as Python values and are never inserted into code.

### Writing adapters

Write adapters for remote callers, not for artists:

- Take names and plain values, never the current selection: the artist may change it while a request is running.
- Never open a dialog. Nuke waits for someone to click it, and the client waits until it times out.
- Raise an exception for any failure. The client receives the traceback as an error.
- Return JSON values (`dict`, `list`, `str`, numbers). Anything else is sent as its `str()`.
- Make tools safe to run twice, or say in the description when they are not. After a timeout the client cannot tell whether the tool ran.

Tools run on Nuke's main thread, so Nuke's interface is busy until a tool returns.

## What the tools file protects against

A tools file limits what a remote client or an LLM agent can do through nukeserversocket. It does not stop people or code that already run as the same user: an artist can still use the Script Editor, and anyone who can edit `menu.py`, the adapter module or the JSON file can change the tools. There is no authentication, so with **Allow LAN Connections** on, anyone on the network can call the tools.
