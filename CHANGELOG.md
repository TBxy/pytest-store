# Changelog

All notable changes to [this project](https://github.com/TBxy/pytest-store) will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

<details>
  <summary>Show Unreleased</summary>

## [Unreleased]

### Added

### Changed

### Fixed

### Removed

[unreleased]: https://github.com/TBxy/pytest-store/compare/v0.0.2...HEAD
</details>

## [0.0.2] - 2023-11-16

### Open Issue

- The `PASS` entry over all tests run is not always correct.

### Added

- Support for [pytest-repeat] if `--repeat-scope` is set to _session_.
- Support for [pytest-rerun-all].

### Changed

- Use _item_ attribute `_store_testname` and `_store_run` for the name and iteration counter.
  This attributes can be set by other plugins or in a `conftest.py` file.

[0.0.2]: https://github.com/TBxy/pytest-store/compare/v0.0.1...v0.0.2


## [0.0.1] - 2023-11-12

### Added

- Initial version.


[0.0.1]: https://github.com/TBxy/pytest-store/tree/v0.0.1
[pytest-repeat]: https://github.com/pytest-dev/pytest-repeat
[pytest-rerun-all]: https://github.com/TBxy/pytest-rerun-all
