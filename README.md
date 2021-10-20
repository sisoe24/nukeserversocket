# 1. NukeServerSocket README

[![Main Build](https://img.shields.io/github/v/release/sisoe24/NukeServerSocket?label=stable)](https://github.com/sisoe24/NukeServerSocket/releases)
![Last commit](https://img.shields.io/github/last-commit/sisoe24/NukeServerSocket)

[![Pre Release](https://img.shields.io/github/v/release/sisoe24/NukeServerSocket?label=pre-release&include_prereleases)](https://github.com/sisoe24/NukeServerSocket/releases)
![Last commit](https://img.shields.io/github/last-commit/sisoe24/NukeServerSocket/0.2.0)

[![issues](https://img.shields.io/github/issues/sisoe24/NukeServerSocket)](https://github.com/sisoe24/NukeServerSocket/issues)
[![pull-request](https://img.shields.io/github/issues-pr/sisoe24/NukeServerSocket)](https://github.com/sisoe24/NukeServerSocket/pulls)
[![Coverage Status](https://coveralls.io/repos/github/sisoe24/NukeServerSocket/badge.svg?branch=0.2.0-dev)](https://coveralls.io/github/sisoe24/NukeServerSocket?branch=0.2.0-dev)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/5b59bd7f80c646a8b2b16ad4b8cba599)](https://www.codacy.com/gh/sisoe24/NukeServerSocket/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=sisoe24/NukeServerSocket&amp;utm_campaign=Badge_Grade)

[![license](https://img.shields.io/github/license/sisoe24/NukeServerSocket)](https://github.com/sisoe24/NukeServerSocket/blob/main/LICENSE)

![x](https://img.shields.io/badge/Python-2.7.16_|_3.7.7-success)
![x](https://img.shields.io/badge/Nuke11-success)
![x](https://img.shields.io/badge/Nuke12-success)
![x](https://img.shields.io/badge/Nuke13-success)

A Nuke plugin that will allow code execution from the local network and more.

> This is primarily a companion plugin for [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools).

- [1. NukeServerSocket README](#1-nukeserversocket-readme)
  - [1.1. Tools](#11-tools)
  - [1.2. Features](#12-features)
  - [1.3. Installation](#13-installation)
  - [1.4. Usage](#14-usage)
    - [1.4.1. Receive incoming request](#141-receive-incoming-request)
    - [1.4.2. Receive/Send nodes](#142-receivesend-nodes)
      - [1.4.2.1. Send](#1421-send)
      - [1.4.2.2. Receive](#1422-receive)
  - [1.5. Settings](#15-settings)
  - [1.6. Extendibility](#16-extendibility)
    - [1.6.1. Code Sample](#161-code-sample)
    - [1.6.2. Port & Host address](#162-port--host-address)
  - [1.7. Known Issues](#17-known-issues)
  - [1.8. Compatibility](#18-compatibility)
  - [1.9. Test plugin locally](#19-test-plugin-locally)
  - [1.10. Overview](#110-overview)

## 1.1. Tools

Tools that are using NukeServerSocket:

- [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools) - Visual Studio Code extension.

## 1.2. Features

- Send Python or BlinkScript code to be executed inside Nuke from your local network.
- Multiple computers can connect to the same Nuke instance.
- Receive/Send nodes from another Nuke instance in your local network.
- Not bound to any application. (more on [Extendibility](#16-extendibility))

## 1.3. Installation

Save the plugin in your _.nuke_ directory or in a custom directory and then `import NukeServerSocket` in your _menu.py_.  
**Remember**: If you use a custom plugin path, add the path in your init.py: `nuke.pluginAddPath('custom/path')`.
> N.B. if your downloaded  zip folder has a different name (NukeServerSocket-master, NukeServerSocket-0.0.2 etc._), then you **need to rename it to just NukeServerSocket**.

## 1.4. Usage

### 1.4.1. Receive incoming request

Open the _NukeServerSocket_ panel and with the mode on **Receiver**, start the server by clicking **Connect**.

  > If you receive a message: "_Server did not initiate. Error: The bound address is already in use_", just change the **Port** to a random number between `49152` and `65535` and try again. It means that probably you have a connection listening on that port already. Also when connected, you could test the receiver with the **Test Receiver** button, otherwise you are done.

When connected, NukeServerSocket will listen for incoming request on the IP Address and Port shown in the plugin.

Now you can send code from Visual Studio Code with [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools) or any other method you prefer.

### 1.4.2. Receive/Send nodes

#### 1.4.2.1. Send

When sending nodes, switch the mode from **Receiver** to **Sender** and be sure that there is another NukeServerSocket instance listening for incoming network request ([Receive incoming request](#141-receive-incoming-request)). Select the nodes you want to send a click **Send Selected Nodes**.

> By default, the IP Address on the sender points to the local IP address, so if you want to send nodes between the same computer you should only specify the Port. When sending nodes to another computer you will also need to specify the IP Address of the NukeServerSocket computer you want the nodes to be sended.

#### 1.4.2.2. Receive

When receiving nodes just follow the steps for [Receive incoming request](#141-receive-incoming-request) for the receiving instance and the [Send](#1421-send) steps for the sending instances.

## 1.5. Settings

The plugin offers some minor settings like output text to internal script editor, format text and so on.

## 1.6. Extendibility

At its core, the plugin is just a server socket that awaits for an incoming request, performs the operations inside Nuke and returns the result. Nothing ties it to any application per se.

The only requirement is that the code received should be inside a string.

From the client point of view, the code can be sended either inside a _stringified_ associative array or inside a simple string, with the latter being valid only when sending Python code.

The associative array should have the following keys: `text` and an optional `file`.

- `text`: Must contain the code to be executed as a string.
- `file`: Could contain the file path of the script that is being executed.

Although the associative array is optional when executing Python code, it is a requirement when executing BlinkScript. The key **file** must contain a valid file extension: `.cpp` or `.blink` in order for the plugin to know where to delegate the job.

> When sending a stringified array, the plugin will try to deserialize it with `json.loads()`.

### 1.6.1. Code Sample

```py
"""Python Send data example."""
from __future__ import print_function

import json
import socket

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# connection host and port must match information inside Nuke plugin
# 127.0.0.1 == localhost
s.connect(('127.0.0.1', 54321))

data = "print('Hello World from py')"
# or
data = {
    "text": "print('Hello World from py')",
    "file" : "path/to/file.py" # optional
}

# if data is a simple string json.dumps is not required
data = json.dumps(data)

s.sendall(bytearray(data))

# the returned data from NukeServerSocket
data = s.recv(1024)

s.close()

print("Result :", data) # Hello World from py
```

```js
// Node.js Send data example.

let socket = new require('net').Socket();

// connection host and port must match information inside Nuke plugin
  socket.connect(54321, '127.0.0.1', function () {

    const data = {
        "text": "print('Hello World from node.js')",
    };

    // stringify the object before sending
      socket.write(JSON.stringify(data));
});

// the returned data from NukeServerSocket
  socket.on('data', function (data) {
    // data could be <Buffer> | <string> | <any>
    console.log(data.toString('utf8'));
      socket.destroy();
});
```

### 1.6.2. Port & Host address

NukeServerSocket by default will listen on any host address.

When connecting locally (same computer) you can just specify the local host address (eg.`127.0.0.1`) in your socket client code. When connecting from a different computer you also specify the exact IP Address (eg `192.168.1.10`).

The port value is written to _.nuke/NukeServerSocket.ini_ inside the `server/port` field. Each time the user changes it, it gets update automatically. If used locally, this can be used from your extension to pick at which port to connect.

This is pretty much all you need to start your own extension for your favorite text editor or any other method you prefer.

If you still have some problems, please feel free to reach out for any questions.

## 1.7. Known Issues

- Settings window doesn't display the tooltip text.
- When changing workspace with an active open connection, Nuke will load a new plugin instance with the default UI state. This would look as if the previous connection has been closed, where in reality is still open and listening. The only way to force close all of the connections is to restart Nuke.

## 1.8. Compatibility

Nuke version: 11,12, 13.

> Because Nuke 11 uses an early version of PySide2, future compatibility is not a guarantee.

While it should work the same on all platforms, it has been currently only tested on:

- Linux:
  - CentOS 8
- MacOS:
  - Mojave 10.14.06
  - Catalina 10.15.06
- Windows 10

## 1.9. Test plugin locally

> This works only on Linux and Mac. Probably Windows WSL but haven't tested it yet.

While limited in some regards, the plugin can be tested outside Nuke environment.

1. Clone the github repo into your machine.
2. `pipenv install --ignore-pipfile` for normal installation or `pipenv install --ignore-pipfile --dev -e .` if you want to test the code with `pytest` (No tests are provided at the time of writing).
3. Launch the app via terminal `python -m tests.run_local` or vscode task: `RunApp`

The local plugin offers a simple emulation of the Nuke's internal Script Editor layout. It just basic enough to test some simple code.

When the application starts it will:

1. Click the connect button
2. Send a test message
3. Display the received message or error if any.
4. Override input/output widgets if settings allowed it.

It is a very basic and simple test but because the PySide2 and Python version are pretty much identical to Nuke's one will likely function the same way inside Nuke.

## 1.10. Overview

<img title="Execute Code" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/execute_code.gif?raw=true" width="100%"/>

<img title="Main Window" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/main_window.png?raw=true" width="80%"/>

<img title="Settings" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/settings.png?raw=trueg" width="30%"/>

<img title="Vscode Manual" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/vscode_manual2.png?raw=trueg" width="90%"/>
