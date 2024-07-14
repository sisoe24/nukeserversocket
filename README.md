# 1. nukeserversocket README

[![Main Build](https://img.shields.io/github/v/release/sisoe24/nukeserversocket?label=stable)](https://github.com/sisoe24/nukeserversocket/releases)
[![Pre Release](https://img.shields.io/github/v/release/sisoe24/nukeserversocket?label=pre-release&include_prereleases)](https://github.com/sisoe24/nukeserversocket/releases)
![Last commit](https://img.shields.io/github/last-commit/sisoe24/nukeserversocket)
[![license](https://img.shields.io/github/license/sisoe24/nukeserversocket)](https://github.com/sisoe24/nukeserversocket/blob/main/LICENSE)

[![issues](https://img.shields.io/github/issues/sisoe24/nukeserversocket)](https://github.com/sisoe24/nukeserversocket/issues)
[![pull-request](https://img.shields.io/github/issues-pr/sisoe24/nukeserversocket)](https://github.com/sisoe24/nukeserversocket/pulls)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/5b59bd7f80c646a8b2b16ad4b8cba599)](https://www.codacy.com/gh/sisoe24/nukeserversocket/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=sisoe24/nukeserversocket&amp;utm_campaign=Badge_Grade)
[![Codacy Badge](https://app.codacy.com/project/badge/Coverage/5b59bd7f80c646a8b2b16ad4b8cba599)](https://www.codacy.com/gh/sisoe24/nukeserversocket/dashboard?utm_source=github.com&utm_medium=referral&utm_content=sisoe24/nukeserversocket&utm_campaign=Badge_Coverage)


[![NukeTools](https://img.shields.io/github/v/release/sisoe24/Nuke-Tools?label=NukeTools)](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools)
![x](https://img.shields.io/badge/Python-3.*-success)
![x](https://img.shields.io/badge/Nuke-_13_|_14_|_15-yellow)

A Nuke plugin to run code from external applications.

- [1. nukeserversocket README](#1-nukeserversocket-readme)
  - [1.0.0 Release](#100-release)
    - [Important Update: Repository Name Change](#important-update-repository-name-change)
  - [1.1. Features](#11-features)
  - [1.2. Client applications](#12-client-applications)
  - [1.3. Installation](#13-installation)
  - [1.4. Usage](#14-usage)
  - [1.5. Settings](#15-settings)
  - [1.6. Extendibility](#16-extendibility)
  - [1.8. Known Issues](#18-known-issues)
  - [1.9. Compatibility](#19-compatibility)

## 1.0.0 Release

This is the initial stable version of nukeserversocket. It's a total rewrite of the earlier version with the primary goal to enhance stability and simplify maintenance. Now, the plugin is more flexible and straightforward to use in different applications.

For a full list of changes, see the [CHANGELOG](https://github.com/sisoe24/nukeserversocket/blob/main/CHANGELOG.md)

If you are using Nuke 12 or Python 2.7, you can still use the previous version of the plugin `<=0.6.2` from the [releases page](https://github.com/sisoe24/nukeserversocket/releases)

Feedback and contributions are welcome!

### Important Update: Repository Name Change

The repository name has changed from `NukeServerSocket` to `nukeserversocket`. Although GitHub url seems to be case insensitive, if you have cloned the repository before, you might need to update the remote url.

```bash
git remote set-url origin https://github.com/sisoe24/nukeserversocket.git
```

This also means that you will need to update the import statement in your _menu.py_ file. See [Installation](#13-installation)

---

## 1.1. Features

- Receive Python or BlinkScript code from any client in your local network. (More on [Extendibility](#16-extendibility))
- Connect more than one client to the same Nuke instance.

## 1.2. Client applications

Client applications that use nukeserversocket:

- [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools) - Visual Studio Code extension.
- [Nuke Tools ST](https://packagecontrol.io/packages/NukeToolsST) - Sublime Text package.
- [DCC WebSocket](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.dcc-websocket) - Visual Studio Code Web extension. Note: I am not actively maintaining this extension anymore.

## 1.3. Installation

1. Download the repository via the [releases page](https://github.com/sisoe24/nukeserversocket/releases) or by cloning it from GitHub.
2. Place the folder inside the _~/.nuke_ directory or into a custom one.
3. Then, in your _menu.py_, write
     ```python
     from nukeserversocket import nukeserversocket
     nukeserversocket.install_nuke()
     ```

> If you use [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools), use the command `Nuke: Add Packages` then select nukeServerSocket.

## 1.4. Usage

![Execute Code](images/run_code.gif)

1. Open the nukeserversocket panel inside Nuke, and start the server by clicking **Connect**.
2. You can now send code from Visual Studio Code with [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools) or any other method you prefer.

NOTES:

- If you receive a message: "_Server did not initiate. Error: The bound address is already in use_", change the **port** to a random number between `49152` and `65535` and try again.

## 1.5. Settings

You access the settings from the plugin toolbar.

- **Mirror To Script Editor**: Allows mirroring the input/output code to the internal script editor.
- **Format Text**: The script editor output window will receive a formatted version of the code result. The available placeholders are:

  - `%d`: Time
  - `%t`: The code result
  - `%f`: The full file path
  - `%F`: The file name
  - `%n`: A new line

   **Format Text Example**: `%d - %t%n` will output `12:00:00 - Hello World!` in the script editor output window.

- **Clear Output**: The script editor output window will clear the code after each execution.

- **Server Timeout**: Set the Timeout when clicking the **Connect** button. The default value is `10` minutes.

## 1.6. Extendibility

The plugin essentially works as a server socket that waits for incoming requests. Once a request is received, it performs the required operations within Nuke and sends back the result. This plugin is not tied to any specific application, which means it is easy to implement a new client without having to modify the nukeserversocket source code. All the client needs to do is send the data to the specified address within nukeserversocket.

If you wish to create a new client or contribute to the existing ones, you can find more information on the [wiki page](https://github.com/sisoe24/nukeserversocket/wiki/Create-custom-client)

## 1.8. Known Issues

- Changing workspace with an active open connection makes Nuke load a new plugin instance with the default UI state. So it would look as if the previous connection has been closed, whereas in reality is still open and listening. To force close all of the listening connections, you can:
  - Restart the Nuke instance.
  - Wait for the connection timeout.

## 1.9. Compatibility

Nuke version: 13, 14, 15

While it should work the same on all platforms, I have tested the plugin only on:

- Linux:
  - CentOS 8
- macOS:
  - Mojave 10.14.06
  - Catalina 10.15.07
  - Monterey 12.6.3
- Windows 10
