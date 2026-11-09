# MCP server

> **Experimental.** The MCP server and the tools file can change in a future release. This includes the tools file format and the requests sent to the panel.

The MCP server lets an agent in an MCP client, such as Claude Code or Claude Desktop, run Python in a running Nuke session. The server is the file `nss_mcp/server.py`. It needs only Python 3, with no other packages. The client starts the server and sends it [MCP](https://modelcontextprotocol.io) requests (JSON-RPC 2.0) over stdio. The server sends each request to the nukeserversocket panel over TCP. The panel's Logs mark each of these requests with `(MCP)`.

The MCP server supports only Nuke for now, not [Houdini](houdini.md).

## Install in a client

Each client starts the server with this command:

```sh
python /path/to/nukeserversocket/nss_mcp/server.py
```

- Use the absolute path to `server.py`. Some clients do not expand `~`.
- The server needs Python 3. If `python` is missing or is Python 2, use `python3` or the full path to the interpreter.
- If the panel does not use the default values, add the [options](#options) after the path.

**Claude Code:**

```sh
claude mcp add -s user nuke -- python /path/to/nukeserversocket/nss_mcp/server.py
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

Or add this entry to `~/.codex/config.toml`:

```toml
[mcp_servers.nuke]
command = "python"
args = ["/path/to/nukeserversocket/nss_mcp/server.py"]
```

**Gemini CLI:**

```sh
gemini mcp add -s user nuke python /path/to/nukeserversocket/nss_mcp/server.py
```

Or add the same `mcpServers` entry as Claude Desktop to `~/.gemini/settings.json`.

**Other clients:** add a stdio server. Set the command to `python`. Set the arguments to `/path/to/nukeserversocket/nss_mcp/server.py`. Most clients use the same `mcpServers` JSON as Claude Desktop.

## Options

| Option      | Environment variable | Default     | Meaning                                   |
| ----------- | -------------------- | ----------- | ----------------------------------------- |
| `--port`    | `NSS_MCP_PORT`       | `54321`     | Port of the nukeserversocket panel.       |
| `--host`    | `NSS_MCP_HOST`       | `127.0.0.1` | Machine that runs Nuke.                   |
| `--timeout` | `NSS_MCP_TIMEOUT`    | `60`        | Seconds to wait for Nuke to answer.       |

To connect to Nuke on a different machine, set `--host` and turn on **Allow LAN Connections** in the panel. With this setting on, the panel runs code from any machine on your network, with no authentication. Use it only on a network that you trust.

## Tools

The server gives the client these tools:

- `nuke_execute_code`, if code is on in the [tools file](#tools-file).
- `nuke_vision`, if **Vision** is on in the panel settings. See [Vision](#vision).
- Each tool that the tools file declares.

The server gets the tool list from Nuke each time the client asks for it. If the client starts before Nuke, the client sees only `nuke_execute_code`. When Nuke answers, the server tells the client to get the tool list again.

## Vision

`nuke_vision` lets the agent see an image in Nuke, for example to check the result of a change. It renders one frame of a node to a JPEG and returns the image with JSON metadata. By default it renders the node that feeds the active Viewer input, at the current frame, with the long edge at most 768 pixels (about 440 tokens).

- The image has the Viewer's display transform (OCIO display and view). It does not have the Viewer's gain, gamma, wipe or overlays.
- Arguments, all optional: `node`, `frame`, `view`, `channels` (for example `alpha`, `depth`, `depth.Z`), `crop` (`[x, y, width, height]` in Nuke pixels, enlarged to show detail) and `size`.
- The metadata has the format, the bounding box, a formula from image pixels to Nuke coordinates, and warnings, for example when the frame is outside the node's range or the image is one color.

A temporary Write node renders the frame. The tool deletes the node and the file after the render, and turns undo off during the render, so the script and the undo history do not change. Nuke runs `onCreate`, `beforeRender` and `afterRender` callbacks for the temporary nodes too. If your pipeline adds callbacks to Write nodes, make sure that they ignore nodes whose names start with `_nss_vision_`.

**Vision** is on by default. It is separate from code: with code off in the tools file, the agent can still see images. To turn it off, clear **Vision** in the panel settings, then disconnect and connect the panel.

Code in Nuke can call the same function:

```py
from nukeserversocket.controllers.nuke_vision import vision

image = vision('Grade1', frame=1001)
with open('/tmp/grade1.jpg', 'wb') as f:
    f.write(image.data)
```

## Tools file

By default, a client can run any code in Nuke. A tools file changes this. It gives clients a fixed set of tools, such as "render this Write node". It can also turn code off, so that the panel refuses all code requests. The person who installs the plugin controls the tools file. The client cannot change it.

Each tool calls a Python function, the adapter. The adapters are in a Python module, the adapter module, in the same folder as the JSON file. Nuke can import any module in that folder.

To make a tools file:

1. In the panel, open **Settings**.
2. Next to **Tools file**, click **Create sample...**.
3. Choose a folder. The panel copies [nss_tools.json](../resources/sample/nss_tools.json) and its adapter module [nss_tools_example.py](../resources/sample/nss_tools_example.py) to that folder. It also sets **Tools file** to the new JSON file.
4. Edit the adapters in the adapter module.
5. Declare each adapter as a tool in the JSON file. See [Fields](#fields).

To use one tools file for the whole studio, set `NSS_TOOLS` to its path before Nuke starts. `NSS_TOOLS` overrides the panel setting and makes the **Tools file** field read-only, so artists cannot change it in the panel.

The panel loads the tools each time it connects. The panel's **MCP tools** list shows the tools that MCP clients see. It includes `nuke_execute_code` only when code is on, and `nuke_vision` only when **Vision** is on. Skipped tools are greyed out at the end. Hover over a tool to see its description, or why it was skipped.

- After you change the JSON file, disconnect and connect the panel.
- After you change the adapter module, restart Nuke. Python keeps the module that it imported first.

Clients other than MCP clients can also use the tools. See [Tool requests](clients.md#tool-requests).

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

| Field         | Meaning                                                                                                                                                                                                                       |
| ------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `allow_code`  | `true` (default): code is on. `false`: code is off, and the panel refuses all code requests.                                                                                                                                       |
| `name`        | Letters, digits, `_`, `-` or `.`, up to 128 characters. `nuke_execute_code` is reserved.                                                                                                                                           |
| `description` | What the tool does. The agent reads it to decide when to call the tool.                                                                                                                                           |
| `function`    | `module:function`. The panel imports the function when you connect the panel. Use dots for nested attributes, such as `module:Class.static_method`.                                                                                               |
| `timeout`     | Optional. Seconds the MCP server waits for this tool. It replaces `--timeout` for this tool only.                                                                                                                             |
| `inputSchema` | Optional for tools without arguments. A JSON Schema object. Its properties must match the function's parameters. Each parameter without a default must be in `required`.                                                      |
| `annotations` | Optional. MCP hints for the client: `title`, and `true` or `false` for `readOnlyHint`, `destructiveHint`, `idempotentHint` and `openWorldHint`. Codex and VS Code do not ask for approval before a `readOnlyHint` tool. Set `readOnlyHint` only on tools that change nothing. |

If an entry cannot load, the panel skips it, shows the reason, and loads the other tools. An entry cannot load when a field is bad, the import fails, or the function signature does not match the schema.

If a tools file is set but is missing or is not valid JSON, no tools load and code is off.

Before the panel calls an adapter, it checks the arguments:

- All required arguments are present.
- No unknown arguments are present, except when the function takes `**kwargs`.
- Each argument matches its `type` and `enum`.

The panel does not check nested values or other schema keywords. The adapter must check them. The panel gives the arguments to the adapter as Python values. It never puts them into code.

### Writing adapters

Write adapters for remote callers, not for artists:

- Take names and plain values as arguments, not the current selection. The artist can change the selection while a request runs.
- Do not open a dialog. Nuke waits for a click, and the client waits until its timeout ends.
- Raise an exception for each failure. The client gets the traceback as an error. To send only a message, without the traceback, raise `nukeserversocket.tools.ToolError`.
- Return JSON values (`dict`, `list`, `str`, numbers). The panel sends any other value as its `str()`.
- To return an image, return `nukeserversocket.tools.Image(data)`, where `data` is the JPEG bytes. MCP clients get the image after the printed text.
- Make tools safe to run two times. If a tool is not safe to run two times, say so in its description. After a timeout, the client cannot know if the tool ran.

Tools run on Nuke's main thread. The Nuke interface is busy until the tool returns.

## What the tools file protects against

A tools file limits what a remote client or an agent can do through nukeserversocket. It does not stop people or code that already run as the same user as Nuke:

- An artist can still use the Script Editor.
- A person who can edit `menu.py`, the adapter module or the JSON file can change the tools.

There is no authentication. With **Allow LAN Connections** on, any person on the network can call the tools.
