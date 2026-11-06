# Client applications

## Sending Code

Send a JSON object as a UTF-8 string. Each connection carries one request: the server sends back the output and closes the connection.

### JSON Object Structure

```json
{
  "text": "Your code here",
  "file": "path/to/script.py",
  "formatText": "0"
}
```

* text: (Required) Contains the code to be executed.
* file: (Optional for Python, Required for BlinkScript and must end with `.cpp` or `.blink`) File path of the script.
* formatText: (Optional. Defaults to `"1"`) `"0"` for plain text, `"1"` for formatted text. If you plan to parse the output, use `"0"`.

> [!IMPORTANT]
> The json object must be stringified before sending it to the server.

## Connecting to the Server

### Host Address

* Local connection: Use `127.0.0.1`. Connect by IPv4: `localhost` resolved to `::1` is refused.
* Remote connection: Turn on **Allow LAN Connections** in the panel's Settings, then use the IP address the panel shows (e.g., `192.168.1.10`). There is no authentication, so only do this on a network you trust.

### Port

The port is set in the NukeServerSocket plugin and is saved in the `nukeserversocket.json` file located in the `.nuke` directory. Your client can read this file to get the current port.

## Putting It All Together

* Set up a socket connection using the host and port.
* Prepare your code as a JSON object.
* Send the code to the server.
* Wait for and process the server's response.

## Studio tools

Besides code, a client can list and call the tools a studio declares. See [Requests for custom clients](studio-tools.md#requests-for-custom-clients).

## Code Sample

### Python

```py
import os
import json
import socket

def get_port():
    """Get Port configuration from .nuke/nukeserversocket.json."""
    config_path = os.path.join(os.path.expanduser('~'), '.nuke', 'nukeserversocket.json')
    with open(config_path) as f:
        return json.load(f).get('port', 54321)


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(('127.0.0.1', get_port()))

data = {
    "text": "print([n.name() for n in nuke.allNodes()])",
    "file" : "path/to/file.py",
    "formatText": "0" 
}

# stringify the object before sending
s.sendall(bytearray(json.dumps(data), 'utf-8'))

# the server closes the connection after the reply
data = b''
while chunk := s.recv(4096):
    data += chunk

s.close()

# convert the data to string
result = data.decode('utf-8')

# help json.loads to parse the string by replacing single quotes with double quotes
nodes = json.loads(result.replace("'", '"'))

for node in nodes:
    print(node)

```

### Node.js

```js
// Send Data Example node.js
const fs = require('fs');
const path = require('path');
const net = require('net');


/**
 * Get the server port value from nukeserversocket.json
 */
function getPort() {
    const configPath = path.join(process.env.HOME || process.env.USERPROFILE, '.nuke', 'nukeserversocket.json');
    const config = JSON.parse(fs.readFileSync(configPath, 'utf8'));
    return config.port || 54321;
}

const client = new net.Socket();
const port = getPort();

client.connect(port, '127.0.0.1', () => {
    console.log('Connected to server');
    
    const data = {
        "text": "print([n.name() for n in nuke.allNodes()])",
        "file": "path/to/file.py",
        "formatText": "0"
    };

    // Stringify the object before sending
    client.write(JSON.stringify(data));
});

client.on('data', (data) => {
    // Convert the data to string
    let result = data.toString('utf-8');
    
    // Help JSON.parse by replacing single quotes with double quotes
    result = result.replace(/'/g, '"');
    
    try {
        const nodes = JSON.parse(result);
        nodes.forEach(node => console.log(node));
    } catch (error) {
        console.error('Error parsing JSON:', error);
        console.log('Raw result:', result);
    }

    client.destroy(); // Close the connection after receiving the response
});

client.on('close', () => {
    console.log('Connection closed');
});

client.on('error', (error) => {
    console.error('Connection error:', error);
});
```
