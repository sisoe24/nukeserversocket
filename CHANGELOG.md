# Changelog

## [Unreleased]

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
