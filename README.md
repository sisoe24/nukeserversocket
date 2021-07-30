# VscodeServerSocket README

A Nuke that plugin will enable you to execute code from Visual Studio Code.

> This is a companion plugin for: www.placeholder.com.

## Features

* Execute code from your local network by using Visual Studio Code.
* If used locally (same machine) no configuration required, just start the server.
* Connect from another computer by specify a custom address.
* Multiple computer can connect to the same Nuke instance.

## Installation

Save the plugin in your _.nuke_ directory or in a custom directory and then `import VscodeServerSocket` in your _menu.py_.  
**Remember**: If you use a custom plugin path, add the path in your init.py: `nuke.pluginAddPath('custom/path')`.
> N.B. if your downloaded  zip folder has a different name (VscodeServerSocket-master, VscodeServerSocket-0.0.2 etc._), then you **need to rename it to just VscodeServerSocket**.

## Usage

1. Open the _Vscode Server Socket_ panel and start the server by clicking on **Connect**.
   1. If you receive a message: "_Server did not initiate. Error: The bound address is already in use_", just change the **port** entry to a different one and try again. It means that probably you have a connection listening on that port already.
2. When connected you could test the receiver with the **Test Server Receiver** otherwise you are done.
3. Send code from you Visual Studio Code by using the companion extension.

## Connection

When used locally (same machine), no configuration is required as the server will listen on the **Local Host Address**. If the server **port** is already busy it will require manual change (just type a random number between `49152` and `65535` and try again). Visual Studio Code will pick Nuke's settings automatically.

When connecting from/to another computer, manual configuration will be required inside Visual Studio Code.
You will need the **Local IP address** and the **port**.

The information inside Visual Studio Code must match the information inside Nuke plugin.

> VMs: Sending from your local machine to a VM machine will likely require some configuration from your side by enabling some network settings and this will differ from application to application.

If you still have some problems, please feel free to reach out for any questions.

## Settings

The plugin offers some minor settings for the internal script editor, like send output, format text and so on but they are pretty self explanatory.

## Known Issues

* Settings window doesn't display the tooltip text. This seems to be a Nuke bug as outside it works correctly.
* Plugin has been tested only on small amount of scripts so if you encounter problems/bugs will be great to receive a testable sample code.

### Compatibility

Nuke version: 11,12, 13.

> Because Nuke 11 uses an early version of PySide2, future compatibility is not a guarantee.

While it should work the same on all platforms, it has been currently only tested on:

* Linux:
  * CentOS 8
* MacOS:
  * Mojave 10.14.06
  * Catalina 10.15.06
* Windows 10

## Screenshot

Execute code
![execute_code](/images/execute_code.gif)

Manual connection from Vscode
![manual_connection](/images/vscode_manual.png)

Internal settings

![settings](/images/settings.png)