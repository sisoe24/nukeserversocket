# Changelog


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
