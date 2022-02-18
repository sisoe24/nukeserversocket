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
![x](https://img.shields.io/badge/Nuke-11_|_12_|13-yellow)

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
  - [1.5. Settings](#15-settings)
  - [1.6. Extendibility](#16-extendibility)
  - [1.7. Test plugin locally](#17-test-plugin-locally)
  - [1.8. Known Issues](#18-known-issues)
  - [1.9. Compatibility](#19-compatibility)
  - [1.10. Overview](#110-overview)
    - [1.10.1. Execute Code](#1101-execute-code)
    - [1.10.2. Send Nodes](#1102-send-nodes)

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

[Demo](#1101-execute-code)

Open the _NukeServerSocket_ panel and with the mode on **Receiver**, start the server by clicking **Connect**.

  > If you receive a message: "_Server did not initiate. Error: The bound address is already in use_", just change the **Port** to a random number between `49152` and `65535` and try again. It means that probably you have a connection listening on that port already. Also when connected, you could test the receiver with the **Test Receiver** button.

When connected, NukeServerSocket will listen for incoming request on the IP Address and Port shown in the plugin.

Now you can send code from Visual Studio Code with [Nuke Tools](https://marketplace.visualstudio.com/items?itemName=virgilsisoe.nuke-tools) or any other method you prefer.

### 1.4.2. Receive/Send nodes

[Demo](#1102-send-nodes)

#### 1.4.2.1. Send

When sending nodes, switch the mode from **Receiver** to **Sender** and be sure that there is another NukeServerSocket instance listening for incoming network request ([Receive incoming request](#141-receive-incoming-request)). Select the nodes you want to send a click **Send Selected Nodes**.

> By default, the IP Address on the sender points to the local IP address, so, if you want to send nodes between the same computer, you should only specify the Port. When sending nodes to another computer, you will also need to specify the IP Address of the computer you want to send the nodes.

#### 1.4.2.2. Receive

When receiving nodes just follow the steps for [Receive incoming request](#141-receive-incoming-request) for the receiving instance and the [Send](#1421-send) steps for the sending instance.

## 1.5. Settings

The settings can be accessed from the plugin toolbar

- **Code Execution Engine**: Change the engine that is executing the code.
  - **Nuke Internal**: Nuke `executeInMainThread` function.
  - **Script Editor**: Nuke Script Editor widget.

- **Mirror To Script Editor**: Allows to mirror the input/output code to the internal script editor.
  - **Override Output Editor**: Mirror output to the internal script editor.
  - **Format Text**: The script editor output window will received a formatted version of the code result.
  - **Clear Output**:  The script editor output window will clear the code after each execution.
  - **Show File Path**: The script editor output window will display the full file path of the file being executed.
  - **Show Unicode**: The script editor output window will display a unicode character `` that indicates the start of the code execution result.
  - **Override Input Editor**: Mirror input to the internal script editor.

- **Timeout**: Terminate the connection when the server is inactive or it wasn't able to establish a successful connection, in the time specified.
  - **Server**: Set the timeout when clicking the **Connect** button. Defaults to `10` minutes.
  - **Receiver**: Set the timeout for when clicking the **Test Receiver** button. Defaults to `10` seconds.
  - **Send Nodes**: Set the timeout when clicking **Send Nodes** button. Defaults to `30` seconds.

## 1.6. Extendibility

At its core, the plugin is just a server socket that awaits for an incoming request,
performs the operations inside Nuke and returns the result. Nothing ties it to any
application per se.

This makes it very easy to implement a new client, without the need to modify NukeServerSocket source code. The client needs only to send the data at the specified address inside NukeServerSocket.

More information and examples on the [wiki page](https://github.com/sisoe24/NukeServerSocket/wiki/Create-custom-client).

## 1.7. Test plugin locally

The plugin can be launched locally outside the Nuke application. This is useful for testing code and implementing new features more rapidly.

More information on the [wiki page](https://github.com/sisoe24/NukeServerSocket/wiki/Test-Plugin-locally).

## 1.8. Known Issues

- Creating a modal window with the Nuke internal code execution engine, will cause Nuke to freeze. A workaround is to switch to the Script Editor engine.
- Settings window doesn't display the tooltip text.
- When changing workspace with an active open connection, Nuke will load a new plugin instance with the default UI state. This would look as if the previous connection has been closed, where in reality is still open and listening. One way to force close all of the connections is to restart Nuke, or you can wait for the connection timeout.

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

### 1.10.1. Execute Code

<img title="Execute Code" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/execute_code.gif?raw=true" width="100%"/>

### 1.10.2. Send Nodes

<img title="Send Nodes" src="https://github.com/sisoe24/NukeServerSocket/blob/main/images/send_nodes.gif?raw=true" width="100%"/>
