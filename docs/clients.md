# Client applications

A client sends code to the nukeserversocket panel over TCP and receives the output. This page shows the request format, so you can write your own client.

## Send code

Send one JSON object as a UTF-8 string. Each connection carries one request. The panel returns the output and closes the connection.

```json
{
  "text": "print(nuke.root().name())",
  "file": "path/to/script.py",
  "formatText": "0"
}
```

- `text`: required. The code to run.
- `file`: the path of the script.
  - Optional for Python.
  - Required for BlinkScript. The path must end with `.cpp` or `.blink`.
- `formatText`: optional, default `"1"`. `"1"` formats the output, `"0"` sends plain text. Use `"0"` if your client parses the output.

Convert the object to a string before you send it, for example with `json.dumps()` or `JSON.stringify()`.

## Connect

### Host

- On the same machine, use `127.0.0.1`. The panel listens on IPv4 only, so `localhost` fails if it resolves to `::1`.
- From another machine, turn on **Allow LAN Connections** in the panel's Settings. Then use the IP address that the panel shows, for example `192.168.1.10`. There is no authentication, so turn on this setting only on a network that you trust.

### Port

The panel saves its port in `~/.nuke/nukeserversocket.json`. Your client can read the port from this file. The default port is `54321`.

## Tool requests

Clients can list and call the panel's tools: `nuke_vision`, `nuke_graph`, `nuke_stats` and the tools of the [tools file](mcp.md#tools-file). Send each request on its own connection, as you do for a code request. The reply is JSON:

```py
{"list_tools": true}
# {"allow_arbitrary_code": false, "tools": [{"name", "description", "inputSchema", "timeout", "annotations"}], "skipped": {"name": "reason"}}

{"call_tool": "render_write", "arguments": {"node": "Write1"}}
# {"ok": true, "output": "printed text, then the return value as JSON"}
```

When a tool returns an image, for example `nuke_vision`, the reply also has `"images": [{"mimeType": "image/jpeg", "data": "<base64>"}]`, and `output` holds only the printed text.

When `allow_arbitrary_code` is `false`, the reply to a code request starts with `NukeServerSocket error:`.

## Code samples

Both samples print the names of all nodes in the script.

### Python

```py
import os
import json
import socket

def get_port():
    """Get the port from ~/.nuke/nukeserversocket.json."""
    config_path = os.path.join(os.path.expanduser('~'), '.nuke', 'nukeserversocket.json')
    with open(config_path) as f:
        return json.load(f).get('port', 54321)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', get_port()))

data = {
    "text": "print([n.name() for n in nuke.allNodes()])",
    "file": "path/to/file.py",
    "formatText": "0"
}

s.sendall(json.dumps(data).encode('utf-8'))

# the panel closes the connection after the reply
reply = b''
while chunk := s.recv(4096):
    reply += chunk

s.close()

# Python prints the list with single quotes; JSON needs double quotes
nodes = json.loads(reply.decode('utf-8').replace("'", '"'))

for node in nodes:
    print(node)
```

### Node.js

```js
const fs = require('fs');
const path = require('path');
const net = require('net');

/**
 * Get the port from ~/.nuke/nukeserversocket.json.
 */
function getPort() {
    const configPath = path.join(process.env.HOME || process.env.USERPROFILE, '.nuke', 'nukeserversocket.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    return config.port || 54321;
}

const client = new net.Socket();
const chunks = [];

client.connect(getPort(), '127.0.0.1', () => {
    const data = {
        "text": "print([n.name() for n in nuke.allNodes()])",
        "file": "path/to/file.py",
        "formatText": "0"
    };
    client.write(JSON.stringify(data));
});

// a long reply arrives in more than one chunk
client.on('data', (chunk) => chunks.push(chunk));

// the panel closes the connection after the reply
client.on('end', () => {
    // Python prints the list with single quotes; JSON needs double quotes
    const result = Buffer.concat(chunks).toString('utf-8').replace(/'/g, '"');
    try {
        JSON.parse(result).forEach(node => console.log(node));
    } catch (error) {
        console.error('Error parsing JSON:', error);
        console.log('Raw result:', result);
    }
});

client.on('error', (error) => {
    console.error('Connection error:', error);
});
```
