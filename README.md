# 1. NukeServerSocket README

A Nuke that plugin that will allow code execution inside Nuke from the local network.

> This is primarily a companion plugin for: [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools).

- [1. NukeServerSocket README](#1-nukeserversocket-readme)
  - [1.1. Features](#11-features)
  - [1.2. Installation](#12-installation)
  - [1.3. Usage](#13-usage)
  - [1.4. Connection](#14-connection)
  - [1.5. Settings](#15-settings)
  - [1.6. Extendibility](#16-extendibility)
    - [1.6.1. Code Sample](#161-code-sample)
    - [1.6.2. Port & Host address](#162-port--host-address)
  - [1.7. Known Issues](#17-known-issues)
  - [1.8. Compatibility](#18-compatibility)
  - [1.9. Test plugin locally](#19-test-plugin-locally)
  - [1.10. Overview](#110-overview)

## 1.1. Features

- Execute code from your local network by using Visual Studio Code.
- If used locally (same machine) no configuration required, just start the server.
- Connect from another computer by specify a custom address.
- Multiple computer can connect to the same Nuke instance.
- Easy expandable with any method of your choice (read more [Extendibility](#16-extendibility))

## 1.2. Installation

Save the plugin in your _.nuke_ directory or in a custom directory and then `import NukeServerSocket` in your _menu.py_.  
**Remember**: If you use a custom plugin path, add the path in your init.py: `nuke.pluginAddPath('custom/path')`.
> N.B. if your downloaded  zip folder has a different name (NukeServerSocket-master, NukeServerSocket-0.0.2 etc._), then you **need to rename it to just NukeServerSocket**.

## 1.3. Usage

1. Open the _NukeServerSocket_ panel and start the server by clicking on **Connect**.
   1. If you receive a message: "_Server did not initiate. Error: The bound address is already in use_", just change the **port** entry to a different one and try again. It means that probably you have a connection listening on that port already.
2. When connected you could test the receiver with the **Test Server Receiver** otherwise you are done.
3. Send code from Visual Studio Code by using the companion extension.

> The plugin doesn't have to stay visible after the server has been initialized.

## 1.4. Connection

When used locally (same machine), no configuration is required as the server will listen on the **Local Host Address**. If the server **port** is already busy, just change it by typing a random number between `49152` and `65535` and try again. Visual Studio Code will pick Nuke's settings automatically.

When connecting from/to another computer, manual configuration will be required inside Visual Studio Code.
You will need the **Local IP address** and the **port** information from NukeServerSocket.

The information inside Visual Studio Code must match the information inside NukeServerSocket.

> VMs: Sending from your local machine to a VM machine will likely require some configuration on your side like enabling some network settings etc.

If you still have some problems, please feel free to reach out for any questions.

## 1.5. Settings

The plugin offers some minor settings for the internal script editor, like send output, format text and so on but they are pretty self explanatory.

## 1.6. Extendibility

At its core, the plugin is just a server socket that waits for an incoming request, performs the operations inside Nuke and returns the result. Nothing ties it to Visual Studio Code per se.

The only requirement is to send a _stringified Associative Array_ with the key **text** containing the code to be executed as a string. An optional key **file** could be added to show the name of the file that is being executed (this will only show if settings **Output to Script Editor** and **Clean & Format Text** are enabled)

On the plugin side, the data is converted with `json.loads()` into a valid `dictionary` python type.

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

data = {"text": "print('Hello World from py')"}

# stringify the dictionary with json.dumps
data = json.dumps(data)

s.sendall(bytearray(data))

# the returned data from NukeServerSocket
data = s.recv(1024)

s.close()

print("Result :", data) # Hello World from py
```

```js
// Node.js Send data example.

let s = new require('net').Socket();

// connection host and port must match information inside Nuke plugin
s.connect(54321, '127.0.0.1', function () {

    const data = {
        'text': 'print("Hello World from node.js")',
        'file': 'path/to/file.py'
    };

    // stringify the object before sending
    s.write(JSON.stringify(data));
});

// the returned data from NukeServerSocket
s.on('data', function (data) {
    // data could be <Buffer> | <string> | <any>
    console.log(data.toString('utf8'));
    s.destroy();
});
```

### 1.6.2. Port & Host address

NukeServerSocket by default will listen on the local address so you just need to specify the local host address (eg.`127.0.0.1`) in your socket client code.
The port information is written automatically to _.nuke/NukeServerSocket.ini_ file each time the user changes it. This is used from the Visual Studio Code extension to pick automatically to which port connect. Otherwise it will required to be specified manually.

This is pretty much all you need to start your own extension for your favorite text editor or any other method you prefer.

If you still have some problems, please feel free to reach out for any questions.

## 1.7. Known Issues

- Settings window doesn't display the tooltip text. This seems to be a Nuke bug as outside it works correctly.
- Plugin has been tested only on small amount of scripts so if you encounter problems/bugs will be great to receive a testable sample code.

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

While limited in some regards, the plugin can be tested outside Nuke environment.

1. Clone the github repo into your machine.
2. `pipenv install` for normal installation or `pipenv install --dev -e .` if you want to test the code with `pytest` (No tests are provided at the time of writing.)
3. Launch the app via terminal `python -m tests.run_app` or vscode task: `RunApp`

The local plugin offers a simple emulation of the Nuke's internal Script Editor layout. It just basic enough to test some simple code. It serves as an indicator for when the output will be sent to it otherwise you shouldn't needed that much.

When the application start will automatically: connect, send test message and display the received message.

## 1.10. Overview

<img title="Execute Code" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/execute_code.gif?raw=true" width="100%"/>

<img title="Main Window" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/main_window.png?raw=true" width="80%"/>

<img title="Settings" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/settings.png?raw=trueg" width="30%"/>

<img title="Vscode Manual" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/vscode_manual2.png?raw=trueg" width="90%"/>
