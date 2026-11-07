# Changelog

## [Unreleased]

### Added

- MCP server (`nss_mcp`) so MCP clients can run code in Nuke. Experimental. Setup for Claude Code, Claude Desktop, Codex, Gemini CLI and other clients is in `docs/mcp.md`, and `docs/mcp-agent-setup.md` is a guide an agent can follow to set it up.
- Tools file: a JSON file of functions clients may call, which can also turn code execution off. Choose it in Settings > Tools file, or set `NSS_TOOLS`, which takes priority. The MCP server lists the tools next to `nuke_execute_code`.
- Settings > Tools file > **Create sample...** copies a sample tools file and its Python module into a folder. Modules next to the tools file import without a `NUKE_PATH` entry.
- The panel lists, under **MCP**, the tools that MCP clients see, with `nuke_execute_code` only when code is on.

### Changed

- The Logs show one line for each request, starting with the client in parentheses, such as `(MCP) render_write: ok`. Requests that take 1 second or more show the time. One bad request logs one warning instead of three lines.
- The Logs show the address and the tools file when the panel starts listening, and why it stopped when the Server Timeout closes it.
- Execution errors sent to clients always start with `NukeServerSocket error:`.
- The README covers getting started only. Details move to `docs/`: the client protocol in `docs/clients.md` (moved from the wiki), the MCP server and tools file in `docs/mcp.md`, and Houdini setup in `docs/houdini.md`.
- The client protocol docs no longer mention plain-string requests, which the server does not accept, and say that remote clients need **Allow LAN Connections**.

### Fixed

- The panel's Logs show `<` and `&` as text instead of reading them as HTML.

## [1.4.1] - 2026-11-07

### Fixed

- The Houdini panel no longer breaks when another Houdini package also ships a top-level `app` package. The package is renamed from `app` to `nukeserversocket_houdini`. Code that imports `app.main` directly must import `nukeserversocket_houdini.main`.

## [1.4.0] - 2026-11-02

### Added

- **Allow LAN Connections** setting, off by default: accept code from other machines on the network.

### Changed

- **Breaking:** the server listens only on `127.0.0.1` by default, because it runs code from clients with no authentication. To send code from another machine, turn on **Allow LAN Connections**.
- Clients must connect to `127.0.0.1` by IPv4. A client that connects to `localhost` by IPv6 only (`::1`) is refused.

## [1.3.0] - 2026-11-02

### Added

- PySide6 support for Nuke 16 and newer. Based on [#38](https://github.com/sisoe24/nukeserversocket/pull/38) by @kanbatsu.
- **Auto Start** setting, off by default: the server starts as soon as the panel opens. Save the panel in your Nuke workspace to start the server when Nuke opens. Requested in [#36](https://github.com/sisoe24/nukeserversocket/issues/36) by @sambeebe.
- Set **Server Timeout** to 0 to never close the server.

### Changed

- Qt classes are imported from the new `nukeserversocket._qt` module (e.g. `from nukeserversocket._qt import QWidget`), which uses PySide6 and falls back to PySide2, so Nuke 15 and older keep working.
- Tests run on Python 3.10 (PySide2) and Python 3.11 (PySide6).
- The default server timeout is 60 minutes instead of 1. Settings files that already store a timeout keep their value.
- The Nuke panel looks for the Script Editor the first time code arrives, not when the panel opens, so a panel restored at startup no longer fails.
- The **Connect** button is now to the right of the status form, which leaves more height for the console.

### Fixed

- The plugin no longer crashes when the `~/.nuke` folder does not exist (e.g. Houdini-only machines).
- `sys.stdout` is restored when executed code calls `sys.exit()`.
- With several clients connected, each client gets its own reply.
- The plugin loads from a read-only install folder; it skips the log file instead of failing.
- Nuke output is no longer truncated when it has no `# Result:` prefix.
- The Nuke panel looks up the Script Editor again when Nuke rebuilds it, instead of failing until the panel is reopened.
- The server frees each client socket after replying.
- Invalid JSON or empty code gets an error reply instead of the Script Editor's old output.
- When the Script Editor cannot be found, the client gets the error message instead of hanging.

## [1.2.0] - 2024-11-17

### Added

- Houdini support through new `HoudiniController` and `HoudiniEditor` in `controllers.houdini` module.

### Changed

- Refactor the core controller components to allow multiple controllers types (houdini does not uses a script editor for example).
- Moved and rename some files for better organizzation.
- Updated logging and documentation

## [1.1.0] - 2024-08-18

### Added

* Added color to logs

### Fixed

* [[#30](https://github.com/sisoe24/nukeserversocket/issues/30)]
* [#31](https://github.com/sisoe24/nukeserversocket/issues/31)
* [#32](https://github.com/sisoe24/nukeserversocket/issues/32)
* Logs font now use proper monospace font

## [1.0.0] - 2023-11-19

### Removed

* Drop support for Nuke <= 12 and Python 2.7.
* Removed the "Send Nodes" feature. It will be re-added in a future release if requested.
* Removed the "Nuke Internal" code execution engine. Now only the "Script Editor" engine is available.
* Removed the "Test Receiver" button.
* Removed the timeout UI counter.
* Removed the websocket connection type. Now only the TCP connection type is available.

### Changed

* Simplified the settings window.
* Simplified the logs window.
* Repository name changed to all lowercase.

### Fixed

* Vastly improved the code base.

### Added

* New setting to change the format of the output code result.

## [0.6.2] - 2023-11-19

### Fixed

* Fixed a bug that would cause the extension to not properly use the Script Editor engine.

## [0.6.1] - 2023-10-04

### Fixed

* Fixed a bug where Nuke's execution button was not found.

## [0.6.0] - 2023-03-12

### Added

* The status log viewers now have a toggle ON/OFF switch.
* Nuke 14 compatibility.

### Changed

* Using the Script Editor engine as default for executing code.

### Fixed

* Nuke internal engine executing nested functions now should work.

### Removed

* QWebSocket connection for Nuke 14.

## [0.5.0] - 2022-02-24

### Added

* New WebSocket connection type.

## [0.4.1] - 2022-02-18

### Added

* New settings to switch che code execution engine.

## [0.4.0] - 2022-02-17

### Added

* Configurable timeout settings.
* Display timeout timers inside UI.

### Fixed

* Exceptions happening in Nuke's thread, will now display in the extension output.

## [0.3.0] - 2022-02-06

Under the hood improvements on code execution and some refactoring.

### Changed

* Changed default way to execute code to `executeInMainThread` function.

## [0.2.0] - 2021-10-29

Tests, code refactoring, connection timeouts, various fixes and optimizations.

### Added

* Connection timeout for client and server.
* Tests.

### Changed

* Python3 is now the base interpreter when building locally.

### Fixed

* Sending nodes when no were selected, will properly display a hint.
* Fixed crash that could occur if connection did not initiate but user would attempt to request a new one.
* Fixed Script editor going out of scope by adding a cache system.

## [0.1.0] - 2021-09-23

Code refactoring and some new features.

### Added

* Send/Receive nodes between Nuke instances.
* Execute BlinkScript code.

### Changed

* Better check for configuration file in case it gets deleted or modified after plugin execution.

## [0.0.3] - 2021-09-11

Code refactoring, under the hood optimizations and cleaning.

### Added

* New widget _About_.

### Changed

* Simple strings are also accepted when sending data to the API.
* Nuke internal script editor gets initialized only at Nuke launch instead of each code execution.

## [0.0.2] - 2021-08-02

Small maintenance

### Added

* _VERSION_ file.
* _setup.py_.
* _paths.py_.

### Changed

* Moved `about` functionality into its own module.
* Changed import system to relative.
* Preparing for tests: included `pytest` with dev build.
* Updated README on how to build plug-in locally (Only Mac & Linux)

## [0.0.1] - 2021-07-30

* Initial release
