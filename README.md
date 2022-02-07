# 1. NukeServerSocket README

[![Main Build](https://img.shields.io/github/v/release/sisoe24/NukeServerSocket?label=stable)](https://github.com/sisoe24/NukeServerSocket/releases)
[![Pre Release](https://img.shields.io/github/v/release/sisoe24/NukeServerSocket?label=pre-release&include_prereleases)](https://github.com/sisoe24/NukeServerSocket/releases)
![Last commit](https://img.shields.io/github/last-commit/sisoe24/NukeServerSocket)

[![issues](https://img.shields.io/github/issues/sisoe24/NukeServerSocket)](https://github.com/sisoe24/NukeServerSocket/issues)
[![pull-request](https://img.shields.io/github/issues-pr/sisoe24/NukeServerSocket)](https://github.com/sisoe24/NukeServerSocket/pulls)

[![Codacy Badge](https://app.codacy.com/project/badge/Grade/5b59bd7f80c646a8b2b16ad4b8cba599)](https://www.codacy.com/gh/sisoe24/NukeServerSocket/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=sisoe24/NukeServerSocket&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/5b59bd7f80c646a8b2b16ad4b8cba599)](https://www.codacy.com/gh/sisoe24/NukeServerSocket/dashboard?utm_source=github.com&utm_medium=referral&utm_content=sisoe24/NukeServerSocket&utm_campaign=Badge_Coverage)
[![DeepSource](https://deepsource.io/gh/sisoe24/NukeServerSocket.svg/?label=active+issues&show_trend=true&token=D3BtO5z54YqAh2Fn2pTf9JKB)](https://deepsource.io/gh/sisoe24/NukeServerSocket/?ref=repository-badge)

[![license](https://img.shields.io/github/license/sisoe24/NukeServerSocket)](https://github.com/sisoe24/NukeServerSocket/blob/main/LICENSE)

![x](https://img.shields.io/badge/Python-2.7.18_|_3.7.7-success)
![x](https://img.shields.io/badge/Nuke11-success)
![x](https://img.shields.io/badge/Nuke12-success)
![x](https://img.shields.io/badge/Nuke13-success)

A Nuke plugin that will allow code execution from the local network and more.

- [1. NukeServerSocket README](#1-nukeserversocket-readme)
  - [1.1. Tools](#11-tools)
  - [1.2. Features](#12-features)
  - [1.3. Installation](#13-installation)
  - [1.4. Usage](#14-usage)
    - [1.4.1. Receive incoming request](#141-receive-incoming-request)
    - [1.4.2. Receive/Send nodes](#142-receivesend-nodes)
      - [1.4.2.1. Send](#1421-send)
      - [1.4.2.2. Receive](#1422-receive)
      - [1.4.2.3. Connection timeouts](#1423-connection-timeouts)
  - [1.5. Settings](#15-settings)
  - [1.6. Extendibility](#16-extendibility)
    - [1.6.1. Code Sample](#161-code-sample)
    - [1.6.2. Port & Host address](#162-port--host-address)
  - [1.7. Test plugin locally](#17-test-plugin-locally)
    - [1.7.1. Python 3](#171-python-3)
    - [1.7.2. Python 2](#172-python-2)
      - [1.7.2.1. `pipenv`](#1721-pipenv)
      - [1.7.2.2. `virtualenv`](#1722-virtualenv)
      - [1.7.2.3. `poetry`](#1723-poetry)
    - [1.7.3. Testing](#173-testing)
  - [1.8. Known Issues](#18-known-issues)
  - [1.9. Compatibility](#19-compatibility)
  - [1.10. Overview](#110-overview)

## 1.1. Tools

Tools that are using NukeServerSocket:

- [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools) - Visual Studio Code extension.
- [Nuke Tools ST](https://packagecontrol.io/packages/NukeToolsST) - Sublime Text package.

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

#### 1.4.2.3. Connection timeouts

- The server connection will shutdown after 5 minutes of inactivity.
- The socket server will shutdown after 30 seconds if it doesn't receive any request.
- The socket client will shutdown after 10 seconds if could not initiate a connection.

## 1.5. Settings

The plugin offers some minor settings like output text to internal script editor, format text and so on.

## 1.6. Extendibility

At its core, the plugin is just a server socket that awaits for an incoming request, performs the operations inside Nuke and returns the result. Nothing ties it to any application per se.

The only requirement is that the code received should be inside a string.

From the client point of view, the code can be sent either inside a _stringified_ associative array or inside a simple string, with the latter being valid only when sending Python code.

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

## 1.7. Test plugin locally

The plugin can be launched locally. This is useful for testing code and implementing new features.
Also the local plugin offers a simple emulation of the Nuke's internal Script Editor layout.

The project default interpreter is Python 3 but it can also be build with Python 2.
Python 3 version is required to be `<=3.7.7` as in newer versions there is a Qt related bug that was solved only in versions newer that the one inside Nuke.

After each new feature, the project is required to pass both Python 2 and Python 3 tests.


### 1.7.1. Python 3

Poetry package manager is used to build the project for Python 3. A different virtualenv wrapper could be used instead as is just a matter of personal preference.

```sh
# clone the repo

# install packages
poetry install

# run app locally
poetry run python -m src.run_local

# run tests
poetry run python -m pytest
```

### 1.7.2. Python 2

There are a few ways to create a second virtual environment for Python2:

- [pipenv](#1722-pipenv): The most straightforward.
- [virtualenv](#1722-virtualenv): Python 2 does not include `virtualenv` by default and on some system not even `pip`.
- [poetry](#1723-poetry): Poetry could create a second env but will have package compatibility issues.
- and probably more...
  
> If the virtualenv created is inside root, poetry must change its configuration value to not use the in root venv: `poetry config virtualenvs.in-project false`

#### 1.7.2.1. `pipenv`

```sh
# install packages for python 2
pipenv install --two 

# run app locally
pipenv run python -m src.run_local

# run tests for python 2
pipenv run python -m pytest
```

#### 1.7.2.2. `virtualenv`

```sh
# Download and setup pip for python 2.
curl https://bootstrap.pypa.io/pip/2.7/get-pip.py --output get-pip.py && python2 $_

# install virtualenv
python2 -m pip install virtualenv

# setup a virtualenv for python2
python2 -m virtualenv .venv/

# activate the env with .venv/bin/activate or call it directly
# install package dependencies
.venv/bin/pip install -r requirements.txt

# run locally
.venv/bin/python -m src.run_local

# run tests
.venv/bin/python -m pytest
```

#### 1.7.2.3. `poetry`

Discouraged.

Because `poetry` allows multiple environment, one could change the _pyproject.toml_ python requirements to satisfy both python 2 and 3: `>=2.7.18, <=3.7.7`. This has the drawback that will only install the latest package version compatible for python2.

### 1.7.3. Testing

The repo includes a `git` hook script that is launched pre-push. The script will execute the tests for Python 2 and 3. If one fails, will exit and abort the push.

```sh
# to activate the .githooks folder as the default hooks folder for the repo
git config core.hooksPath .githooks
```

The script will assume that `poetry` is used for python 3 and that python 2 executable is inside `root/.venv/bin/`. If this is not the case, change `python2path` and `python3path`.

## 1.8. Known Issues

- Settings window doesn't display the tooltip text.
- When changing workspace with an active open connection, Nuke will load a new plugin instance with the default UI state. This would look as if the previous connection has been closed, where in reality is still open and listening. One way to force close all of the connections is to restart Nuke, or wait for the connection timeout: `5` minutes.

## 1.9. Compatibility

Nuke version: 11,12, 13.

> Because Nuke 11 uses an early version of PySide2, future compatibility is not a guarantee.

While it should work the same on all platforms, it has been currently only tested on:

- Linux:
  - CentOS 8
- MacOS:
  - Mojave 10.14.06
  - Catalina 10.15.06
- Windows 10

## 1.10. Overview

<img title="Execute Code" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/execute_code.gif?raw=true" width="100%"/>

<img title="Main Window" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/main_window.png?raw=true" width="80%"/>

<img title="Settings" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/settings.png?raw=trueg" width="30%"/>
