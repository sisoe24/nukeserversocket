# Studio tools

> **Experimental.** The tools file format and the tool requests may change in a future release.

A tools file declares the functions clients may call, and whether they may still run arbitrary code. To create one and choose it, see [Studio tools in the README](../README.md#113-studio-tools).

## Tools file

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

## Writing adapters

Write adapters for remote callers, not for artists:

- Take names and plain values, never the current selection: the artist may change it while a request is running.
- Never open a dialog. Nuke waits for someone to click it, and the client waits until it times out.
- Raise an exception for any failure. The client receives the traceback as an error.
- Return JSON values (`dict`, `list`, `str`, numbers). Anything else is sent as its `str()`.
- Make tools safe to run twice, or say in the description when they are not. After a timeout the client cannot tell whether the tool ran.

Tools run on Nuke's main thread, so Nuke's interface is busy until a tool returns.

## Requests for custom clients

Custom clients use two requests, each on its own connection like [code requests](clients.md). The reply is JSON:

```py
{"list_tools": true}
# {"allow_code": false, "tools": [{"name", "description", "inputSchema", "timeout"}], "skipped": {"name": "reason"}}

{"call_tool": "render_write", "arguments": {"node": "Write1"}}
# {"ok": true, "output": "printed text, then the return value as JSON"}
```

When `allow_code` is `false`, a code request gets a reply starting with `NukeServerSocket error:`.

## Security

Studio tools limit what a remote client or an LLM agent can do through nukeserversocket. It does not stop people or code that already run as the same user: an artist can still use the Script Editor, and anyone who can edit `menu.py`, the adapter module or the JSON file can change the tools. There is no authentication, so with **Allow LAN Connections** on, anyone on the network can call the tools.
